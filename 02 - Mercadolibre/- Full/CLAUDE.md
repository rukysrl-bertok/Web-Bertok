# Reposición a Full — CLAUDE.md

Módulo que decide **qué SKU mandar a Full y cuántas unidades**, con los tres
costos en número, y publica esa decisión en una tabla estable que el Centro de
Operaciones lee.

- **Ubicación:** `C:\Users\gcorzo\Ruky S.R.L\Bertok - Documentos\02 - Mercadolibre\- Full`
- **Base:** `ML.db`
- **Estado:** relevamiento en curso. **Sin código de producción todavía.**
- **Creado:** 08/09/2026

---

## 1. La regla de Full, partida en dos

Esto se confundía en una sola frase y es la corrección que habilita todo el módulo.

| | |
|---|---|
| **Fulfillment de pedidos** | Bertok **nunca** arma ni despacha un pedido Full. Por eso el Sistema de Picking los filtra. **Vigente, sin cambios.** |
| **Reposición de inventario a Full** | **Sí existe.** Cada ~15 días, un envío único de 200 a 300 paquetes de SKU repetidos, con flete que cobra ML. De ahí en adelante ML almacena y entrega. **Es de lo que se ocupa este módulo.** |

> El `CLAUDE.md` raíz todavía dice «nunca Full» sin esta distinción.
> **Corregirlo es parte del trabajo**, y requiere OK previo porque es un archivo ajeno.

---

## 2. Qué es y qué no es este módulo

**Es** el que produce la decisión de reposición: la lista de SKU con cantidades,
los tres costos calculados, y la comparación contra la sugerencia de ML.

**No es:**

- **No decide precios.** Si necesita un precio o un costo, se lo pide al motor de
  precios (`03 - Lista precios`). Sin excepción.
- **No recalcula demanda, rotación, margen ni costos.** Eso ya está calculado y
  validado contra facturación real en `bertok_bi_*`. Se consume, no se rehace.
- **No es el Centro de Operaciones.** El Centro es de sólo lectura; este módulo
  sí escribe en `ML.db`, pero únicamente en sus propias tablas.
- **No crea el envío en Mercado Libre.** No existe API para eso en vendedor local,
  y aunque existiera, la decisión ya tomada es que una persona lo carga en el
  Seller Center. El módulo produce la lista; el cierre es por detección.

---

## 3. El proceso real que se está automatizando

| Dato | Valor |
|---|---|
| Cadencia | ~15 días — **es una estimación; hay que medirla** (ver §7) |
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

Es **una tarjeta con cuatro hitos, no cuatro tarjetas**. Cada hito tiene su
propio vencimiento y su propio rojo.

### La fecha de recolección no puede caer sábado ni feriado

Genera horas extras. **El sistema tiene que advertirlo al elegir la fecha, no
después.** Se define en el hito 2.

Tensión pendiente de resolver: el calendario de feriados está especificado en
`bertok_ops_calendario`, que vive en `ops.db` — una base que todavía no existe.
Ver §9, decisión abierta 1.

---

## 4. El modelo económico — es el corazón

Problema clásico de **reposición con revisión periódica (modelo R,S)**: el nivel
objetivo se elige donde el costo de quedarse corto iguala al costo de pasarse.
Hay que ponerle número a los dos lados.

### Costo de quedarse corto
Margen perdido + daño de posicionamiento en ML por quedarse sin stock.

### Costo de pasarse — dos componentes, y el segundo duele
- **(a)** ML cobra almacenamiento **por unidad y por día**, desde que entra hasta
  que se vende o se retira. → cargo `WAREHOUSING`
- **(b)** Si un SKU no rota, **ML termina descartándolo**: se pierde la mercadería
  entera, no sólo el almacenaje acumulado. → cargo `AGING` como señal temprana,
  operación `withdrawal_discarded` como el hecho consumado.

### Costo oculto — el que más se pasa por alto
**No hay reserva de stock.** Lo que va a Full deja de estar disponible para Flex
y para el local. Mandar de más desabastece los otros dos canales.

