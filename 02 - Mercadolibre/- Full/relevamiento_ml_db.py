# -*- coding: utf-8 -*-
"""
Relevamiento de ML.db para el modulo de Reposicion a Full.

ESTRICTAMENTE DE SOLO LECTURA. Abre la base con mode=ro: SQLite rechaza a nivel
motor cualquier INSERT/UPDATE/DELETE/DDL. No escribe, no bloquea, no crea -wal.
Lo unico que crea es el informe de texto en la carpeta donde se lo corre.

Uso:
    python relevamiento_full.py "C:\\ruta\\a\\ML.db"
    python relevamiento_full.py            (intenta ubicarla sola)

Sin dependencias externas: solo biblioteca estandar.
"""

import os
import re
import sys
import sqlite3
from datetime import datetime

# ---------------------------------------------------------------- parametros

MAX_CARDINALIDAD = 80      # hasta cuantos valores distintos se listan de una columna
MUESTRA_FILAS = 3          # filas de muestra por tabla de bertok_bi_*
ANCHO = 78

PATRONES_FULL = [
    "full", "fulfil", "inbound", "restock", "reposic", "sugeren",
    "suggest", "almacen", "storage", "stock", "deposito", "envio",
    "shipment", "shipping", "flete", "logistic", "disponib",
    "available", "canal", "recolec", "pickup",
]

NOMBRES_BASE = ["ML.db", "ml.db"]

# ---------------------------------------------------------------- utilidades

SALIDA = []


def w(texto=""):
    SALIDA.append(texto)


def titulo(txt, car="="):
    w()
    w(car * ANCHO)
    w(txt)
    w(car * ANCHO)


def sub(txt):
    w()
    w("--- " + txt + " " + "-" * max(0, ANCHO - 6 - len(txt)))


def ubicar_base():
    """Busca ML.db en rutas tipicas si no vino por argumento."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    candidatas = []
    raices = [
        os.path.expanduser("~"),
        os.path.join(os.path.expanduser("~"), "OneDrive"),
        os.getcwd(),
        os.path.abspath(os.path.join(os.getcwd(), "..")),
        os.path.abspath(os.path.join(os.getcwd(), "..", "..")),
    ]
    vistos = set()
    for raiz in raices:
        if not os.path.isdir(raiz) or raiz in vistos:
            continue
        vistos.add(raiz)
        for base, dirs, files in os.walk(raiz):
            dirs[:] = [d for d in dirs if not d.startswith(".")
                       and d.lower() not in ("node_modules", "venv", "__pycache__",
                                             "appdata", "windows", "program files")]
            if base.count(os.sep) - raiz.count(os.sep) > 4:
                dirs[:] = []
                continue
            for f in files:
                if f in NOMBRES_BASE:
                    candidatas.append(os.path.join(base, f))
            if len(candidatas) > 6:
                break
        if candidatas:
            break
    if not candidatas:
        return None
    candidatas.sort(key=lambda p: -os.path.getsize(p))
    return candidatas[0]


def conectar_ro(ruta):
    uri = "file:" + ruta.replace("?", "%3f").replace("#", "%23") + "?mode=ro"
    cx = sqlite3.connect(uri, uri=True, timeout=10)
    cx.text_factory = lambda b: b.decode("utf-8", "replace")
    return cx


def q(cx, sql, args=()):
    try:
        cur = cx.execute(sql, args)
        return cur.fetchall(), [d[0] for d in (cur.description or [])]
    except Exception as e:
        return [("ERROR: %s" % e,)], ["error"]


def tabla_md(cols, filas, limite=None):
    if not filas:
        w("  (sin filas)")
        return
    if limite:
        filas = filas[:limite]
    anchos = [len(str(c)) for c in cols]
    for f in filas:
        for i, v in enumerate(f):
            if i < len(anchos):
                anchos[i] = max(anchos[i], min(len(str(v)), 46))
    def linea(vals):
        celdas = []
        for i, v in enumerate(vals):
            s = str(v)
            if len(s) > 46:
                s = s[:43] + "..."
            celdas.append(s.ljust(anchos[i]) if i < len(anchos) else s)
        return "  " + " | ".join(celdas)
    w(linea(cols))
    w("  " + "-+-".join("-" * a for a in anchos))
    for f in filas:
        w(linea(f))


# ---------------------------------------------------------------- secciones

def inventario(cx):
    titulo("1. INVENTARIO DE TABLAS DE ML.db")
    filas, _ = q(cx, """
        SELECT name, type FROM sqlite_master
        WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tablas = []
    datos = []
    for fila in filas:
        if len(fila) != 2 or not isinstance(fila[0], str):
            continue
        nombre, tipo = fila
        n, _ = q(cx, 'SELECT COUNT(*) FROM "%s"' % nombre)
        try:
            cant = n[0][0]
        except Exception:
            cant = "?"
        cols, _ = q(cx, 'PRAGMA table_info("%s")' % nombre)
        ncols = len(cols)
        tablas.append(nombre)
        datos.append((nombre, tipo, cant, ncols))
    w("Total de objetos: %d" % len(datos))
    w()
    tabla_md(["objeto", "tipo", "filas", "columnas"], datos)

    sub("Agrupado por prefijo (convencion de nombres)")
    pref = {}
    for nombre, tipo, cant, ncols in datos:
        p = nombre.split("_")[0] if "_" in nombre else "(sin prefijo)"
        if nombre.startswith("bertok_bi_"):
            p = "bertok_bi_"
        pref.setdefault(p, []).append(nombre)
    for p in sorted(pref):
        w("  %-22s %3d  ->  %s" % (p, len(pref[p]), ", ".join(sorted(pref[p])[:8])
                                   + (" ..." if len(pref[p]) > 8 else "")))
    return tablas


