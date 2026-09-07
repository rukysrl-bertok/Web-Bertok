"""
Centro de Operaciones Bertok — backup de ops.db y picking.db.

POR QUÉ NO ALCANZA UN «copy»
    Una SQLite en modo WAL usa tres archivos (.db, .db-wal, .db-shm) que
    deben estar coherentes entre sí. Copiar el .db con transacciones en
    vuelo produce una base incompleta, y NO SE NOTA hasta el día que hace
    falta. Por eso acá se usa VACUUM INTO, que genera un archivo único,
    consistente y ya cerrado, sin frenar la operación.

Qué hace, en orden:
    1. VACUUM INTO sobre un archivo nuevo (la base sigue en uso).
    2. Verifica el resultado: integrity_check + conteo de filas.
       Si no verifica, NO reemplaza el backup anterior.
    3. Lo deja en diario/, y asegura una copia semanal de la semana ISO.
    4. Poda: 7 diarios + 4 semanales. Nunca pisa un archivo existente.
    5. Escribe ultimo_backup.json, para que el Centro pueda avisar si el
       backup dejó de correr.

Uso:
    python backup_bases.py
    python backup_bases.py --destino "D:\\OneDrive\\Backups"
    python backup_bases.py --fecha 2026-09-12      # para probar la rotación

Se programa como tarea de Windows, una vez por día, en horario no operativo.
Código de salida distinto de 0 = algo falló y hay que mirarlo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# --- configuración ----------------------------------------------------

BASES = {
    "ops":     Path(r"C:\Sistema de Picking\ops.db"),
    "picking": Path(r"C:\Sistema de Picking\picking.db"),
}

DESTINO_POR_DEFECTO = Path(
    r"C:\Users\Gerardo\Ruky S.R.L\Bertok - Documentos"
    r"\17 - Centro de Operaciones\Backups"
)

RETENER_DIARIOS = 7
RETENER_SEMANALES = 4

# VACUUM INTO existe desde SQLite 3.27 (2019).
SQLITE_MINIMO = (3, 27, 0)


class BackupFallido(Exception):
    pass


# --- utilidades -------------------------------------------------------

def _version_sqlite_ok() -> bool:
    return tuple(int(x) for x in sqlite3.sqlite_version.split(".")) >= SQLITE_MINIMO


def _tablas_y_filas(ruta: Path) -> dict[str, int]:
    """Cuenta filas por tabla. Sirve para comparar origen contra copia."""
    cx = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    try:
        tablas = [r[0] for r in cx.execute(
            "SELECT name FROM sqlite_master "
            " WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {t: cx.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                for t in tablas}
    finally:
        cx.close()


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def _verificar(copia: Path) -> dict[str, int]:
    """
    Un backup no verificado no es un backup. Se abre la copia, se corre
    integrity_check y se cuentan las filas. Si algo falla, se descarta.

    OJO CON EL ALCANCE DE integrity_check: recorre la estructura del árbol,
    pero NO detecta toda la corrupción. Medido sobre esta misma base: con
    3.000 bytes ensuciados en páginas libres del medio del archivo, devolvió
    «ok» igual. Por eso además se guarda un SHA-256 al lado de cada copia
    (.sha256): eso sí detecta cualquier byte cambiado, que es lo que hace
    falta cuando el backup vive en una carpeta sincronizada.
    """
    cx = sqlite3.connect(f"file:{copia}?mode=ro", uri=True)
    try:
        estado = cx.execute("PRAGMA integrity_check").fetchone()[0]
        if estado != "ok":
            raise BackupFallido(f"integrity_check devolvió «{estado}»")
    finally:
        cx.close()
    return _tablas_y_filas(copia)


def _podar(carpeta: Path, patron: str, retener: int) -> list[str]:
    archivos = sorted(carpeta.glob(patron))
    sobrantes = archivos[:-retener] if len(archivos) > retener else []
    for a in sobrantes:
        a.unlink()
        firma = a.with_suffix(a.suffix + ".sha256")
        if firma.exists():
            firma.unlink()
    return [a.name for a in sobrantes]


# --- backup de una base ----------------------------------------------

def respaldar(nombre: str, origen: Path, destino: Path,
              momento: datetime) -> dict:
    resultado: dict = {"base": nombre, "origen": str(origen), "ok": False}

    if not origen.exists():
        resultado["error"] = "la base de origen no existe"
        return resultado

    carpeta_diaria = destino / nombre / "diario"
    carpeta_semanal = destino / nombre / "semanal"
    carpeta_diaria.mkdir(parents=True, exist_ok=True)
    carpeta_semanal.mkdir(parents=True, exist_ok=True)

    sello = momento.strftime("%Y-%m-%d_%H%M")
    anio, semana, _ = momento.isocalendar()
    destino_diario = carpeta_diaria / f"{nombre}_{sello}.db"
    destino_semanal = carpeta_semanal / f"{nombre}_{anio}-W{semana:02d}.db"

    # Nunca pisar: si algo se corrompió el lunes y se nota el jueves,
    # sobrescribir habría destruido las copias buenas.
    if destino_diario.exists():
        resultado["error"] = f"ya existe {destino_diario.name}, no se pisa"
        return resultado

    parcial = destino_diario.with_suffix(".db.parcial")
    if parcial.exists():
        parcial.unlink()

    try:
        # El conteo de referencia se toma ANTES del VACUUM. Si se tomara
        # después, con la base en uso el origen siempre tendría más filas
        # que la copia y toda corrida daría falso negativo — que es
        # exactamente el escenario para el que existe este backup.
        filas_antes = _tablas_y_filas(origen)

        # VACUUM INTO: archivo único, consistente, cerrado. Sin frenar la base.
        cx = sqlite3.connect(str(origen))
        try:
            cx.execute("PRAGMA busy_timeout = 30000")
            cx.execute("VACUUM INTO ?", (str(parcial),))
        finally:
            cx.close()

        filas_copia = _verificar(parcial)

        faltantes = [t for t in filas_antes if t not in filas_copia]
        if faltantes:
            raise BackupFallido(f"faltan tablas en la copia: {faltantes}")

        # La copia es una foto posterior al conteo de referencia: puede
        # tener filas de más (entraron durante el VACUUM), nunca de menos.
        cortas = {t: (filas_antes[t], filas_copia[t])
                  for t in filas_antes if filas_copia[t] < filas_antes[t]}
        if cortas:
            raise BackupFallido(f"la copia tiene menos filas que el origen "
                                f"antes de copiar: {cortas}")

        parcial.rename(destino_diario)

        # Firma del archivo final. Es lo único que detecta un byte cambiado
        # después de la copia: sincronización a medias, bit-rot, escritura
        # parcial. integrity_check no llega ahí.
        firma = sha256(destino_diario)
        destino_diario.with_suffix(".db.sha256").write_text(
            f"{firma}  {destino_diario.name}\n", encoding="utf-8")

        if not destino_semanal.exists():
            shutil.copy2(destino_diario, destino_semanal)
            destino_semanal.with_suffix(".db.sha256").write_text(
                f"{firma}  {destino_semanal.name}\n", encoding="utf-8")
            resultado["semanal_creado"] = destino_semanal.name

        resultado.update(
            ok=True,
            archivo=str(destino_diario),
            tamano_mb=round(destino_diario.stat().st_size / 1_048_576, 2),
            tablas=len(filas_copia),
            filas=sum(filas_copia.values()),
            sha256=firma,
            podados_diarios=_podar(carpeta_diaria, f"{nombre}_*.db", RETENER_DIARIOS),
            podados_semanales=_podar(carpeta_semanal, f"{nombre}_*.db", RETENER_SEMANALES),
        )

    except Exception as e:
        # Si algo falló, el backup anterior sigue intacto: nunca se tocó.
        if parcial.exists():
            parcial.unlink()
        resultado["error"] = f"{type(e).__name__}: {e}"

    return resultado


# --- principal --------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Backup de las bases del Centro")
    p.add_argument("--destino", type=Path, default=DESTINO_POR_DEFECTO)
    p.add_argument("--fecha", help="AAAA-MM-DD, para probar la rotación")
    p.add_argument("--base", action="append",
                   help="nombre=ruta, repetible; reemplaza la config")
    args = p.parse_args(argv)

    if not _version_sqlite_ok():
        print(f"\n  ABORTADO: SQLite {sqlite3.sqlite_version} no soporta "
              f"VACUUM INTO (hace falta {'.'.join(map(str, SQLITE_MINIMO))}+).\n"
              f"  Sin VACUUM INTO no hay backup confiable: copiar el .db a mano\n"
              f"  con el WAL activo produce una base incompleta.\n")
        return 2

    bases = BASES
    if args.base:
        bases = {}
        for spec in args.base:
            nombre, _, ruta = spec.partition("=")
            bases[nombre] = Path(ruta)

    momento = (datetime.strptime(args.fecha, "%Y-%m-%d")
               if args.fecha else datetime.now())

    print(f"\n  Backup — {momento:%Y-%m-%d %H:%M}")
    print(f"  Destino: {args.destino}")
    print("  " + "-" * 58)

    resultados = [respaldar(n, r, args.destino, momento) for n, r in bases.items()]

    for r in resultados:
        if r["ok"]:
            print(f"  OK    {r['base']:<8} {r['tamano_mb']:>7.2f} MB   "
                  f"{r['tablas']} tablas · {r['filas']} filas")
            if r.get("semanal_creado"):
                print(f"        semanal: {r['semanal_creado']}")
            for tipo in ("podados_diarios", "podados_semanales"):
                if r[tipo]:
                    print(f"        podados ({tipo.split('_')[1]}): "
                          f"{', '.join(r[tipo])}")
        else:
            print(f"  FALLA {r['base']:<8} {r['error']}")

    # Para que el Centro pueda avisar si el backup dejó de correr.
    args.destino.mkdir(parents=True, exist_ok=True)
    (args.destino / "ultimo_backup.json").write_text(
        json.dumps({"momento": momento.isoformat(timespec="seconds"),
                    "resultados": resultados}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    fallidos = [r for r in resultados if not r["ok"]]
    if fallidos:
        print(f"\n  {len(fallidos)} base(s) sin respaldar. REVISAR.\n")
        return 1

    print("\n  Todas las bases respaldadas y verificadas.")
    print("  Recordatorio: la restauración de prueba va una vez por mes "
          "(restaurar_prueba.py).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
