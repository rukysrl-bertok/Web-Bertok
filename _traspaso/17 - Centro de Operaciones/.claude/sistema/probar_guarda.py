"""
Centro de Operaciones Bertok — prueba de la guarda de alcance.

Toma una base descartable, le agrega una tabla ajena a propósito, y le
tira encima un set de sentencias destructivas. TODAS tienen que fallar.
Además verifica que lo que sí está permitido siga funcionando: una guarda
que bloquea todo no sirve de nada.

Es el equivalente de las sentencias destructivas con las que se probó la
guarda de Bertok BI, y se corre después de cada cambio en guarda_alcance.py
o en el esquema.

Uso:
    python probar_guarda.py
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

from guarda_alcance import AlcanceDenegado, abrir

ESQUEMA = Path(__file__).with_name("esquema_ops.sql")

VERDE, ROJO, GRIS, FIN = "\033[32m", "\033[31m", "\033[90m", "\033[0m"


class Resultado:
    def __init__(self) -> None:
        self.ok = 0
        self.fallos: list[str] = []

    def afirmar(self, condicion: bool, titulo: str, detalle: str = "") -> None:
        if condicion:
            self.ok += 1
            print(f"  {VERDE}OK{FIN}    {titulo}")
        else:
            self.fallos.append(titulo)
            print(f"  {ROJO}FALLA{FIN} {titulo}   {GRIS}{detalle}{FIN}")


def debe_fallar(cx, sql, res: Resultado, titulo: str, excepciones=(AlcanceDenegado,)):
    try:
        cx.execute(sql)
    except excepciones as e:
        res.afirmar(True, titulo)
        return
    except sqlite3.DatabaseError as e:
        res.afirmar(True, titulo)
        return
    res.afirmar(False, titulo, "la sentencia NO fue bloqueada")


def debe_funcionar(cx, sql, res: Resultado, titulo: str, parametros=()):
    try:
        cx.execute(sql, parametros)
        res.afirmar(True, titulo)
    except Exception as e:
        res.afirmar(False, titulo, f"{type(e).__name__}: {e}")


def main() -> int:
    res = Resultado()
    tmp = Path(tempfile.mkdtemp(prefix="prueba_ops_"))
    ruta = tmp / "ops_prueba.db"

    # Tabla ajena creada SIN la guarda, para tener un blanco realista:
    # simula cualquier tabla de otro módulo que no debe poder tocarse.
    crudo = sqlite3.connect(ruta)
    crudo.executescript("""
        CREATE TABLE tabla_ajena (id INTEGER PRIMARY KEY, valor TEXT);
        INSERT INTO tabla_ajena (valor) VALUES ('no me toques');
        CREATE TABLE bertok_bi_snapshot (id INTEGER PRIMARY KEY, valor TEXT);
    """)
    crudo.commit()
    crudo.close()

    print(f"\n{GRIS}Base de prueba: {ruta}{FIN}\n")

    # =================================================================
    print("MODO ESCRITURA — el esquema se aplica con la guarda puesta")
    print("-" * 62)
    with abrir(ruta, modo="escritura") as cx:
        debe_funcionar(cx, ESQUEMA.read_text(encoding="utf-8").split(";")[0] + ";",
                       res, "PRAGMA foreign_keys pasa")
        cx.executescript(ESQUEMA.read_text(encoding="utf-8"))
        res.afirmar(True, "el esquema completo se aplica sin ser bloqueado")

        print("\nSENTENCIAS DESTRUCTIVAS — todas deben fallar")
        print("-" * 62)
        destructivas = [
            ("INSERT en tabla ajena",
             "INSERT INTO tabla_ajena (valor) VALUES ('intruso')"),
            ("UPDATE en tabla ajena",
             "UPDATE tabla_ajena SET valor = 'pisado'"),
            ("DELETE en tabla ajena",
             "DELETE FROM tabla_ajena"),
            ("INSERT en tabla de Bertok BI",
             "INSERT INTO bertok_bi_snapshot (valor) VALUES ('intruso')"),
            ("UPDATE en tabla de Bertok BI",
             "UPDATE bertok_bi_snapshot SET valor = 'pisado'"),
            ("DROP de tabla ajena",
             "DROP TABLE tabla_ajena"),
            ("CREATE TABLE sin el prefijo",
             "CREATE TABLE colada (id INTEGER)"),
            ("ALTER de tabla ajena",
             "ALTER TABLE tabla_ajena ADD COLUMN extra TEXT"),
            ("CREATE INDEX sobre tabla ajena",
             "CREATE INDEX ix_colado ON tabla_ajena (valor)"),
            ("CREATE TRIGGER sobre tabla ajena",
             "CREATE TRIGGER tr_colado AFTER INSERT ON tabla_ajena "
             "BEGIN SELECT 1; END"),
            ("CREATE VIEW sin el prefijo",
             "CREATE VIEW vista_colada AS SELECT 1"),
            ("ATTACH de otra base",
             "ATTACH DATABASE 'ML.db' AS ml"),
            ("PRAGMA writable_schema",
             "PRAGMA writable_schema = ON"),
            ("INSERT con nombre entre comillas",
             'INSERT INTO "tabla_ajena" (valor) VALUES (\'intruso\')'),
            ("INSERT con mayúsculas y comentario",
             "/* zafo */ INSERT INTO TABLA_AJENA (valor) VALUES ('intruso')"),
        ]
        for titulo, sql in destructivas:
            debe_fallar(cx, sql, res, titulo)

        print("\nINTEGRIDAD DEL ESQUEMA — los triggers y CHECK deben morder")
        print("-" * 62)
        cx.execute("INSERT INTO bertok_ops_personas (persona_id, nombre) "
                   "VALUES ('p1', 'Prueba')")
        cx.execute("INSERT INTO bertok_ops_procesos "
                   "(proceso_id, nombre, tipo, modo_asignacion, dueno_id) "
                   "VALUES ('pr1', 'Prueba', 'informativa', 'fijo', 'p1')")
        cx.execute("INSERT INTO bertok_ops_eventos (proceso_id, tipo) "
                   "VALUES ('pr1', 'detectado')")
        cx.execute("INSERT INTO bertok_ops_hallazgos "
                   "(proceso_id, clave_natural, datos_al) "
                   "VALUES ('pr1', 'prueba:1', '2026-09-05 10:00:00')")

        debe_fallar(cx, "UPDATE bertok_ops_eventos SET tipo = 'otro'", res,
                    "eventos es append-only: no acepta UPDATE")
        debe_fallar(cx, "DELETE FROM bertok_ops_eventos", res,
                    "eventos es append-only: no acepta DELETE")
        debe_fallar(cx, "DELETE FROM bertok_ops_personas WHERE persona_id='p1'",
                    res, "una persona no se borra, se marca inactiva")
        debe_fallar(cx, "UPDATE bertok_ops_hallazgos "
                        "SET nacido_en = '2020-01-01 00:00:00'", res,
                    "nacido_en es inmutable")
        debe_fallar(cx, "INSERT INTO bertok_ops_hallazgos "
                        "(proceso_id, clave_natural, datos_al) "
                        "VALUES ('pr1', 'prueba:1', '2026-09-05 10:00:00')", res,
                    "no puede haber dos veces la misma clave natural viva")
        debe_fallar(cx, "UPDATE bertok_ops_hallazgos "
                        "SET estado='resuelto', resuelto_motivo=NULL", res,
                    "un hallazgo resuelto exige motivo")
        debe_fallar(cx, "INSERT INTO bertok_ops_procesos "
                        "(proceso_id, nombre, tipo, modo_asignacion) "
                        "VALUES ('pr2','X','informativa','fijo')", res,
                    "un proceso de asignación fija exige dueño")
        debe_fallar(cx, "INSERT INTO bertok_ops_procesos "
                        "(proceso_id, nombre, tipo, madurez, modo_asignacion, dueno_id) "
                        "VALUES ('pr3','X','informativa','encendida','fijo','p1')",
                    res, "madurez sólo acepta los cuatro estados definidos")

        print("\nLO QUE SÍ TIENE QUE FUNCIONAR")
        print("-" * 62)
        debe_funcionar(cx, "INSERT INTO bertok_ops_eventos "
                           "(proceso_id, tipo, version) VALUES ('pr1','visible',1)",
                       res, "se puede escribir en bertok_ops_eventos")
        debe_funcionar(cx, "UPDATE bertok_ops_hallazgos SET prioridad = 50", res,
                       "se puede actualizar un hallazgo")
        debe_funcionar(cx, "SELECT COUNT(*) FROM tabla_ajena", res,
                       "se puede LEER una tabla ajena (el Centro lee todo)")
        debe_funcionar(cx, "SELECT COUNT(*) FROM bertok_bi_snapshot", res,
                       "se puede LEER las tablas de Bertok BI")

        # Archivar y volver a crear la misma clave: NO revive, nace de nuevo.
        cx.execute("UPDATE bertok_ops_hallazgos "
                   "SET estado='archivado', resuelto_motivo='automatico', "
                   "    archivado_en=datetime('now','localtime') "
                   "WHERE clave_natural='prueba:1'")
        debe_funcionar(cx, "INSERT INTO bertok_ops_hallazgos "
                           "(proceso_id, clave_natural, datos_al, hallazgo_previo_id) "
                           "VALUES ('pr1','prueba:1','2026-09-06 10:00:00',1)", res,
                       "una clave archivada puede volver a nacer, enlazada")

    # =================================================================
    print("\nMODO LECTURA — ninguna escritura, ni siquiera con el prefijo")
    print("-" * 62)
    with abrir(ruta, modo="lectura") as cx:
        debe_fallar(cx, "INSERT INTO bertok_ops_eventos (proceso_id, tipo) "
                        "VALUES ('pr1','x')", res,
                    "en modo lectura no se escribe ni en bertok_ops_*")
        debe_fallar(cx, "UPDATE tabla_ajena SET valor='x'", res,
                    "en modo lectura no se escribe en tablas ajenas")
        debe_funcionar(cx, "SELECT COUNT(*) FROM bertok_ops_hallazgos", res,
                       "en modo lectura se puede consultar")

    # =================================================================
    print("\n" + "=" * 62)
    if res.fallos:
        print(f"{ROJO}  {len(res.fallos)} FALLA(S) — la guarda NO está lista{FIN}")
        for f in res.fallos:
            print(f"    - {f}")
        return 1
    print(f"{VERDE}  {res.ok} comprobaciones, todas OK.{FIN}")
    print("  La guarda bloquea todo lo que debe bloquear y deja pasar lo que debe.")
    print(f"{GRIS}  Estado: probado por código (amarillo). Verde recién cuando"
          f" una persona lo use.{FIN}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
