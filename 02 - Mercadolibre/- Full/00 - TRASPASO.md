# TRASPASO — Reposición a Full de Mercado Libre

**Documento de arranque para una sesión nueva. Es autocontenido: leyendo esto
alcanza para retomar el trabajo sin haber visto la conversación anterior.**

- **Proyecto:** Reposición a Full — Bertok
- **Ruta:** `C:\Users\gcorzo\Ruky S.R.L\Bertok - Documentos\02 - Mercadolibre\- Full`
- **Interlocutor:** Gerardo Corzo
- **Fecha de traspaso:** 09/09/2026
- **Estado:** relevamiento pendiente. **Cero código de producción escrito.**

### Índice

1. [Lo primero que tenés que saber](#1-lo-primero-que-tenés-que-saber)
2. [El brief original, textual](#2-el-brief-original-textual)
3. [Contexto de la operación](#3-contexto-de-la-operación)
4. [El modelo económico](#4-el-modelo-económico-el-corazón-del-problema)
5. [Reglas duras de Bertok](#5-reglas-duras-de-bertok)
6. [Reglas de ML.db](#6-reglas-de-mldb)
7. [Stop conditions](#7-stop-conditions)
8. [El relevamiento pendiente](#8-el-relevamiento-pendiente-empezá-por-acá)
9. [Lo que ya se relevó de la API de ML](#9-lo-que-ya-se-relevó-de-la-api-de-ml)
10. [El Centro de Operaciones y la tarjeta](#10-el-centro-de-operaciones-y-la-tarjeta-de-full)
11. [Entregables, en orden](#11-entregables-en-orden)
12. [Decisiones abiertas](#12-decisiones-abiertas)
13. [Qué hay en la carpeta hoy](#13-qué-hay-en-la-carpeta-hoy)
14. [Cómo arrancar](#14-cómo-arrancar-la-sesión-nueva)

---

## 1. Lo primero que tenés que saber

**No existe nada de esto hoy.** No hay script, no hay tablas, no hay
documentación. La reposición a Full **se hace a ojo**. El objetivo es
automatizarla y dejarla integrada con el resto de los módulos de Bertok.

**La regla de Full estaba mal escrita y hay que corregirla.** Dos cosas
distintas se confundían en una sola frase:

| | |
|---|---|
| **Fulfillment de pedidos** | Bertok **nunca** arma ni despacha un pedido Full. Por eso el Sistema de Picking los filtra. **Vigente, sin cambios.** |
| **Reposición de inventario a Full** | **Sí existe.** Cada ~15 días, un envío único de 200 a 300 paquetes de SKU repetidos, con flete que cobra ML. De ahí en adelante ML almacena y entrega. **Es de esto que se trata el trabajo.** |

> El `CLAUDE.md` **raíz** todavía dice «nunca Full» sin esa distinción.
> **Corregirlo es parte del trabajo** — pero es un archivo ajeno: pedir OK antes.

**No se programa hasta terminar el relevamiento.** Instrucción explícita de
Gerardo. Ver §8.

---

## 2. El brief original, textual

Lo que pidió Gerardo, sin interpretar. Es la fuente de verdad del alcance.

> Necesito desarrollar desde cero la REPOSICIÓN A FULL de Mercado Libre.
> Hoy no existe: no hay script, no hay tablas, no hay documentación. Se hace
> a ojo. El objetivo es automatizarlo y dejarlo integrado con el resto de
> los módulos de Bertok.
>
> **Datos duros del proceso:**
> - Cadencia: ~15 días (es una estimación mía, hay que optimizarla)
> - Volumen: 200-300 paquetes por envío
> - Ejecuta Facundo, revisa Antonella (rotativo Facundo↔Federico por ciclo)
> - El pedido se arma mínimo 4 días antes; se puede programar hasta un mes
> - Las etiquetas de bulto y de producto salen de la plataforma de ML
> - La fecha de recolección la define ML al generar el envío
> - LA FECHA DE RECOLECCIÓN NO PUEDE CAER SÁBADO NI FERIADO: genera
>   horas extras. El sistema tiene que advertirlo al elegir la fecha.
>
> **PRIMERO RELEVAR, DESPUÉS PROGRAMAR.** NO escribas código hasta responderme
> esto, mirando los datos reales. [las 6 preguntas de §8]
>
> **CÓMO SE INTEGRA:** Este módulo SÍ escribe en ML.db — no es el Centro de
> Operaciones, que es de sólo lectura. Pero respeta las reglas de ML.db.
>
> **LA SALIDA TIENE QUE SER UNA TABLA ESTABLE EN ML.db**, no un Excel ni un
> print, porque el Centro de Operaciones la va a leer para su tarjeta de
> Reposición a Full. **El contrato de esa tabla es lo más importante que
> vas a definir**: pensala para que otro módulo la consuma.

---

## 3. Contexto de la operación

Bertok vende **siliconas, adhesivos, espumas de poliuretano y discos
abrasivos**, importados de China. Dos canales: Mercado Libre y venta local B2B
con remito y factura.

> **Ojo:** el `CLAUDE.md` de Cortex (el asistente de WhatsApp) dice que Bertok
> vende «tintas, sustratos e insumos gráficos». **Está mal y alimenta los
> prompts de un agente que responde a leads B2B reales.** Es independiente de
> este proyecto y es más urgente que él. Vale avisarle a Gerardo.

### El proceso de reposición

| Dato | Valor |
|---|---|
| Cadencia | ~15 días — **es estimación, hay que medirla** |
| Volumen | 200 a 300 paquetes por envío |
| Ejecuta | Facundo ↔ Federico, rotativo por ciclo |
| Revisa | Antonella |
| Antelación mínima | El pedido se arma **mínimo 4 días antes** |
| Antelación máxima | Se puede programar hasta un mes antes |
| Etiquetas | De bulto y de producto, salen de la plataforma de ML |
| Fecha de recolección | La define ML al generar el envío |

### Los cuatro hitos

```
1 · DECIDIR      qué SKU y cuánto              T−7 o antes
2 · GENERAR      envío en ML, etiquetas,       T−4 mínimo
                 fijar recolección
3 · ARMAR        escaneo, bultos, etiquetado   en Picking
4 · RECOLECCIÓN  ML retira                     cierra con el acuse del inbound
```

Es **una tarjeta con cuatro hitos, no cuatro tarjetas**: es un solo proceso y
partirlo genera cuatro cosas que nadie mira enteras. Pero **cada hito tiene su
propio vencimiento y su propio rojo**.

**La fecha de recolección no puede caer sábado ni feriado.** Genera horas
extras. Se define en el hito 2 y el sistema tiene que advertirlo **al momento de
elegir la fecha, no después**.

---

## 4. El modelo económico: el corazón del problema

Cuánto enviar es un problema clásico de **reposición con revisión periódica
(modelo R,S)**: el nivel objetivo se elige donde el costo de quedarse corto
iguala al costo de pasarse. **Hay que ponerle número a los dos lados.**

### Costo de quedarse corto
Margen perdido + daño de posicionamiento en ML por quedarse sin stock.
→ Margen por SKU sale de `bertok_bi_*` y de la lista de precios.

### Costo de pasarse — dos componentes, y el segundo duele
- **(a)** ML cobra almacenamiento **por unidad y por día**, desde que entra
  hasta que se vende o se retira. → cargo `WAREHOUSING`
- **(b)** Si un SKU no rota, **ML termina descartándolo**: se pierde la
  mercadería entera, no sólo el almacenaje acumulado. → cargo `AGING` como
  señal temprana, operación `withdrawal_discarded` como hecho consumado.

### Costo oculto — el que más se pasa por alto
**NO HAY RESERVA DE STOCK.** Lo que va a Full deja de estar disponible para Flex
y para el local. Mandar de más desabastece los otros dos canales.

> **Por eso el cálculo NO puede ser «cubrir 15 días de demanda de Full».**
> Tiene que ser un **REPARTO ENTRE CANALES que reconozca que el stock es uno solo.**

Mandar de más a Full tiene **triple castigo**: pagás almacenaje, arriesgás que
ML tire la mercadería, y desabastecés Flex y el local.

### La sugerencia de ML: mostrarla, no obedecerla

ML calcula su propia sugerencia de cantidades en la misma ventana. La salida
tiene que mostrar **las dos lado a lado con el desvío**, y pedir decisión humana
cuando se separan más de un umbral.

**ML optimiza para ML:** más stock en Full es más ingreso por almacenamiento
para ellos, y su sugerencia no sabe nada de las ventas por Flex, ni por el
local, ni del costo de mercadería.

Con el tiempo, la comparación dice **cuánto se le puede creer a ML por categoría**.

> **RESTRICCIÓN DESCUBIERTA EN EL RELEVAMIENTO:** la sugerencia **no está
> expuesta en la API** para vendedores locales. Ver §9.5.

---

## 5. Reglas duras de Bertok

**No se negocian y no se reinterpretan.**

- **COT (cotización) SIEMPRE cuenta como venta.**
- **NUNCA medir demanda en meses con quiebre de stock** (disponibilidad < 70%).
  Vender 0 por falta de mercadería es demanda reprimida, no falta de demanda.
  **Un SKU pasó de 18 a 3.536 u/mes al corregir esto.**
- **Estimador central: MEDIANA, no media.** Los meses posteriores a la llegada
  de un container inflan el promedio **hasta un 69%**.
- **Toda base de cálculo es SIN IVA.**
- **Comisiones y cargo fijo de ML son ALL-IN: ya incluyen IVA. Nunca
  multiplicar por 1,21.** Aplica también a los cargos de Full.
- **Ningún parámetro de ML se escribe a mano:** se mide contra la API o la
  factura real.
- **Este módulo NO decide precios.** Si necesita un precio o un costo, se lo
  pide al motor de precios (`03 - Lista precios`).
- **Todo en español**, incluida la terminología técnica.
- **Sin dependencias nuevas sin OK de Gerardo.** Hoy: sólo biblioteca estándar.

---

## 6. Reglas de ML.db

Este módulo **SÍ escribe** en `ML.db` — no es el Centro de Operaciones, que es
de sólo lectura. Pero respeta sus reglas.

### Un dueño por tabla
Declarar explícitamente qué tablas son de este módulo y **no tocar las de nadie
más**. El prefijo definitivo **sale del relevamiento** (§8, pregunta 6). **No se
inventa una convención nueva: se sigue la que ya existe.**

### Las tablas de hechos se acumulan, NUNCA se reemplazan en bloque
> Reconstruir con `DELETE` + recarga ya hizo perder **505 filas de facturación
> real, en silencio**. No repetirlo.

Toda ingesta es incremental e idempotente: se insertan las filas nuevas y se
actualizan las existentes por clave. **Nunca se vacía una tabla de hechos.**

### La ingesta se integra al pipeline
Va dentro de `actualizar_ml.py` / el `.bat` unificador. **No como un script
suelto que alguien tiene que acordarse de correr.** Modificar cualquiera de los
dos **requiere OK previo**.

### Corta con error si algún dato quedó viejo
Un cálculo sobre datos vencidos es peor que no calcular. Tolerancia de frescura
para `ML.db`: **1 hora**.

### No duplicar cálculos
**Si un valor ya lo calcula otro módulo, se CONSUME.** Demanda, rotación, margen
por SKU y costos ya están calculados y validados contra la facturación real.
**No los rehagas.**

---

## 7. Stop conditions

**Pedir OK a Gerardo antes de:**

- Tocar tablas de `ML.db` que no sean de este módulo
- Modificar `actualizar_ml.py` o el `.bat`
- Instalar dependencias
- Cambiar cualquier parámetro de negocio
- Borrar archivos
- Escribir en módulos ajenos — **incluido el `CLAUDE.md` raíz**

---

## 8. El relevamiento pendiente: EMPEZÁ POR ACÁ

**Instrucción explícita: no escribir código hasta responder esto, mirando los
datos reales.** Ninguna de estas preguntas se contesta de memoria ni por
estimación.

### Las seis preguntas sobre ML.db

1. **¿Qué tablas tiene `ML.db` hoy?** Esquema completo, y cuáles se relacionan
   con Full.
2. **¿`ML.db` ya trae STOCK EN FULL?** ¿Y los ENVÍOS DE REPOSICIÓN (inbounds)
   con su estado? ¿Y la SUGERENCIA DE CANTIDADES de ML?
3. **En la tabla de cargos reales (~7.051 filas), ¿están identificados los
   CARGOS DE ALMACENAMIENTO de Full?** ¿Con qué nombre o código? **De eso
   depende poder calcular el costo de pasarse.**
4. **¿Hay registro histórico de los envíos de reposición ya hechos?** Si no,
   ¿se puede reconstruir desde los cargos de flete?
5. **¿Qué produce hoy `bertok_bi_*` que sirva acá?** Hace falta demanda por SKU
   **Y POR CANAL**, rotación, y clasificación de SKU.
6. **¿Cómo está estructurado `actualizar_ml.py` y cuál es la convención de
   nombres de tablas en `ML.db`?** Hay que seguirla, no inventar una nueva.

**El script que las responde ya está escrito** y es de solo lectura estricta
(`mode=ro`: SQLite rechaza cualquier escritura a nivel motor):

```
python relevamiento_ml_db.py "ruta\a\ML.db"
```

Corrélo desde la raíz del sistema Bertok para que también releve el árbol de
scripts. Genera `relevamiento_ml_db.txt`.

### La sonda de la API

```
set ML_ACCESS_TOKEN=APP_USR-...
python sonda_api_full.py
```

Verifica los ocho puntos del catálogo contra la API real. Solo hace GET y
enmascara el token en el informe. **Los dos puntos decisivos:**

- **Qué `charge_type` aparecen de verdad** en los últimos 12 períodos, con importe.
- **Desde qué antigüedad se dispara `AGING`.**

Sin esos dos, el costo de pasarse queda estimado — que es exactamente lo que
este trabajo viene a corregir.

---

## 9. Lo que ya se relevó de la API de ML

Detalle completo en `docs/catalogo-datos-full.md`. Resumen operativo:

> **Limitación de método, declarada:** el relevamiento se armó desde la
> documentación oficial indexada, porque el portal de developers de ML estaba
> bloqueado por la política de red de la sesión anterior. **Por eso existe la
> sonda: nada se codifica sin que la API real lo confirme.** Desde una sesión
> local esto se puede verificar directo.

### 9.1 Stock en Full

```
GET /items/$ITEM_ID                                → inventory_id
GET /inventories/$INVENTORY_ID/stock/fulfillment
```

Campos: `available_quantity`, `not_available_quantity`, `total`, y
`not_available_detail` con el desglose:

| Motivo | Qué significa |
|---|---|
| `damaged` | Dañados (por seller, ML o transportista) — **es plata perdida** |
| `lost` | Perdidos y no encontrados — **reclamable a ML** |
| `withdrawal` | Reservados para un retiro |
| `internal_process` | Retenidos por control de calidad |
| `transfer` | Reservados para mover entre depósitos |
| `noFiscalCoverage` | Solo Brasil, no aplica a MLA |

> **Un SKU con poco disponible y `damaged` alto no necesita reposición:
> necesita un reclamo.** Hoy nadie mira ese campo.

**La clave de todo Full no es el MLA ni el SKU: es el `inventory_id`** (ej.
`LCQI05831`). **Un ítem con variaciones tiene un `inventory_id` por variación** —
para Bertok esto casi seguro aplica. El mapeo `SKU ↔ inventory_id` es una tabla
propia del módulo y hay que mantenerla: es la juntura contra `bertok_bi_*`.

### 9.2 El libro mayor de movimientos

```
GET /stock/fulfillment/operations/search?seller_id=$SELLER_ID
```

**Trampa:** si no pasás `date_from`, **te da solo 15 días**. Pasarlo siempre.

Parámetros: `seller_id`, `inventory_id`, `date_from`, `date_to`, `type`,
`external_references.shipment_id`.
Respuesta: `paging` (con `total` y `scroll`) y `results[]` con `id`, `seller_id`,
`inventory_id`, `date_created`, `type`, `detail`, `result`, `external_references[]`.

**Los quince tipos de operación:**

| Grupo | Tipos |
|---|---|
| Entrada | `inbound_reception` — **el acuse del envío de reposición** |
| Venta | `sale_confirmation`, `sale_cancelation`, `sale_delivery_cancelation`, `sale_return` |
| Retiro | `withdrawal_reservation`, `withdrawal_cancelation`, `withdrawal_delivery`, `withdrawal_removal`, `withdrawal_discarded` |
| Interno | `transfer_reservation`, `transfer_ajustment`, `transfer_delivery`, `quarantine_reservation` |
| Brasil | `fiscal_coverage_ajustment` |

### 9.3 Reparto entre canales — sostiene el costo oculto

```
GET /user-products/$USER_PRODUCT_ID/stock
```

Devuelve `locations[]` con `type` y `quantity`:

- `meli_facility` → **Full**
- `selling_address` → **Flex y venta local**

Se modifican por separado. **Es el stock único repartido en dos lugares, en el
dato.** Confirmado para MLA.

Y para separar la demanda: cada orden trae `shipping.logistic_type` →
`fulfillment` (Full), `self_service` (Flex), `cross_docking`/`xd_drop_off`/
`drop_off` (colecta).

### 9.4 Los cargos reales — el costo de pasarse en pesos

Hay endpoint **específico de Full**, y **está disponible en MLA**:

```
GET /billing/monthly/periods?group=ML                                → últimos 12 períodos
GET /billing/integration/periods/key/$KEY/group/ML/full/details      → el detalle
GET /billing/integration/group/ML/order/details?order_ids=$ORDER_ID  → por orden
```

`$KEY` es el primer día del mes (ej. `2026-09-01`).

**Los `charge_type` de Full:**

| `charge_type` | Qué es | Rol en el modelo |
|---|---|---|
| `WAREHOUSING` | Almacenamiento, por unidad y por día | **Costo de pasarse (a)** |
| `AGING` | Almacenamiento prolongado — el stock viejo | **Señal temprana del descarte** |
| `INBOUND_COLLECT` | Servicio de recolección — el flete de la reposición | **Reconstruye el histórico** |
| `INBOUND_PENALTY` | Incumplimiento en el ingreso | Penalidad |
| `WITHDRAWAL` | Retiro de stock | Costo de sacar mercadería |
| `OVERAGE` | Exceso | A verificar |
| `SPACE_PURCHASE` / `SPACE_CANCELLATION` | Compra/cancelación de espacio | A verificar |

Campos ya identificados: `charge_amount_without_discount`, `discount_amount`.
**Todo all-in: ya incluye IVA. Nunca multiplicar por 1,21.**

### 9.5 Los tres hallazgos derivados

1. **El histórico de envíos se reconstruye, por dos vías que se validan entre
   sí.** `INBOUND_COLLECT` es el flete de cada reposición, con fecha e importe.
   Del otro lado, cada envío dejó su grupo de `inbound_reception`. **De ahí sale
   la cadencia real**, no la estimación de 15 días. → responde la pregunta 4.

2. **La antigüedad del stock es calculable hoy**, sin esperar el cargo. FIFO de
   `inbound_reception` contra `sale_confirmation` por `inventory_id` da cuántos
   días lleva cada unidad en el depósito. **Convierte el descarte de sorpresa en
   aviso anticipado.**

3. **El descarte se mide.** `withdrawal_discarded` + `withdrawal_removal`
   × costo de mercadería de `bertok_bi_*` = el costo de pasarse en su forma más cara.

### 9.6 Los dos huecos

**La sugerencia de cantidades de ML NO está en la API pública** para vendedores
locales. Vive en el Seller Center. `/marketplace/fbm/replenishment-orders`
existe pero es **Global Selling / Fully Managed, para vendedores extranjeros:
no aplica a Bertok**. Lo mismo `POST /marketplace/fbm/inbounds`.

Tres caminos, en orden de preferencia:
1. **Carga manual, una vez por ciclo.** Son ~15 días entre envíos y el pedido ya
   se arma a mano: el costo marginal son minutos. **Es la recomendación.**
2. **Descarga del XLSX del Seller Center**, si la sugerencia aparece ahí. La
   sonda lo chequea.
3. **Scraping. Descartado** salvo que 1 y 2 fallen: es la fuente más frágil que
   tiene Bertok hoy (Contabilium) y no se le suma otra.

**Crear el inbound por API tampoco existe** para vendedor local. **No es un
problema:** ya estaba decidido que el módulo produce la lista, una persona la
carga en ML, y el hito 3 **cierra por detección** contra `picking.db`.

### 9.7 Webhooks y límites

| Tópico | Qué avisa |
|---|---|
| `fbm_stock_operations` | Operaciones sobre el stock en Full. Disponible en Argentina. |
| `items` | Alta, cambio o baja de publicaciones |
| `orders_v2` | Ventas confirmadas y modificaciones |

Encaja con la arquitectura ya decidida: **ML → webhook → n8n → ML.db → el módulo lee.**

**Rate limit: 1.500 requests por minuto por vendedor.** Excederlo devuelve 429
con cuerpo vacío. Mirar la cabecera `RateLimit-Remaining`.
Auth: OAuth 2.0, Authorization Code.

### 9.8 Reportes descargables

El reporte de Fulfillment **solo sale en XLSX**. Tres pasos:

```
POST /billing/integration/periods/key/$KEY/reports    → FILE_ID
GET  /billing/integration/reports/$FILE_ID/status     → esperar "Ready"
GET  /billing/integration/reports/$FILE_ID            → descarga
```

Sirve como control cruzado, no como fuente primaria. Vale bajar uno la primera
vez para conciliar y confirmar que el diccionario de `charge_type` está completo.

---

## 10. El Centro de Operaciones y la tarjeta de Full

Existe un **Master Plan del Centro de Operaciones** (versión 5, 05/09/2026), un
sistema de detección y seguimiento de pendientes sobre 13 procesos de Bertok.
**Este módulo produce los datos que su tarjeta de Reposición a Full (punto 22)
va a leer.** El Centro define **qué** se muestra; este trabajo produce **con qué**.

Artifact: `https://claude.ai/code/artifact/03dc1c35-756b-44d4-bbcf-59d794b480b5`

### Lo que hay que saber del Centro para diseñar bien la salida

**El Centro sólo lee de los sistemas ajenos. Lo único que escribe es su propia
base (`ops.db`).** Sin excepciones. Se evaluó una —que el Centro creara el
pedido de reposición dentro de Picking— y **se descartó**.

**La clave natural.** Cada hallazgo del Centro lleva una clave estable derivada
del hecho real, no de la corrida. Para Full: `full:ciclo:2026-09-16:armar`.
Si ya existía es el mismo problema y **conserva su fecha de nacimiento** y con
ella su antigüedad; si desapareció, se resolvió solo. **Sin clave natural no hay
antigüedad, y sin antigüedad no hay prioridad creciente, ni escalado, ni
auditoría.**

**Cómo cierra el hito 3 sin escribir en ningún lado.** El Centro produce la
lista, una persona la carga en Picking, y el Centro cierra el hito **por
detección**: ve el pedido terminado en `picking.db` y lo da por cumplido.

**Cada dato lleva su `datos_al`.** No se muestra un número sin decir de cuándo
es. Un detector que falla no deja la tarjeta en verde: la deja en **gris «sin
datos»**. Verde significa «miré y está bien».

**La maqueta de la tarjeta, tal como está especificada:**

```
FULL · CICLO 16/09 · DECIDIR
SKU-0142   ML sugiere 120  ·  Bertok 84  ·  −30%
SKU-0207   ML sugiere 40   ·  Bertok 44  ·  +10%
3 SKU con desvío > 25% — requieren decisión
```

**El calendario de feriados** está especificado en `bertok_ops_calendario`,
dentro de `ops.db` — **una base que todavía no existe**. Ver decisión abierta 1.

**Detector de Full: corre 1 vez por día, a la mañana.** Horizonte de días.

---

## 11. Entregables, en orden

Pedidos por Gerardo, en este orden exacto:

| # | Entregable | Estado |
|---|---|---|
| 1 | El relevamiento, con los datos a la vista | **PENDIENTE — bloquea todo** |
| 2 | Propuesta de dónde vive el módulo | ✅ Cerrado: `02 - Mercadolibre\- Full` |
| 3 | `CLAUDE.md` y `BITACORA.md`, **antes de la primera línea de código** | ✅ Hecho |
| 4 | La ingesta de datos de Full a `ML.db` | Pendiente |
| 5 | El motor de cálculo, **con los tres costos en número** | Pendiente |
| 6 | La salida: tabla estable + el contrato para el Centro | Pendiente |

### El contrato de la tabla de salida

Es **lo más importante que define este módulo**. Una tabla estable en `ML.db`,
no un Excel ni un `print`. Requisitos ya conocidos:

- **Clave natural estable:** `full:ciclo:AAAA-MM-DD:<hito>`
- **Cada fila lleva su `datos_al`**
- **Idempotente:** correr la ingesta dos veces deja el mismo resultado
- Tiene que sostener los cuatro hitos con vencimiento propio, la comparación
  ML vs Bertok con el desvío, y los tres costos en pesos

**El esquema se define DESPUÉS del relevamiento**, cuando se conozcan la
convención de nombres y qué datos existen de verdad.

---

## 12. Decisiones abiertas

| # | Decisión | Qué bloquea |
|---|---|---|
| 1 | **El calendario de feriados:** ¿lo trae este módulo o se espera a `ops.db`? La advertencia de sábado/feriado se necesita en el hito 2 y `ops.db` no existe. **Recomendación: que lo traiga este módulo** —son ~20 fechas por año— y el Centro después lo lea. Es alcance nuevo: decide Gerardo. | La advertencia del hito 2 |
| 2 | **Prefijo de tablas del módulo.** Sale del relevamiento, pregunta 6. | El esquema entero |
| 3 | **El umbral de desvío** que dispara decisión humana frente a la sugerencia de ML. **No se elige: se mide** sobre los ciclos observados. | La tarjeta del Centro |
| 4 | **La sugerencia de ML se carga a mano, una vez por ciclo.** Propuesto, pendiente de confirmación. | Que la tarjeta muestre la comparación |
| 5 | **¿Se versiona el sistema Bertok en git?** Hoy no lo está. Sin eso, el trabajo viaja como archivos sueltos. | La entrega y la trazabilidad |

---

## 13. Qué hay en la carpeta hoy

```
- Full\
    00 - TRASPASO.md            este archivo
    CLAUDE.md                   las reglas del módulo
    BITACORA.md                 registro de decisiones — se agrega arriba
    relevamiento_ml_db.py       releva ML.db, solo lectura (mode=ro)
    sonda_api_full.py           verifica la API de Full, solo GET
    docs\
        catalogo-datos-full.md  el relevamiento completo de la API
```

**Los dos scripts usan solo biblioteca estándar. No instalan nada.**
Los dos fueron probados de punta a punta: `relevamiento_ml_db.py` contra una
base sintética de 7.051 filas de cargos, y `sonda_api_full.py` contra un
simulador de la API.

**No hay código de producción todavía.** Es correcto: el relevamiento va primero.

---

## 14. Cómo arrancar la sesión nueva

```
cd "C:\Users\gcorzo\Ruky S.R.L\Bertok - Documentos\02 - Mercadolibre\- Full"
claude
```

Y el primer mensaje:

> Leé `00 - TRASPASO.md` y `CLAUDE.md`. Retomamos la Reposición a Full.
> Empezá por el relevamiento: corré `relevamiento_ml_db.py` contra `ML.db` y
> contestame las seis preguntas con los datos a la vista. No programes todavía.

### Orden de trabajo sugerido

1. **Correr `relevamiento_ml_db.py`** y contestar las seis preguntas de §8.
2. **Correr `sonda_api_full.py`** y confirmar los `charge_type` reales y el
   umbral de `AGING`.
3. **Cerrar las decisiones abiertas** 1, 2 y 4 con Gerardo.
4. **Diseñar el esquema de tablas** siguiendo la convención relevada, y el
   contrato de la tabla de salida. Presentarlo antes de implementar.
5. **Recién ahí, código:** ingesta primero, motor de cálculo después.

### Tres cosas para no olvidarse nunca

1. **Las tablas de hechos se acumulan. Nunca `DELETE` + recarga.** Ya se
   perdieron 505 filas de facturación real, en silencio.
2. **No recalcular lo que ya calcula `bertok_bi_*`.** Se consume.
3. **Los cargos de ML son all-in. Nunca multiplicar por 1,21.**