def ddl_completo(cx):
    titulo("2. DDL COMPLETO (esquema)")
    filas, _ = q(cx, """
        SELECT type, name, sql FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%' AND sql IS NOT NULL
        ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'view' THEN 1 ELSE 2 END, name
    """)
    for tipo, nombre, sql in filas:
        w()
        w("-- [%s] %s" % (tipo, nombre))
        w(sql if isinstance(sql, str) else str(sql))
        w(";")


def rastreo_full(cx, tablas):
    titulo("3. RASTREO DE FULL (tablas y columnas candidatas)")
    sub("Tablas cuyo NOMBRE menciona Full / inbound / stock / sugerencia")
    hit_t = [t for t in tablas
             if any(p in t.lower() for p in PATRONES_FULL)]
    for t in hit_t:
        n, _ = q(cx, 'SELECT COUNT(*) FROM "%s"' % t)
        w("  %-42s %s filas" % (t, n[0][0]))
    if not hit_t:
        w("  NINGUNA. -> Full no esta modelado por nombre de tabla.")

    sub("Columnas cuyo NOMBRE menciona esos terminos")
    encontrados = 0
    for t in tablas:
        cols, _ = q(cx, 'PRAGMA table_info("%s")' % t)
        for c in cols:
            try:
                cn = c[1]
            except Exception:
                continue
            if any(p in str(cn).lower() for p in PATRONES_FULL):
                w("  %-42s . %s" % (t, cn))
                encontrados += 1
    if not encontrados:
        w("  NINGUNA.")

    sub("Columnas de texto con VALORES que mencionan FULL / fulfillment")
    # busca en columnas de baja cardinalidad para no barrer texto libre
    for t in tablas:
        cols, _ = q(cx, 'PRAGMA table_info("%s")' % t)
        for c in cols:
            try:
                cn, ctipo = c[1], str(c[2]).upper()
            except Exception:
                continue
            if "CHAR" not in ctipo and "TEXT" not in ctipo and ctipo != "":
                continue
            r, _ = q(cx, 'SELECT COUNT(DISTINCT "%s") FROM "%s"' % (cn, t))
            try:
                card = r[0][0]
            except Exception:
                continue
            if not isinstance(card, int) or card > MAX_CARDINALIDAD or card == 0:
                continue
            r2, _ = q(cx,
                      'SELECT DISTINCT "%s" FROM "%s" WHERE lower("%s") LIKE \'%%full%%\''
                      ' OR lower("%s") LIKE \'%%fulfil%%\''
                      ' OR lower("%s") LIKE \'%%inbound%%\''
                      ' OR lower("%s") LIKE \'%%almacen%%\' LIMIT 12'
                      % (cn, t, cn, cn, cn, cn))
            vals = [str(x[0]) for x in r2 if x and x[0] is not None]
            if vals:
                w("  %-34s . %-22s -> %s" % (t, cn, " | ".join(vals)))


