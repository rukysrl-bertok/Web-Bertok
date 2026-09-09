# -*- coding: utf-8 -*-
"""
Sonda de verificacion de la API de Full de Mercado Libre.

Verifica, contra la API real y con el token de Bertok, cada punto del
catalogo de datos de Full (docs/catalogo-datos-full.md). No codificamos
nada que no haya contestado la API de verdad.

SOLO HACE GET. No crea, no modifica y no borra nada en Mercado Libre.
Lo unico que escribe es el informe de texto en la carpeta donde se corre.

Uso:
    set ML_ACCESS_TOKEN=APP_USR-...
    python sonda_api_full.py

    o bien:
    python sonda_api_full.py APP_USR-...

El token no se guarda en el informe: se enmascara.
Sin dependencias externas: solo biblioteca estandar.
"""

import os
import sys
import json
import ssl
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta

API = "https://api.mercadolibre.com"
ANCHO = 78
TIEMPO_ESPERA = 30
PAUSA = 0.15          # cortesia entre llamadas; el limite es 1500/min por vendedor

SALIDA = []
LLAMADAS = []         # (url, status, ms, rate_remaining)


def w(t=""):
    SALIDA.append(t)


def titulo(t, car="="):
    w()
    w(car * ANCHO)
    w(t)
    w(car * ANCHO)


def sub(t):
    w()
    w("--- " + t + " " + "-" * max(0, ANCHO - 6 - len(t)))


def enmascarar(token):
    if not token or len(token) < 12:
        return "(oculto)"
    return token[:8] + "..." + token[-4:]


def get(token, ruta, params=None):
    """GET contra la API. Devuelve (status, objeto, cabeceras). Nunca lanza."""
    url = ruta if ruta.startswith("http") else API + ruta
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    pedido = urllib.request.Request(url, method="GET")
    pedido.add_header("Authorization", "Bearer " + token)
    pedido.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    t0 = time.time()
    try:
        with urllib.request.urlopen(pedido, timeout=TIEMPO_ESPERA, context=ctx) as r:
            crudo = r.read()
            cab = dict(r.headers)
            estado = r.status
    except urllib.error.HTTPError as e:
        crudo = e.read()
        cab = dict(e.headers or {})
        estado = e.code
    except Exception as e:
        ms = int((time.time() - t0) * 1000)
        LLAMADAS.append((url, "EXC", ms, ""))
        return None, {"error_local": str(e)}, {}
    ms = int((time.time() - t0) * 1000)
    resto = cab.get("RateLimit-Remaining") or cab.get("X-RateLimit-Remaining") or ""
    LLAMADAS.append((url, estado, ms, resto))
    try:
        obj = json.loads(crudo.decode("utf-8", "replace"))
    except Exception:
        obj = {"cuerpo_no_json": crudo[:400].decode("utf-8", "replace")}
    time.sleep(PAUSA)
    return estado, obj, cab


def volcar(obj, sangria=2, prof=0, max_prof=3):
    """Imprime un objeto JSON de forma legible y acotada."""
    pre = " " * sangria
    if prof > max_prof:
        w(pre + "...")
        return
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:40]:
            if isinstance(v, (dict, list)):
                w("%s%s:" % (pre, k))
                volcar(v, sangria + 2, prof + 1, max_prof)
            else:
                w("%s%s: %s" % (pre, k, str(v)[:120]))
    elif isinstance(obj, list):
        for v in obj[:6]:
            if isinstance(v, (dict, list)):
                volcar(v, sangria + 2, prof + 1, max_prof)
                w(pre + "-")
            else:
                w("%s- %s" % (pre, str(v)[:120]))
        if len(obj) > 6:
            w("%s... (%d elementos en total)" % (pre, len(obj)))
    else:
        w(pre + str(obj)[:200])


# ------------------------------------------------------------------ pruebas

