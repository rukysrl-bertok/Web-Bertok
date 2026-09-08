# Catálogo de datos de Full — qué se puede bajar de la API de Mercado Libre

Relevamiento de la API pública de Mercado Libre para el módulo de Reposición a Full.
Responde una sola pregunta: **de todo lo que hace falta para decidir cuánto mandar a Full,
qué se puede bajar automáticamente y qué no.**

- **Fecha:** 08/09/2026
- **Sitio:** MLA (Argentina)
- **Alcance:** vendedor local con Full activo. No Global Selling / CBT.

---

## 0. Cómo se hizo este relevamiento, y qué confianza tiene cada dato

El portal `developers.mercadolibre.com.ar` y todos sus espejos por país están
bloqueados por la política de egress de la sesión (403 del proxy, en todos los
dominios de Mercado Libre, la API incluida). El relevamiento se armó desde la
documentación oficial indexada, no leyendo las páginas directo.

Consecuencia práctica, y hay que tomarla en serio:

> **Nada de lo que sigue se codifica sin verificarlo antes contra la API real
> con el token de Bertok.** Esto es un mapa de qué buscar, no una especificación
> cerrada. Es la misma regla que ya rige en Bertok: ningún parámetro de ML se
> escribe a mano, se mide contra la API o la factura real.

Cada bloque lleva su marca:

| Marca | Significado |
|---|---|
| **CONFIRMADO** | Aparece en la documentación oficial de ML con nombre de endpoint y campos. |
| **PROBABLE** | Documentado, pero la forma exacta de la respuesta o la disponibilidad en MLA hay que verificarla. |
| **NO EXISTE** | Se buscó y no hay API pública. Requiere otra vía. |

La verificación se hace con la sonda del punto 9, que consulta y no escribe nada.

---

## 1. El mapa completo

Seis bloques de datos. Los primeros cuatro son API; el quinto es descarga de
archivos; el sexto es push.

| # | Bloque | Qué responde del modelo económico | Estado |
|---|---|---|---|
| A | Stock actual en Full | Cuánto hay hoy, y cuánto de eso no se puede vender | CONFIRMADO |
| B | Movimientos de stock | Toda la historia: qué entró, qué se vendió, qué se perdió, qué descartaron | CONFIRMADO |
| C | Ventas y reparto por canal | Demanda de Full vs Flex vs local — el costo oculto | CONFIRMADO |
| D | Cargos reales | Almacenamiento, stock viejo y flete de reposición — el costo de pasarse | CONFIRMADO |
| E | Reportes descargables | El mismo detalle en XLSX, para conciliar | PROBABLE |
| F | Webhooks | Aviso en el momento, sin consultar | CONFIRMADO |
| — | **Sugerencia de reposición de ML** | La comparación ML vs Bertok de la tarjeta | **NO EXISTE** |

---

## 2. Bloque A — Stock actual en Full

**CONFIRMADO.** Disponible en Argentina, Brasil, México, Chile y Colombia.

### A.1 Conseguir el `inventory_id`

La clave de todo Full no es el MLA ni el SKU: es el `inventory_id`, un código
propio de ML por ítem almacenado (ej. `LCQI05831`). Sin él no se consulta nada.

```
GET /items/$ITEM_ID            →  campo inventory_id
```

**Ojo:** un ítem con variaciones tiene **un `inventory_id` distinto por variación**.
Para Bertok, que vende siliconas y discos en presentaciones, esto casi seguro
aplica. El mapeo `SKU ↔ inventory_id` es una tabla propia del módulo y hay que
mantenerla: es la juntura contra todo lo que ya calcula `bertok_bi_*`.

### A.2 El stock

```
GET /inventories/$INVENTORY_ID/stock/fulfillment
```

Campos:

| Campo | Qué es |
|---|---|
| `available_quantity` | Unidades disponibles para la venta |
| `not_available_quantity` | Unidades que están en el depósito pero **no se pueden vender** |
| `total` | Suma de las dos |
| `not_available_detail` | El desglose de por qué no se pueden vender — ver abajo |

`not_available_detail` es el campo que más importa y el que nadie mira:

| Motivo | Qué significa | Por qué importa |
|---|---|---|
| `damaged` | Dañados (por seller, por ML o por el transportista) | Mercadería perdida. Es plata. |
| `lost` | Perdidos y no encontrados | Ídem, y es reclamable a ML. |
| `withdrawal` | Reservados para un retiro | Stock que ya decidiste sacar. |
| `internal_process` | Retenidos por control de calidad del depósito | Temporal. |
| `transfer` | Reservados para mover entre depósitos | Temporal. |
| `noFiscalCoverage` | Sin cobertura fiscal (solo Brasil) | No aplica a MLA. |

> **Esto responde una pregunta que hoy nadie se hace:** cuánto del stock que
> Bertok cree que tiene en Full está en realidad dañado, perdido o retenido.
> Un SKU con `available_quantity` bajo y `damaged` alto no necesita reposición:
> necesita un reclamo.

### A.3 Full y Flex al mismo tiempo — el reparto de canales

**Este es el bloque que sostiene el "costo oculto" del modelo.**

```
GET /user-products/$USER_PRODUCT_ID/stock
```

Devuelve un array `locations`, cada uno con `type` y `quantity`:

| `type` | Es |
|---|---|
| `meli_facility` | Stock en el depósito de ML — **Full** |
| `selling_address` | Stock en el depósito de Bertok — **Flex y venta local** |

Se pueden modificar de forma independiente. Es la prueba, en el dato, de que
el stock es uno solo repartido en dos lugares — exactamente lo que el cálculo
tiene que reconocer. **Confirmado para MLA.**

---

## 3. Bloque B — Movimientos de stock: el libro mayor de Full

**CONFIRMADO.** Es la fuente más rica del relevamiento y la que permite
reconstruir el histórico que hoy no existe.

```
GET /stock/fulfillment/operations/search?seller_id=$SELLER_ID
```

Parámetros:

| Parámetro | Nota |
|---|---|
| `seller_id` | Obligatorio |
| `inventory_id` | Filtra un ítem |
| `date_from` | **Si no se pasa, por defecto son solo 15 días.** Hay que pasarlo siempre. |
| `date_to` | Por defecto, hoy |
| `type` | Tipo de operación |
| `external_references.shipment_id` | Cruza contra el envío al comprador |

Respuesta: `paging` (con `total` y `scroll`) y `results[]`, cada uno con
`id`, `seller_id`, `inventory_id`, `date_created`, `type`, `detail`,
`result` (el estado del stock después de la operación) y `external_references[]`.

### Los tipos de operación, completos

**Entrada de mercadería**

| Tipo | Qué es |
|---|---|
| `inbound_reception` | **Ingreso de stock.** Al terminar, las unidades quedan a la venta. **Este es el acuse del envío de reposición.** |

**Venta**

| Tipo | Qué es |
|---|---|
| `sale_confirmation` | Se reservan unidades por una venta |
| `sale_cancelation` | Se cancela esa reserva |
| `sale_delivery_cancelation` | No se pudo entregar al comprador, vuelve al depósito |
| `sale_return` | Devolución del comprador |

**Retiro de stock**

| Tipo | Qué es |
|---|---|
| `withdrawal_reservation` | Se reservan unidades para un retiro |
| `withdrawal_cancelation` | Se cancela el retiro, total o parcial |
| `withdrawal_delivery` | Bertok retira físicamente las unidades |
| `withdrawal_removal` | **Stock removido por retiro abandonado** |
| `withdrawal_discarded` | **Remoción de stock — el descarte** |

**Interno del depósito**

| Tipo | Qué es |
|---|---|
| `transfer_reservation` | Reserva para transferencia entre depósitos |
| `transfer_ajustment` | Tras inspección: se repone como disponible o dañado |
| `transfer_delivery` | Ingresan las unidades transferidas |
| `quarantine_reservation` | Calidad retiene unidades para inspección |
| `fiscal_coverage_ajustment` | Solo Brasil |

### Lo que este bloque desbloquea