def cargos(cx, tablas):
    titulo("4. CARGOS DE ML: ?SE IDENTIFICA EL ALMACENAMIENTO DE FULL?")
    # candidatas: tablas cuyo nombre suene a cargo/costo/tarifa/liquidacion
    pat = ["cargo", "costo", "coste", "tarifa", "fee", "liquid", "billing",
           "factur", "comision", "settle", "detalle"]
    cand = [t for t in tablas if any(p in t.lower() for p in pat)]
    if not cand:
        w("  No se detectaron tablas de cargos por nombre. Revisar el inventario.")
    for t in cand:
        n, _ = q(cx, 'SELECT COUNT(*) FROM "%s"' % t)
        sub("%s  (%s filas)" % (t, n[0][0]))
        cols, _ = q(cx, 'PRAGMA table_info("%s")' % t)
        nombres = [c[1] for c in cols if isinstance(c, tuple) and len(c) > 1]
        w("  columnas: " + ", ".join(str(x) for x in nombres))
        # columnas categoricas -> distribucion
        for cn in nombres:
            r, _ = q(cx, 'SELECT COUNT(DISTINCT "%s") FROM "%s"' % (cn, t))
            try:
                card = r[0][0]
            except Exception:
                continue
            if not isinstance(card, int) or card == 0 or card > MAX_CARDINALIDAD:
                continue
            # buscar una columna de importe para sumar
            imp = None
            for posible in nombres:
                pl = str(posible).lower()
                if any(k in pl for k in ("importe", "monto", "amount", "total",
                                         "valor", "cargo", "costo")):
                    imp = posible
                    break
            if imp and imp != cn:
                r2, c2 = q(cx, 'SELECT "%s" AS valor, COUNT(*) AS filas,'
                               ' ROUND(SUM(CAST("%s" AS REAL)),2) AS suma'
                               ' FROM "%s" GROUP BY 1 ORDER BY 2 DESC LIMIT %d'
                               % (cn, imp, t, MAX_CARDINALIDAD))
            else:
                r2, c2 = q(cx, 'SELECT "%s" AS valor, COUNT(*) AS filas'
                               ' FROM "%s" GROUP BY 1 ORDER BY 2 DESC LIMIT %d'
                               % (cn, t, MAX_CARDINALIDAD))
            w()
            w("  > distribucion de [%s]  (%d valores distintos)" % (cn, card))
            tabla_md(c2, r2)
        # rango de fechas
        for cn in nombres:
            if any(k in str(cn).lower() for k in ("fecha", "date", "periodo", "mes")):
                r3, _ = q(cx, 'SELECT MIN("%s"), MAX("%s") FROM "%s"' % (cn, cn, t))
                w("  rango de [%s]: %s  ->  %s" % (cn, r3[0][0], r3[0][1]))


def historico_envios(cx, tablas):
    titulo("5. ?HAY HISTORICO DE ENVIOS DE REPOSICION?")
    w("Se busca: cargos de flete de inbound, o cualquier tabla de envios propios.")
    pat = ["flete", "shipping", "envio", "inbound", "shipment", "recolec"]
    cand = [t for t in tablas if any(p in t.lower() for p in pat)]
    if cand:
        for t in cand:
            n, _ = q(cx, 'SELECT COUNT(*) FROM "%s"' % t)
            w("  candidata: %-40s %s filas" % (t, n[0][0]))
    else:
        w("  Ninguna tabla con ese nombre.")
    w()
    w("Si no hay tabla propia, la reconstruccion tiene que salir de agrupar los")
    w("cargos por fecha: un envio de reposicion deberia verse como un pico aislado")
    w("de cargo de flete cada ~15 dias. Eso se evalua con la seccion 4.")