> Por eso el cálculo **no puede ser «cubrir 15 días de demanda de Full»**.
> Tiene que ser un **reparto entre canales que reconozca que el stock es uno solo.**

Mandar de más a Full tiene triple castigo: pagás almacenaje, arriesgás que ML
tire la mercadería, y desabastecés Flex y el local.

### La sugerencia de ML: mostrarla, no obedecerla

ML calcula su propia sugerencia en la misma ventana. La salida muestra **las dos
lado a lado con el desvío**, y pide decisión humana cuando se separan más de un
umbral.

**ML optimiza para ML.** Más stock en Full es más ingreso por almacenamiento para
ellos, y su sugerencia no sabe nada de las ventas por Flex, ni por el local, ni
del costo de mercadería.

**Restricción descubierta en el relevamiento:** la sugerencia **no está expuesta
en la API** para vendedores locales. Se carga a mano una vez por ciclo, con su
fecha. Ver `docs/catalogo-datos-full.md` §8.1.

---

## 5. Reglas duras de Bertok — no se negocian

- **COT (cotización) SIEMPRE cuenta como venta.**
- **Nunca medir demanda en meses con quiebre de stock** (disponibilidad < 70%).
  Vender 0 por falta de mercadería es demanda reprimida, no falta de demanda.
  Un SKU pasó de 18 a 3.536 u/mes al corregir esto.
- **Estimador central: MEDIANA, no media.** Los meses posteriores a la llegada de
  un container inflan el promedio hasta un 69%.
- **Toda base de cálculo es SIN IVA.**
- **Comisiones y cargo fijo de ML son ALL-IN: ya incluyen IVA. Nunca multiplicar
  por 1,21.** Aplica también a los cargos de Full (`WAREHOUSING`, `AGING`,
  `INBOUND_COLLECT`).
- **Ningún parámetro de ML se escribe a mano:** se mide contra la API o la
  factura real.
- **Todo en español**, incluida la terminología técnica.
- **Sin dependencias nuevas sin OK de Gerardo.** Hoy: sólo biblioteca estándar.

---

## 6. Reglas de ML.db

### Un dueño por tabla
Este módulo declara explícitamente qué tablas son suyas y **no toca las de nadie
más**. El prefijo definitivo queda **PENDIENTE** hasta ver la convención real de
`ML.db` (§7, pregunta 6). No se inventa una convención nueva.

### Las tablas de hechos se acumulan, NUNCA se reemplazan en bloque
Reconstruir con `DELETE` + recarga ya hizo perder **505 filas de facturación
real, en silencio**. No se repite. Toda ingesta es incremental e idempotente:
se insertan las filas nuevas y se actualizan las existentes por clave, nunca se
vacía una tabla de hechos.

### La ingesta se integra al pipeline
Va dentro de `actualizar_ml.py` / el `.bat` unificador. **No como un script suelto
que alguien tiene que acordarse de correr.** Modificar cualquiera de los dos
requiere OK previo.

### Corta con error si algún dato quedó viejo
Un cálculo sobre datos vencidos es peor que no calcular. Frescura tolerada para
`ML.db`: 1 hora.

### No duplicar cálculos
Si un valor ya lo calcula otro módulo, **se consume**. Demanda, rotación, margen
por SKU y costos ya están calculados y validados contra la facturación real.

---

## 7. Lo que falta saber antes de escribir código

Dos relevamientos, los dos con su script listo en esta carpeta. **Ninguno se
responde de memoria ni por estimación.**

### `relevamiento_ml_db.py` — sobre ML.db (solo lectura, `mode=ro`)
1. ¿Qué tablas tiene `ML.db` hoy y cuáles se relacionan con Full?
2. ¿Ya trae stock en Full, envíos de reposición con su estado, y la sugerencia de ML?
3. En los ~7.051 cargos reales, ¿están identificados los de almacenamiento de Full?
4. ¿Hay histórico de envíos de reposición? Si no, ¿se reconstruye desde el flete?
5. ¿Qué produce `bertok_bi_*` que sirva? Demanda por SKU **y por canal**, rotación, ABC.
6. ¿Cómo está estructurado `actualizar_ml.py` y cuál es la convención de nombres?