1. **El histórico de envíos de reposición se reconstruye.** Cada envío pasado
   deja su rastro como un grupo de `inbound_reception` con fechas contiguas.
   Agrupando por fecha salen los ciclos reales — la cadencia verdadera, no
   la estimación de 15 días.

2. **La antigüedad del stock (el "stock viejo") es calculable.** ML cobra
   `AGING` cuando ya pasó, pero cruzando `inbound_reception` contra
   `sale_confirmation` por `inventory_id` en orden FIFO sale **cuántos días
   lleva cada unidad en el depósito, hoy**. Eso permite avisar antes de que
   llegue el cargo, no después. Es un cálculo derivado, no un dato que ML
   entregue.

3. **El descarte se mide.** `withdrawal_discarded` y `withdrawal_removal`
   ponen número al peor escenario del modelo: la mercadería que ML tiró.
   Multiplicado por el costo de mercadería que ya tiene `bertok_bi_*`, es
   el costo de pasarse en su forma más cara.

---

## 4. Bloque C — Ventas por canal

**CONFIRMADO.**

La demanda de Full no se mide con las ventas totales: se separa por el tipo de
logística de cada venta.

```
GET /orders/search?seller=$SELLER_ID&...     →  shipping.logistic_type
```

| `logistic_type` | Canal |
|---|---|
| `fulfillment` | **Full** — lo despacha ML desde su depósito |
| `self_service` | **Flex** — lo despacha Bertok el mismo día |
| `cross_docking` / `xd_drop_off` / `drop_off` | Colecta o despacho a sucursal |

Cruzado con la venta local de Contabilium, cierra los tres canales del reparto.

Las reglas duras de Bertok se aplican igual acá y no se negocian: **COT cuenta
como venta**, **no se miden meses con disponibilidad bajo 70%**, y el estimador
central es la **mediana**. Nada de esto se recalcula en este módulo: se consume
de `bertok_bi_*`, que ya lo tiene validado contra facturación real.

---

## 5. Bloque D — Los cargos reales: el costo de pasarse, en pesos

**CONFIRMADO, y es el hallazgo más importante del relevamiento.**

Existe un endpoint de facturación **específico de Full**:

```
GET /billing/integration/periods/key/$KEY/group/ML/full/details
```

Disponible **solo para MLA, MLB, MLM, MCO y MLC**. Argentina está.

El `$KEY` es el primer día del mes del período (ej. `2026-09-01`). Los períodos
se listan con:

```
GET /billing/monthly/periods?group=ML     →  últimos 12 períodos
```

Devuelve `amount`, `unpaid_amount`, `period` (`date_from`/`date_to`), `key`,
`expiration_date` y `period_status`.

### Los tipos de cargo de Full

Este es el diccionario que hoy falta para poder calcular el costo de pasarse:

| `charge_type` | Qué es | Rol en el modelo |
|---|---|---|
| `WAREHOUSING` | **Almacenamiento.** Por unidad y por día. | Costo de pasarse, componente (a) |
| `AGING` | **Almacenamiento prolongado.** El recargo del stock viejo. | Costo de pasarse, la señal temprana del descarte |
| `INBOUND_COLLECT` | **Servicio de recolección.** El flete que ML cobra por el envío de reposición. | **Reconstruye el histórico de envíos** |
| `INBOUND_PENALTY` | Incumplimiento en el ingreso | Penalidad por inbound mal armado |
| `WITHDRAWAL` | Retiro de stock | Costo de sacar mercadería de Full |
| `OVERAGE` | Exceso | A verificar contra factura |
| `SPACE_PURCHASE` | Compra de espacio | A verificar |
| `SPACE_CANCELLATION` | Cancelación de espacio | A verificar |

Campos de la respuesta que ya se identificaron: `charge_amount_without_discount`
y `discount_amount`. **Los importes de facturación de ML son all-in: ya incluyen
IVA. Nunca multiplicarlos por 1,21.**

> **`INBOUND_COLLECT` responde la pregunta 4 del relevamiento.** Cada envío de
> reposición pasado dejó su cargo de recolección con fecha e importe. Cruzado
> contra los `inbound_reception` del bloque B, el histórico se reconstruye por
> dos vías independientes que se validan entre sí.