def p1_identidad(token):
    titulo("1. IDENTIDAD Y LIMITES")
    est, obj, cab = get(token, "/users/me")
    if est != 200:
        w("FALLO: el token no sirve o expiro. status=%s" % est)
        volcar(obj)
        return None, None
    sid, site = obj.get("id"), obj.get("site_id")
    w("seller_id : %s" % sid)
    w("site_id   : %s   (tiene que ser MLA)" % site)
    w("nickname  : %s" % obj.get("nickname"))
    w("tipo      : %s" % obj.get("user_type"))
    tags = obj.get("tags") or []
    w("tags      : %s" % ", ".join(str(t) for t in tags))
    for c in ("RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset",
              "X-RateLimit-Limit", "X-RateLimit-Remaining"):
        if c in cab:
            w("%-22s %s" % (c + ":", cab[c]))
    return sid, site


def p2_items_full(token, sid):
    titulo("2. ITEMS EN FULL Y SUS inventory_id")
    w("Se listan publicaciones activas y se busca cuales estan en fulfillment.")
    est, obj, _ = get(token, "/users/%s/items/search" % sid,
                      {"status": "active", "limit": 50})
    if est != 200:
        w("FALLO al listar items. status=%s" % est)
        volcar(obj)
        return []
    ids = obj.get("results") or []
    total = (obj.get("paging") or {}).get("total")
    w("publicaciones activas (total informado): %s" % total)
    w("se inspeccionan las primeras %d" % len(ids))

    full, con_var, sin_inv = [], 0, 0
    for i in range(0, len(ids), 20):
        lote = ids[i:i + 20]
        est2, obj2, _ = get(token, "/items", {"ids": ",".join(lote)})
        if est2 != 200 or not isinstance(obj2, list):
            continue
        for env in obj2:
            it = env.get("body") or {}
            if it.get("shipping", {}).get("logistic_type") != "fulfillment":
                continue
            variaciones = it.get("variations") or []
            invs = []
            if it.get("inventory_id"):
                invs.append(("(sin variacion)", it["inventory_id"]))
            for v in variaciones:
                if v.get("inventory_id"):
                    invs.append((str(v.get("id")), v["inventory_id"]))
            if variaciones:
                con_var += 1
            if not invs:
                sin_inv += 1
            full.append({
                "id": it.get("id"),
                "sku": (it.get("seller_custom_field")
                        or _sku_de_atributos(it) or ""),
                "titulo": (it.get("title") or "")[:52],
                "user_product_id": it.get("user_product_id"),
                "variaciones": len(variaciones),
                "inventarios": invs,
            })

    sub("Resultado")
    w("items en fulfillment (de la muestra) : %d" % len(full))
    w("de esos, con variaciones             : %d" % con_var)
    w("de esos, SIN inventory_id            : %d   <- si es >0, revisar" % sin_inv)
    w()
    w("VERIFICACION 1 del catalogo: un item con variaciones tiene un")
    w("inventory_id por variacion. Se confirma si arriba hay items con")
    w("variaciones > 1 y esa misma cantidad de inventarios.")
    w()
    for f in full[:12]:
        w("  %s | var=%d | up=%s | %s" % (f["id"], f["variaciones"],
                                          f["user_product_id"], f["titulo"]))
        for vid, inv in f["inventarios"][:6]:
            w("      %-14s -> %s" % (vid, inv))
    return full


def _sku_de_atributos(it):
    for a in (it.get("attributes") or []):
        if a.get("id") in ("SELLER_SKU", "GTIN"):
            return a.get("value_name")
    return None