### `sonda_api_full.py` — sobre la API de ML (solo GET)
Verifica los ocho puntos de `docs/catalogo-datos-full.md`. Los dos decisivos:

- **Qué `charge_type` aparecen de verdad** en los últimos 12 períodos, con importe.
- **Desde qué antigüedad se dispara `AGING`.**

Sin esos dos, el costo de pasarse queda estimado — que es exactamente lo que este
trabajo viene a corregir.

---

## 8. Fuentes de datos

Detalle completo en `docs/catalogo-datos-full.md`.

| Necesito | Sale de |
|---|---|
| Stock en Full y por qué no está disponible | `GET /inventories/$INV/stock/fulfillment` |
| Movimientos: qué entró, se vendió, se descartó | `GET /stock/fulfillment/operations/search` |
| Reparto Full vs Flex/local | `GET /user-products/$ID/stock` → `meli_facility` / `selling_address` |
| Ventas separadas por canal | `orders.shipping.logistic_type` |
| Almacenamiento, stock viejo, flete de reposición | `/billing/integration/periods/key/$KEY/group/ML/full/details` |
| Aviso en el momento | webhook `fbm_stock_operations` |
| Demanda, rotación, margen, costo por SKU | `bertok_bi_*` — **se consume, no se recalcula** |
| Precio y costo | Motor de precios (`03 - Lista precios`) — **se pide, no se calcula** |
| Sugerencia de cantidades de ML | **Carga manual por ciclo.** No hay API. |

---

## 9. Decisiones abiertas

| # | Decisión | Qué bloquea |
|---|---|---|
| 1 | El calendario de feriados: ¿lo trae este módulo, o se espera a `ops.db`? La advertencia de sábado/feriado se necesita en el hito 2, y `ops.db` no existe todavía. Mi voto: que lo traiga este módulo y el Centro después lo lea. | La advertencia del hito 2 |
| 2 | Prefijo de tablas del módulo. Sale del relevamiento, pregunta 6. | El esquema entero |
| 3 | El umbral de desvío que dispara decisión humana en la comparación con ML. Se **mide** sobre los ciclos observados, no se elige. | La tarjeta del Centro |
| 4 | Cómo llega el código a la carpeta de Gerardo: hoy viaja como archivos sueltos desde un repo remoto. | La entrega de todo lo que sigue |

---

## 10. Stop conditions — pedir OK antes de

- Tocar tablas de `ML.db` que no sean de este módulo
- Modificar `actualizar_ml.py` o el `.bat`
- Instalar dependencias
- Cambiar cualquier parámetro de negocio
- Borrar archivos
- Escribir en módulos ajenos — incluido el `CLAUDE.md` raíz

---

## 11. La salida: el contrato con el Centro

Lo más importante que define este módulo. **Una tabla estable en `ML.db`** — no un
Excel, no un `print` — porque el Centro de Operaciones la va a leer para su
tarjeta de Reposición a Full.

Requisitos del contrato, ya conocidos por cómo funciona el Centro:

- **Clave natural estable**, derivada del hecho real y no de la corrida:
  `full:ciclo:AAAA-MM-DD:<hito>`. Sin ella no hay antigüedad, y sin antigüedad no
  hay prioridad creciente ni escalado.
- **Cada fila lleva su `datos_al`.** El Centro no muestra un número sin decir de
  cuándo es.
- **Idempotente:** correr la ingesta dos veces deja el mismo resultado.
- Tiene que sostener los cuatro hitos con su vencimiento propio, la comparación
  ML vs Bertok con el desvío, y los tres costos en pesos.

El esquema exacto se define **después** del relevamiento, cuando se conozcan la
convención de nombres y los datos que existen de verdad.
