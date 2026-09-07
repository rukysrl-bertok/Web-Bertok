"""
Centro de Operaciones Bertok — restauración de prueba.

    UN BACKUP QUE NUNCA SE RESTAURÓ NO ES UN BACKUP.

Se corre UNA VEZ POR MES. Cinco minutos, y es la diferencia entre tener
backup y creer que se tiene.

Qué hace:
    1. Toma el backup más reciente de cada base.
    2. Lo copia a una carpeta descartable (nunca toca la base real).
    3. Lo abre, corre integrity_check y foreign_key_check.
    4. Cuenta filas y las compara contra la base viva.
    5. Verifica que el esquema esté completo: tablas, vistas y triggers.
    6. Informa la antigüedad del backup: uno de hace diez días no sirve.

Uso:
    python restaurar_prueba.py
    python restaurar_prueba.py --destino "D:\\OneDrive\\Backups"

Al terminar hay que anotar el resultado en BITACORA.md, con fecha y quién.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from backup_bases import BASES, DESTINO_POR_DEFECTO, _tablas_y_filas, sha256

VERDE, ROJO, AMARILLO, GRIS, FIN = (
    "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m")

ANTIGUEDAD_ACEPTABLE_H = 30      # un backup diario no debería pasar de esto


def _mas_reciente(carpeta: Path, nombre: str) -> Path | None:
    archivos = sorted(carpeta.glob(f"{nombre}_*.db"))
    return archivos[-1] if archivos else None


def _inventario(ruta: Path) -> dict:
    cx = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    try:
        return {
            tipo: sorted(r[0] for r in cx.execute(
                "SELECT name FROM sqlite_master "
                " WHERE type=? AND name NOT LIKE 'sqlite_%'", (tipo,)))
            for tipo in ("table", "view", "trigger", "index")
        }
    finally:
        cx.close()


def probar(nombre: str, viva: Path, destino: Path, taller: Path) -> bool:
    print(f"\n  {nombre}")
    print("  " + "-" * 58)

    carpeta = destino / nombre / "diario"
    backup = _mas_reciente(carpeta, nombre) if carpeta.exists() else None
    if backup is None:
        print(f"  {ROJO}FALLA{FIN} no hay ningún backup diario en {carpeta}")
        return False

    edad_h = (datetime.now() - datetime.fromtimestamp(
        backup.stat().st_mtime)).total_seconds() / 3600
    marca = VERDE if edad_h <= ANTIGUEDAD_ACEPTABLE_H else AMARILLO
    print(f"  Backup:  {backup.name}   {GRIS}({backup.stat().st_size/1_048_576:.2f} MB){FIN}")
    print(f"  Antigüedad: {marca}{edad_h:.1f} h{FIN}"
          + (f"   {AMARILLO}← el backup diario dejó de correr{FIN}"
             if edad_h > ANTIGUEDAD_ACEPTABLE_H else ""))

    ok = True

    # PRIMERO el checksum: es lo único que detecta un byte cambiado desde
    # que se creó la copia. integrity_check no llega ahí — medido: con
    # 3.000 bytes ensuciados en páginas libres devuelve «ok» igual.
    firma_guardada = backup.with_suffix(".db.sha256")
    if firma_guardada.exists():
        esperado = firma_guardada.read_text(encoding="utf-8").split()[0]
        obtenido = sha256(backup)
        coincide = esperado == obtenido
        print(f"  SHA-256: {VERDE + 'coincide' if coincide else ROJO + 'NO COINCIDE'}{FIN}"
              f"   {GRIS}{obtenido[:16]}…{FIN}")
        if not coincide:
            print(f"  {ROJO}        El archivo cambió desde que se creó."
                  f" No sirve como backup.{FIN}")
            print(f"  {GRIS}        esperado {esperado[:16]}…{FIN}")
        ok &= coincide
    else:
        print(f"  {AMARILLO}SHA-256: sin firma guardada (backup anterior "
              f"a esta versión del script){FIN}")

    # Restaurar de verdad: copiar a otro lado y abrir esa copia.
    copia = taller / f"restaurado_{nombre}.db"
    shutil.copy2(backup, copia)

    cx = sqlite3.connect(str(copia))
    try:
        estado = cx.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"  integrity_check: {VERDE if estado=='ok' else ROJO}{estado}{FIN}")
        ok &= estado == "ok"

        fks = cx.execute("PRAGMA foreign_key_check").fetchall()
        print(f"  foreign_key_check: "
              f"{VERDE + 'sin violaciones' if not fks else ROJO + str(len(fks)) + ' violaciones'}{FIN}")
        ok &= not fks
    finally:
        cx.close()

    inv_backup = _inventario(copia)
    if viva.exists():
        inv_viva = _inventario(viva)
        for tipo in ("table", "view", "trigger"):
            faltan = set(inv_viva[tipo]) - set(inv_backup[tipo])
            if faltan:
                print(f"  {ROJO}FALLA{FIN} faltan {tipo}s en el backup: {sorted(faltan)}")
                ok = False
        if ok:
            print(f"  Esquema: {VERDE}completo{FIN}   "
                  f"{GRIS}{len(inv_backup['table'])} tablas · "
                  f"{len(inv_backup['view'])} vistas · "
                  f"{len(inv_backup['trigger'])} triggers{FIN}")

        filas_v, filas_b = _tablas_y_filas(viva), _tablas_y_filas(copia)
        perdidas = {t: (filas_v[t], filas_b.get(t, 0))
                    for t in filas_v if filas_b.get(t, 0) < filas_v[t]}
        total_b = sum(filas_b.values())
        if perdidas:
            print(f"  {AMARILLO}Filas: el backup tiene menos que la base viva{FIN}")
            for t, (v, b) in sorted(perdidas.items()):
                print(f"        {t}: viva {v} · backup {b}")
            print(f"  {GRIS}  (esperable si hubo actividad desde el backup;"
                  f" alarmante si la diferencia es grande){FIN}")
        else:
            print(f"  Filas: {VERDE}{total_b} en el backup, ninguna tabla corta{FIN}")
    else:
        print(f"  {AMARILLO}La base viva no existe: sólo se validó el backup.{FIN}")

    if ok:
        print(f"  {VERDE}El backup abre, está íntegro y trae el esquema completo.{FIN}")
    return ok


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Restauración de prueba mensual")
    p.add_argument("--destino", type=Path, default=DESTINO_POR_DEFECTO)
    p.add_argument("--base", action="append", help="nombre=ruta, repetible")
    args = p.parse_args(argv)

    bases = BASES
    if args.base:
        bases = {}
        for spec in args.base:
            nombre, _, ruta = spec.partition("=")
            bases[nombre] = Path(ruta)

    taller = Path(tempfile.mkdtemp(prefix="restauracion_"))
    print(f"\n  RESTAURACIÓN DE PRUEBA — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"  {GRIS}Taller descartable: {taller}{FIN}")
    print(f"  {GRIS}Las bases vivas no se tocan en ningún momento.{FIN}")

    resultados = {n: probar(n, r, args.destino, taller) for n, r in bases.items()}

    print("\n  " + "=" * 58)
    fallidas = [n for n, ok in resultados.items() if not ok]
    if fallidas:
        print(f"  {ROJO}NO RESTAURAN: {', '.join(fallidas)}{FIN}")
        print("  Hay que arreglarlo hoy: el backup no sirve como está.\n")
        return 1
    print(f"  {VERDE}Todas las bases restauran correctamente.{FIN}")
    print("  Anotar en BITACORA.md: fecha, quién lo corrió y este resultado.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
