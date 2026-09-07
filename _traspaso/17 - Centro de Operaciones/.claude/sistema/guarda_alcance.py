"""
Centro de Operaciones Bertok — guarda de alcance.

REGLA DURA DEL MÓDULO
    El Centro sólo lee de los sistemas ajenos. Lo único que escribe es
    ops.db, y sólo tablas con prefijo bertok_ops_. Sin excepciones.

Esta guarda NO es una convención ni un filtro por texto del SQL: usa el
autorizador del propio SQLite, que se ejecuta dentro del motor antes de
compilar cada sentencia. No se puede esquivar con comentarios, mayúsculas,
nombres entre comillas ni sentencias encadenadas.

Se replica el mismo mecanismo que ya protege a Bertok BI, y se prueba
igual: con un set de sentencias destructivas que deben fallar todas
(probar_guarda.py).

Uso:
    from guarda_alcance import abrir

    with abrir(RUTA_OPS, modo="escritura") as cx:
        cx.execute("INSERT INTO bertok_ops_eventos (...) VALUES (...)")

    with abrir(RUTA_ML, modo="lectura") as cx:      # ML.db, picking.db
        cx.execute("SELECT ...")
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

PREFIJO = "bertok_ops_"

# Pragmas de concurrencia. busy_timeout es lo que más pesa: sin él una
# escritura concurrente falla al instante en vez de esperar el lock.
BUSY_TIMEOUT_MS = 5000
WAL_AUTOCHECKPOINT = 1000


class AlcanceDenegado(Exception):
    """Se intentó escribir fuera del alcance permitido."""


# --- acciones del autorizador -----------------------------------------

# (accion, indice del argumento que trae el nombre de la tabla)
_ESCRITURA_DATOS = {
    sqlite3.SQLITE_INSERT: 0,
    sqlite3.SQLITE_UPDATE: 0,
    sqlite3.SQLITE_DELETE: 0,
}

_ESCRITURA_ESQUEMA = {
    sqlite3.SQLITE_CREATE_TABLE: 0,
    sqlite3.SQLITE_DROP_TABLE: 0,
    sqlite3.SQLITE_CREATE_VIEW: 0,
    sqlite3.SQLITE_DROP_VIEW: 0,
    sqlite3.SQLITE_CREATE_INDEX: 1,      # (indice, tabla)
    sqlite3.SQLITE_DROP_INDEX: 1,
    sqlite3.SQLITE_CREATE_TRIGGER: 1,    # (trigger, tabla)
    sqlite3.SQLITE_DROP_TRIGGER: 1,
    sqlite3.SQLITE_ALTER_TABLE: 1,       # (base, tabla)
}

# Temporales: viven en la base temp, desaparecen al cerrar y no pueden
# tocar datos persistidos. Se permiten.
_TEMPORALES = {
    sqlite3.SQLITE_CREATE_TEMP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_INDEX,
    sqlite3.SQLITE_DROP_TEMP_INDEX,
    sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
    sqlite3.SQLITE_DROP_TEMP_TRIGGER,
    sqlite3.SQLITE_CREATE_TEMP_VIEW,
    sqlite3.SQLITE_DROP_TEMP_VIEW,
    sqlite3.SQLITE_INSERT,   # se resuelve antes por nombre de tabla
}

# Pragmas que permiten reescribir el esquema o saltar validaciones.
_PRAGMAS_PROHIBIDOS = {"writable_schema", "ignore_check_constraints"}


def _nombre_tabla(accion: int, arg1, arg2):
    idx = _ESCRITURA_DATOS.get(accion, _ESCRITURA_ESQUEMA.get(accion))
    if idx is None:
        return None
    return (arg1, arg2)[idx]


def _permitida(nombre) -> bool:
    if not nombre:
        return False
    n = nombre.lower()

    # Tablas internas de SQLite (sqlite_master, sqlite_sequence, temp_*).
    # Todo DDL escribe en sqlite_master por debajo: si no se permite, no se
    # puede ni crear el propio esquema. Es seguro permitirlas porque:
    #   1. escribirlas a mano exige PRAGMA writable_schema, que está denegado;
    #   2. el CREATE/DROP/ALTER que las provoca ya se autoriza aparte, por
    #      el nombre de la tabla real.
    if n.startswith("sqlite_"):
        return True

    return n.startswith(PREFIJO)


def _crear_autorizador(modo: str, ultimo: list):
    """Devuelve el callback del autorizador para el modo pedido."""

    solo_lectura = modo == "lectura"

    def autorizador(accion, arg1, arg2, base, disparador):
        # Nunca adjuntar ni desadjuntar otras bases: es la vía más simple
        # para escribir en ML.db o picking.db desde acá.
        if accion in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH):
            ultimo.append(f"ATTACH/DETACH bloqueado ({arg1})")
            return sqlite3.SQLITE_DENY

        if accion == sqlite3.SQLITE_PRAGMA:
            if (arg1 or "").lower() in _PRAGMAS_PROHIBIDOS:
                ultimo.append(f"PRAGMA {arg1} bloqueado")
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        es_escritura = accion in _ESCRITURA_DATOS or accion in _ESCRITURA_ESQUEMA

        if not es_escritura:
            if accion in _TEMPORALES:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_OK   # lecturas, transacciones, funciones

        if solo_lectura:
            ultimo.append(f"escritura bloqueada en modo lectura ({arg1})")
            return sqlite3.SQLITE_DENY

        tabla = _nombre_tabla(accion, arg1, arg2)
        if _permitida(tabla):
            return sqlite3.SQLITE_OK

        ultimo.append(f"escritura fuera de alcance sobre «{tabla}»")
        return sqlite3.SQLITE_DENY

    return autorizador


class Conexion(sqlite3.Connection):
    """Conexión que traduce el rechazo del autorizador a un error legible."""

    _ultimo_motivo: list

    def execute(self, sql, parameters=(), /):
        try:
            return super().execute(sql, parameters)
        except sqlite3.DatabaseError as e:
            if "not authorized" in str(e).lower():
                motivo = self._ultimo_motivo[-1] if self._ultimo_motivo else str(e)
                raise AlcanceDenegado(
                    f"Guarda de alcance: {motivo}. "
                    f"El Centro sólo escribe tablas «{PREFIJO}*» en ops.db."
                ) from e
            raise

    def executescript(self, sql, /):
        try:
            return super().executescript(sql)
        except sqlite3.DatabaseError as e:
            if "not authorized" in str(e).lower():
                motivo = self._ultimo_motivo[-1] if self._ultimo_motivo else str(e)
                raise AlcanceDenegado(f"Guarda de alcance: {motivo}") from e
            raise


def abrir(ruta: str | Path, modo: str = "escritura",
          aplicar_pragmas: bool = True) -> Conexion:
    """
    Abre una conexión con los pragmas de producción y la guarda instalada.

    modo="escritura"  → sólo tablas bertok_ops_* (ops.db)
    modo="lectura"    → ninguna escritura (ML.db, picking.db, y cualquier
                        fuente ajena)
    """
    if modo not in ("escritura", "lectura"):
        raise ValueError("modo debe ser 'escritura' o 'lectura'")

    cx = sqlite3.connect(str(ruta), factory=Conexion, isolation_level=None)
    cx.row_factory = sqlite3.Row

    if aplicar_pragmas:
        # Antes de instalar la guarda: journal_mode y synchronous son
        # configuración de apertura, no escritura de datos.
        cx.execute("PRAGMA journal_mode = WAL")
        cx.execute("PRAGMA synchronous = FULL")
        cx.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        cx.execute(f"PRAGMA wal_autocheckpoint = {WAL_AUTOCHECKPOINT}")
        cx.execute("PRAGMA foreign_keys = ON")

    cx._ultimo_motivo = []
    cx.set_authorizer(_crear_autorizador(modo, cx._ultimo_motivo))
    return cx


def escribir(cx: Conexion, sql: str, parametros=()):
    """
    Azúcar para escrituras: usa BEGIN IMMEDIATE.

    Sin BEGIN IMMEDIATE se puede recibir SQLITE_BUSY aunque busy_timeout
    esté configurado, porque SQLite recién intenta tomar el lock de
    escritura al promover la transacción, y ahí ya es tarde.
    """
    cx.execute("BEGIN IMMEDIATE")
    try:
        cur = cx.execute(sql, parametros)
        cx.execute("COMMIT")
        return cur
    except Exception:
        cx.execute("ROLLBACK")
        raise