def p3_stock(token, full):
    titulo("3. STOCK EN FULL Y not_available_detail")
    if not full:
        w("Sin items en fulfillment en la muestra: no se puede probar.")
        return
    probados = 0
    motivos = set()
    for f in full:
        for _, inv in f["inventarios"]:
            if probados >= 5:
                break
            est, obj, _ = get(token, "/inventories/%s/stock/fulfillment" % inv)
            sub("%s   (%s)" % (inv, f["titulo"]))
            w("status: %s" % est)
            volcar(obj)
            if isinstance(obj, dict):
                det = obj.get("not_available_detail")
                if isinstance(det, list):
                    for d in det:
                        if isinstance(d, dict) and d.get("status"):
                            motivos.add(str(d["status"]))
                elif isinstance(det, dict):
                    motivos.update(str(k) for k in det.keys())
            probados += 1
        if probados >= 5:
            break
    sub("VERIFICACION 2 del catalogo")
    w("motivos de not_available_detail observados: %s"
      % (", ".join(sorted(motivos)) if motivos else "NINGUNO en la muestra"))
    w("esperados: damaged, lost, withdrawal, internal_process, transfer")
    w("(noFiscalCoverage es solo Brasil; si aparece en MLA, anotarlo)")


def p4_operaciones(token, sid):
    titulo("4. MOVIMIENTOS DE STOCK (el libro mayor)")
    w("Es la prueba mas importante para reconstruir el historico:")
    w("si esto trae 12 meses, la cadencia real y la antiguedad del stock")
    w("se pueden calcular sin depender de nadie.")

    for meses, etiqueta in ((1, "ultimos 30 dias"), (12, "ultimos 12 meses")):
        desde = (datetime.now() - timedelta(days=30 * meses)).strftime("%Y-%m-%dT00:00:00.000-00:00")
        hasta = datetime.now().strftime("%Y-%m-%dT23:59:59.000-00:00")
        sub(etiqueta)
        est, obj, _ = get(token, "/stock/fulfillment/operations/search",
                          {"seller_id": sid, "date_from": desde, "date_to": hasta})
        w("status: %s" % est)
        if est != 200:
            volcar(obj)
            continue
        pag = obj.get("paging") or {}
        res = obj.get("results") or []
        w("paging: %s" % json.dumps(pag)[:200])
        w("operaciones en esta pagina: %d" % len(res))
        tipos = {}
        for r in res:
            tipos[str(r.get("type"))] = tipos.get(str(r.get("type")), 0) + 1
        w("tipos observados:")
        for t, n in sorted(tipos.items(), key=lambda x: -x[1]):
            w("    %-30s %d" % (t, n))
        if res:
            w()
            w("estructura de una operacion:")
            volcar(res[0], 4)
        if meses == 12:
            sub("VERIFICACION 3 del catalogo")
            w("hay 'scroll' en paging?  %s" % ("SI" if pag.get("scroll") else "NO"))
            w("total informado:         %s" % pag.get("total"))
            w("Si el total supera lo que trae una pagina, la ingesta necesita")
            w("paginar. Anotar el mecanismo exacto que devolvio ML.")
            w()
            w("inbound_reception encontrados: %d" % tipos.get("inbound_reception", 0))
            w("Cada grupo de inbound_reception con fechas contiguas es un envio")
            w("de reposicion pasado. De ahi sale la cadencia real.")
            w()
            w("descartes (withdrawal_discarded + withdrawal_removal): %d"
              % (tipos.get("withdrawal_discarded", 0) + tipos.get("withdrawal_removal", 0)))