def bi(cx, tablas):
    titulo("6. BERTOK_BI_*: QUE HAY YA CALCULADO (demanda, rotacion, ABC)")
    bis = [t for t in tablas if t.startswith("bertok_bi_")]
    w("Tablas bertok_bi_*: %d" % len(bis))
    for t in bis:
        n, _ = q(cx, 'SELECT COUNT(*) FROM "%s"' % t)
        sub("%s  (%s filas)" % (t, n[0][0]))
        cols, _ = q(cx, 'PRAGMA table_info("%s")' % t)
        w("  columnas: " + ", ".join(str(c[1]) for c in cols
                                     if isinstance(c, tuple) and len(c) > 1))
        r, c = q(cx, 'SELECT * FROM "%s" LIMIT %d' % (t, MUESTRA_FILAS))
        tabla_md(c, r)


def frescura(cx, tablas):
    titulo("7. FRESCURA DE LOS DATOS (max fecha por tabla)")
    for t in tablas:
        cols, _ = q(cx, 'PRAGMA table_info("%s")' % t)
        for c in cols:
            try:
                cn = str(c[1])
            except Exception:
                continue
            if re.search(r"fecha|date|periodo|actualiz|timestamp", cn, re.I):
                r, _ = q(cx, 'SELECT MIN("%s"), MAX("%s") FROM "%s"' % (cn, cn, t))
                try:
                    w("  %-40s %-22s %s -> %s" % (t, cn, r[0][0], r[0][1]))
                except Exception:
                    pass
                break


def contexto_archivos():
    titulo("8. CONTEXTO DE ARCHIVOS (scripts y convenciones)")
    raiz = os.getcwd()
    w("Corriendo desde: %s" % raiz)
    w()
    w("Arbol (3 niveles, sin ocultos):")
    for base, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d.lower() not in ("__pycache__", "venv", "node_modules")]
        prof = base[len(raiz):].count(os.sep)
        if prof > 2:
            dirs[:] = []
            continue
        w("  " + "  " * prof + os.path.basename(base) + os.sep)
        for f in sorted(files)[:40]:
            w("  " + "  " * (prof + 1) + f)

    sub("Encabezado de actualizar_ml.py, si esta")
    for base, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.lower() in ("actualizar_ml.py",) or f.lower().endswith(".bat"):
                ruta = os.path.join(base, f)
                w()
                w("### %s" % ruta)
                try:
                    with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                        for i, linea in enumerate(fh):
                            if i >= 80:
                                w("    ... (recortado a 80 lineas)")
                                break
                            w("    " + linea.rstrip())
                except Exception as e:
                    w("    no se pudo leer: %s" % e)


# ---------------------------------------------------------------- principal

def main():
    ruta = ubicar_base()
    if not ruta or not os.path.isfile(ruta):
        print("No encontre ML.db. Pasala como argumento:")
        print('   python relevamiento_full.py "C:\\ruta\\a\\ML.db"')
        return 1

    w("RELEVAMIENTO DE ML.db PARA REPOSICION A FULL")
    w("generado: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    w("base:     %s" % os.path.abspath(ruta))
    w("tamano:   %.1f MB" % (os.path.getsize(ruta) / 1048576.0))
    w("modo:     SOLO LECTURA (sqlite mode=ro)")

    cx = conectar_ro(ruta)
    try:
        tablas = inventario(cx)
        ddl_completo(cx)
        rastreo_full(cx, tablas)
        cargos(cx, tablas)
        historico_envios(cx, tablas)
        bi(cx, tablas)
        frescura(cx, tablas)
    finally:
        cx.close()

    contexto_archivos()

    destino = os.path.join(os.getcwd(), "relevamiento_full.txt")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write("\n".join(SALIDA))
    print("Informe escrito en: %s" % destino)
    print("Lineas: %d" % len(SALIDA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
