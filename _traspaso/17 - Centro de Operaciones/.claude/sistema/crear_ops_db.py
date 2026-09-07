"""
Centro de Operaciones Bertok — creación de ops.db.

Crea la base con los pragmas de producción y aplica el esquema.
Es idempotente: se puede correr sobre una base existente sin romper nada
(todo el DDL usa IF NOT EXISTS).

Uso:
    python crear_ops_db.py                       # ruta por defecto
    python crear_ops_db.py "C:\\Sistema de Picking\\ops.db"
"""

from __future__ import annotations

import sys
from pathlib import Path

from guarda_alcance import PREFIJO, abrir

RUTA_POR_DEFECTO = Path(r"C:\Sistema de Picking\ops.db")
ESQUEMA = Path(__file__).with_name("esquema_ops.sql")

# La base NUNCA va adentro de OneDrive: una SQLite en WAL usa tres archivos
# que deben estar coherentes entre sí, y la sincronización los rompe.
# Es el mismo motivo por el que picking.db vive afuera.
SENALES_SINCRONIZADO = ("onedrive", "dropbox", "google drive", "icloud")


def verificar_ubicacion(ruta: Path) -> None:
    texto = str(ruta).lower()
    for senal in SENALES_SINCRONIZADO:
        if senal in texto:
            raise SystemExit(
                f"\n  ABORTADO: la ruta parece estar dentro de {senal}.\n"
                f"  ops.db no puede vivir en una carpeta sincronizada: el modo\n"
                f"  WAL usa tres archivos y la sincronización los descoordina.\n"
                f"  Los backups sí van a OneDrive, porque son archivos cerrados.\n"
                f"  Ruta recibida: {ruta}\n"
            )


def main(argv: list[str]) -> int:
    ruta = Path(argv[1]) if len(argv) > 1 else RUTA_POR_DEFECTO
    verificar_ubicacion(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    existia = ruta.exists()
    print(f"\n  Base: {ruta}")
    print(f"  Estado previo: {'existente' if existia else 'nueva'}")

    with abrir(ruta, modo="escritura") as cx:
        cx.executescript(ESQUEMA.read_text(encoding="utf-8"))

        modo = cx.execute("PRAGMA journal_mode").fetchone()[0]
        sync = cx.execute("PRAGMA synchronous").fetchone()[0]
        busy = cx.execute("PRAGMA busy_timeout").fetchone()[0]

        tablas = [r[0] for r in cx.execute(
            "SELECT name FROM sqlite_master "
            " WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            " ORDER BY name"
        )]
        vistas = [r[0] for r in cx.execute(
            "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
        triggers = [r[0] for r in cx.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name")]

    nombres_sync = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
    print(f"\n  journal_mode = {modo}   "
          f"synchronous = {nombres_sync.get(sync, sync)}   "
          f"busy_timeout = {busy} ms")

    fuera = [t for t in tablas if not t.startswith(PREFIJO)]
    print(f"\n  Tablas ({len(tablas)}):")
    for t in tablas:
        print(f"    - {t}")
    print(f"\n  Vistas ({len(vistas)}):   " + ", ".join(vistas))
    print(f"  Triggers ({len(triggers)}): " + ", ".join(triggers))

    if fuera:
        print(f"\n  ATENCIÓN: hay tablas fuera del prefijo {PREFIJO}: {fuera}")
        return 1

    print(f"\n  OK — todas las tablas respetan el prefijo «{PREFIJO}».")
    print("  Siguiente paso: python probar_guarda.py\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