def p5_cargos(token):
    titulo("5. CARGOS REALES DE FULL  --  LA PRUEBA DECISIVA")
    w("De esto depende poder calcular el costo de pasarse. Si este bloque")
    w("no responde, el motor de calculo no se puede escribir con datos medidos.")

    sub("Periodos de facturacion disponibles")
    est, obj, _ = get(token, "/billing/monthly/periods", {"group": "ML"})
    w("status: %s" % est)
    periodos = []
    if est == 200:
        res = obj.get("results") if isinstance(obj, dict) else obj
        if isinstance(res, list):
            for p in res:
                k = p.get("key") or p.get("expiration_date")
                if k:
                    periodos.append(str(k))
                w("  key=%-14s estado=%-12s monto=%s  %s"
                  % (p.get("key"), p.get("period_status"), p.get("amount"),
                     json.dumps(p.get("period") or {})[:60]))
        else:
            volcar(obj)
    else:
        volcar(obj)

    if not periodos:
        w()
        w("No se obtuvieron periodos. Se prueba igual con el mes en curso y")
        w("los dos anteriores, armando la key a mano (primer dia del mes).")
        hoy = datetime.now()
        for atras in range(0, 3):
            m = hoy.month - atras
            a = hoy.year
            while m <= 0:
                m += 12
                a -= 1
            periodos.append("%04d-%02d-01" % (a, m))

    tipos_vistos = {}
    for k in periodos[:6]:
        sub("Detalle de Full del periodo %s" % k)
        est, obj, _ = get(token,
                          "/billing/integration/periods/key/%s/group/ML/full/details" % k)
        w("status: %s" % est)
        if est != 200:
            volcar(obj)
            continue
        res = obj.get("results") if isinstance(obj, dict) else obj
        if not isinstance(res, list):
            volcar(obj, max_prof=2)
            continue
        w("filas de cargo: %d" % len(res))
        if res:
            w("estructura de una fila:")
            volcar(res[0], 4)
        for r in res:
            if not isinstance(r, dict):
                continue
            ct = str(r.get("charge_type") or r.get("detail") or r.get("concept") or "?")
            imp = 0.0
            for campo in ("charge_amount_without_discount", "charge_amount",
                          "amount", "total_amount"):
                if r.get(campo) is not None:
                    try:
                        imp = float(r[campo])
                    except Exception:
                        imp = 0.0
                    break
            n, s = tipos_vistos.get(ct, (0, 0.0))
            tipos_vistos[ct] = (n + 1, s + imp)

    sub("VERIFICACION 4 y 5 del catalogo  --  charge_type REALES")
    if tipos_vistos:
        w("%-32s %8s %16s" % ("charge_type", "filas", "importe"))
        w("-" * 58)
        for ct, (n, s) in sorted(tipos_vistos.items(), key=lambda x: -x[1][1]):
            w("%-32s %8d %16.2f" % (ct, n, s))
        w()
        esperados = ["WAREHOUSING", "AGING", "INBOUND_COLLECT", "INBOUND_PENALTY",
                     "WITHDRAWAL", "OVERAGE", "SPACE_PURCHASE", "SPACE_CANCELLATION"]
        faltan = [e for e in esperados if e not in tipos_vistos]
        sobran = [t for t in tipos_vistos if t not in esperados]
        w("esperados y NO vistos : %s" % (", ".join(faltan) or "ninguno"))
        w("vistos y NO esperados : %s" % (", ".join(sobran) or "ninguno"))
        w()
        w("WAREHOUSING = almacenamiento  -> costo de pasarse (a)")
        w("AGING       = stock viejo     -> senal temprana del descarte")
        w("INBOUND_COLLECT = flete de la reposicion -> reconstruye el historico")
        w()
        w("RECORDATORIO: los importes de facturacion de ML son all-in,")
        w("ya incluyen IVA. Nunca multiplicarlos por 1,21.")
    else:
        w("NO se obtuvo ningun cargo. Es el resultado mas importante de la sonda:")
        w("sin esto hay que ir por el reporte XLSX o por la factura real.")


def p6_canales(token, full):
    titulo("6. REPARTO ENTRE CANALES (Full vs Flex/local)")
    w("VERIFICACION 6: /user-products/$ID/stock tiene que devolver las dos")
    w("ubicaciones. Es lo que sostiene todo el costo oculto del modelo.")
    ups = [f["user_product_id"] for f in full if f.get("user_product_id")]
    if not ups:
        w()
        w("Ningun item de la muestra trae user_product_id. Verificar si en MLA")
        w("hace falta pedir el item con el parametro de formato nuevo.")
        return
    for up in ups[:4]:
        sub("user_product %s" % up)
        est, obj, _ = get(token, "/user-products/%s/stock" % up)
        w("status: %s" % est)
        volcar(obj)