Hay también un endpoint por orden, útil para atribuir cargos a ventas puntuales:

```
GET /billing/integration/group/ML/order/details?order_ids=$ORDER_ID
```

---

## 6. Bloque E — Reportes descargables

**PROBABLE** — el flujo está documentado; las columnas del XLSX de Fulfillment
hay que verificarlas con una descarga real.

Proceso de tres pasos. **El reporte de Fulfillment solo sale en XLSX** (no CSV):

```
1. POST  /billing/integration/periods/key/$KEY/reports        → genera, devuelve FILE_ID
2. GET   /billing/integration/reports/$FILE_ID/status         → esperar "Ready"
3. GET   /billing/integration/reports/$FILE_ID                → descarga
```

Sirve como control cruzado contra el bloque D, no como fuente primaria: el
detalle por API es más manejable que parsear un XLSX. Vale la pena bajar uno
igual, para conciliar la primera vez y confirmar que el diccionario de
`charge_type` está completo.

---

## 7. Bloque F — Webhooks

**CONFIRMADO.**

| Tópico | Qué avisa |
|---|---|
| `fbm_stock_operations` | **Operaciones sobre el stock en Full.** El recurso que llega es `/stock/fulfillment/operations/...` |
| `items` | Alta, cambio o baja de publicaciones |
| `orders_v2` | Ventas confirmadas y sus modificaciones |

`fbm_stock_operations` está disponible en Argentina.

Encaja exactamente con la arquitectura ya decidida en el Master Plan:
**ML → webhook → n8n → ML.db → el módulo lee.** El acuse del hito 4
(«ML retiró la mercadería») puede llegar solo, sin que nadie consulte nada:
es el `inbound_reception` entrando por webhook.

---

## 8. Lo que NO se puede bajar

Tan importante como lo anterior. Dos huecos, y uno afecta el diseño de la tarjeta.

### 8.1 La sugerencia de reposición de ML — **NO EXISTE en la API pública**

Se buscó con varias formulaciones. La sugerencia de cantidades que muestra la
aplicación de Full **vive en el Seller Center y no está expuesta como endpoint
para vendedores locales**.

Lo único parecido que apareció es `GET /marketplace/fbm/replenishment-orders`,
y **no sirve**: es de Global Selling / CBT, exclusivo del modelo *Fully Managed*
para vendedores extranjeros. Bertok es vendedor local argentino. No aplica.

Esto tiene consecuencia directa sobre la tarjeta del Centro, que está
especificada para mostrar «ML sugiere 120 · Bertok 84 · −30%». **Ese número de
ML no llega solo.** Quedan tres caminos:

1. **Carga manual, una vez por ciclo.** Facundo copia la sugerencia de ML al
   armar el pedido. Son ~15 días entre ciclos y el pedido ya se arma a mano:
   el costo marginal es de minutos. La tarjeta funciona completa.
2. **Descarga del reporte del Seller Center**, si la sugerencia aparece en
   alguno de los XLSX. Hay que mirarlo. Si está, se automatiza.
3. **Scraping del Seller Center.** Es lo que ya pasa con Contabilium y es la
   fuente más frágil que tiene Bertok. **No lo recomiendo** salvo que 1 y 2 fallen.

Mi voto es el 1, con el 2 como mejora si el reporte lo trae. Y decirlo así en
la tarjeta: la sugerencia de ML es un dato cargado, con su fecha, no un dato vivo.

### 8.2 Crear el envío de reposición — **NO EXISTE para vendedor local**

No hay endpoint público para que un vendedor MLA genere un inbound por API.
El envío se crea en el Seller Center, y de ahí salen las etiquetas de bulto y
de producto y la fecha de recolección. (`POST /marketplace/fbm/inbounds` existe,
pero otra vez es CBT / Fully Managed. No aplica.)

**Esto no es un problema: es lo que ya se decidió.** El Master Plan estableció
que el Centro no escribe en sistemas ajenos y que el hito 3 cierra por
detección. El módulo produce la lista de qué mandar y cuánto; una persona la
carga en ML; el sistema confirma por lectura cuando ve el `inbound_reception`.
El circuito cierra sin escribir en ML.