def p7_ventas_por_canal(token, sid):
    titulo("7. VENTAS POR CANAL (demanda separada)")
    desde = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%dT00:00:00.000-00:00")
    est, obj, _ = get(token, "/orders/search",
                      {"seller": sid, "order.date_created.from": desde,
                       "sort": "date_desc", "limit": 50})
    w("status: %s" % est)
    if est != 200:
        volcar(obj)
        return
    res = obj.get("results") or []
    w("ordenes en la muestra: %d  (total informado: %s)"
      % (len(res), (obj.get("paging") or {}).get("total")))
    canales = {}
    for o in res:
        lt = ((o.get("shipping") or {}).get("logistic_type")) or "(sin dato en la orden)"
        canales[str(lt)] = canales.get(str(lt), 0) + 1
    w()
    w("logistic_type observados:")
    for k, v in sorted(canales.items(), key=lambda x: -x[1]):
        w("    %-28s %d" % (k, v))
    w()
    w("fulfillment = Full | self_service = Flex | cross_docking/drop_off = colecta")
    w("Si la orden no trae logistic_type, hay que pedir el envio:")
    w("  GET /shipments/$SHIPMENT_ID  con la cabecera x-format-new: true")


def p8_reportes(token):
    titulo("8. REPORTES DESCARGABLES  --  ¿traen la sugerencia de ML?")
    w("VERIFICACION 7: el unico camino automatico posible para la sugerencia")
    w("de cantidades de ML seria que venga en algun XLSX. Aca solo se listan")
    w("los reportes disponibles: NO se genera ninguno (eso es un POST).")
    for ruta in ("/users/me/report/settings", "/billing/integration/reports"):
        sub(ruta)
        est, obj, _ = get(token, ruta)
        w("status: %s" % est)
        volcar(obj, max_prof=2)
    w()
    w("Si esto no da nada, la sugerencia de ML se carga a mano una vez por")
    w("ciclo, con su fecha. Son ~15 dias entre ciclos: el costo es de minutos.")


def resumen():
    titulo("RESUMEN DE LLAMADAS")
    w("%-58s %6s %7s %10s" % ("url", "status", "ms", "restante"))
    w("-" * ANCHO)
    for url, est, ms, resto in LLAMADAS:
        u = url.replace(API, "")
        if len(u) > 58:
            u = u[:55] + "..."
        w("%-58s %6s %7s %10s" % (u, est, ms, resto))
    w()
    ok = sum(1 for _, e, _, _ in LLAMADAS if e == 200)
    w("llamadas: %d   con exito: %d   fallidas: %d"
      % (len(LLAMADAS), ok, len(LLAMADAS) - ok))
    w()
    w("VERIFICACION 8: el limite es 1.500 requests por minuto por vendedor.")
    w("La columna 'restante' es la cabecera RateLimit-Remaining, si ML la manda.")


def main():
    token = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ML_ACCESS_TOKEN", "")).strip()
    if not token:
        print("Falta el token. Pasalo como argumento o en ML_ACCESS_TOKEN:")
        print("   set ML_ACCESS_TOKEN=APP_USR-...")
        print("   python sonda_api_full.py")
        return 1

    w("SONDA DE VERIFICACION DE LA API DE FULL")
    w("generado: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    w("token:    %s" % enmascarar(token))
    w("modo:     SOLO LECTURA (unicamente GET)")

    sid, site = p1_identidad(token)
    if not sid:
        w()
        w("Sin identidad valida no se puede seguir. Renovar el token y repetir.")
    else:
        if site and site != "MLA":
            w()
            w("ATENCION: el site es %s, no MLA. Los resultados pueden no aplicar." % site)
        full = p2_items_full(token, sid)
        p3_stock(token, full)
        p4_operaciones(token, sid)
        p5_cargos(token)
        p6_canales(token, full)
        p7_ventas_por_canal(token, sid)
        p8_reportes(token)
    resumen()

    destino = os.path.join(os.getcwd(), "sonda_api_full.txt")
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write("\n".join(SALIDA))
    print("Informe escrito en: %s" % destino)
    print("Lineas: %d   Llamadas: %d" % (len(SALIDA), len(LLAMADAS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