---

## 9. Antes de codificar: la sonda de verificación

Nada de este catálogo entra en el módulo sin comprobarse. La sonda hace una
llamada de cada tipo, con el token real, y reporta qué contestó ML de verdad:

| # | Qué verifica | Por qué es crítico |
|---|---|---|
| 1 | `/items/$ID` trae `inventory_id`, y cuántos por variación | Sin esto no hay juntura SKU ↔ Full |
| 2 | El stock trae `not_available_detail` con los seis motivos | Define si se puede medir mercadería dañada |
| 3 | `operations/search` con `date_from` de 12 meses: cuántas páginas, si el `scroll` funciona | Decide si el histórico es reconstruible |
| 4 | Qué `charge_type` aparecen realmente en los últimos 12 períodos, con importe | **Cierra el costo de pasarse. Es la verificación más importante.** |
| 5 | Si `AGING` figura y desde qué antigüedad se dispara | El umbral real del stock viejo, medido, no supuesto |
| 6 | `/user-products/$ID/stock` devuelve las dos `locations` en MLA | Sostiene todo el reparto entre canales |
| 7 | Si algún XLSX trae la sugerencia de ML | Decide entre carga manual y automática |
| 8 | Rate limit real observado (1.500 req/min por vendedor, cabecera `RateLimit-Remaining`) | Dimensiona la ingesta |

Los puntos 4 y 5 son los que ponen número al costo de pasarse. Sin ellos el
motor de cálculo no se puede escribir: quedaría estimando el lado caro de la
balanza, que es justo lo que este trabajo viene a corregir.

---

## 10. Cómo cae todo esto sobre el modelo económico

| Lado del modelo | Dato que lo alimenta | De dónde sale |
|---|---|---|
| **Costo de quedarse corto** — margen perdido | Margen por SKU | `bertok_bi_*` — ya calculado, se consume |
| **Costo de quedarse corto** — quiebre en Full | `available_quantity = 0` con demanda viva | Bloque A + Bloque C |
| **Costo de pasarse (a)** — almacenamiento | `WAREHOUSING`, en pesos reales | Bloque D |
| **Costo de pasarse (b)** — descarte | `AGING` creciente → `withdrawal_discarded` | Bloque D + Bloque B |
| **Costo oculto** — desabastecer Flex y local | `meli_facility` vs `selling_address` + demanda por canal | Bloque A.3 + Bloque C |
| **Cadencia real del ciclo** | `INBOUND_COLLECT` y `inbound_reception` por fecha | Bloque D + Bloque B |
| **Antigüedad del stock hoy** | FIFO de `inbound_reception` contra `sale_confirmation` | Bloque B, calculado |
| **Sugerencia de ML** | — | **No hay API. Carga manual por ciclo.** |

Todo lo de la columna derecha existe salvo la última fila. El modelo económico
se puede construir con datos medidos, no estimados — que era la duda que
abría este trabajo.

---

## 11. Fuentes

Documentación oficial de Mercado Libre (consultada por índice, no por lectura
directa — ver punto 0):

- Mercado Envíos Full (fulfillment) — developers.mercadolibre.com.ar/es_ar/fulfillment
- Envíos Fulfillment — developers.mercadolibre.com.ar/envios-fulfillment
- Fulfillment stock — global-selling.mercadolibre.com/devsite/fulfillment-stock-gs
- Convivencia Full/Flex (MLA y MLC) — developers.mercadolibre.cl/es_ar/convivencia-full-y-flex
- Reportes de Facturación — developers.mercadolibre.cl/es_ar/reportes-de-facturacion
- Buenas prácticas para el consumo de las APIs de reportes de facturación — developers.mercadolibre.com.ar
- Reportes: descargas — developers.mercadolibre.com.co/es_ar/reportes-descargas
- Productos: recibe notificaciones — developers.mercadolibre.com.ar/es_ar/productos-recibe-notificaciones
- Get Replenishment Orders (CBT — no aplica) — global-selling.mercadolibre.com/devsite/api-docs
