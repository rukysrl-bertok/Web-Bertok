# Reposición a Full — arranque

> **Este archivo se pega tal cual como primer mensaje de una sesión dedicada.**
> Requiere sesión **local** (que vea `ML.db`). Todo lo que sigue es el prompt.

---

Necesito desarrollar desde cero la REPOSICIÓN A FULL de Mercado Libre.
Hoy no existe: no hay script, no hay tablas, no hay documentación. Se hace
a ojo. El objetivo es automatizarlo y dejarlo integrado con el resto de
los módulos de Bertok.

## DÓNDE VA — YA DECIDIDO

El módulo vive en: **`02 - Mercadolibre\Reposición Full\`**

Razón: este módulo escribe en `ML.db`, y el módulo 02 es el dueño de
Mercado Libre. Además ya hay precedente — Hermes y Mercado Ads son
submódulos de 02. No lo vuelvas a discutir.

Y las tablas que escriba son de **DOS CLASES que no se mezclan**:

1. **DATOS CRUDOS DE ML** (stock en Full, envíos de reposición, sugerencia
   de cantidades de ML). Son **ingesta**, le pertenecen a `actualizar_ml.py`,
   y tienen que seguir **la convención de nombres que ya usa `ML.db`**.
   No inventes un prefijo nuevo para esto.

2. **EL CÁLCULO DE REPOSICIÓN** (lista propuesta por SKU, los tres costos,
   el desvío contra la sugerencia de ML, la decisión tomada). Esto es
   **derivado** y lleva prefijo propio: **`bertok_full_*`**

Por qué separarlas: si el cálculo escribe con el mismo nombre que la
ingesta, en seis meses nadie sabe qué vino de ML y qué calculamos
nosotros, y la regla de «un dueño por tabla» se vuelve insostenible.

No va en `bertok_bi_*`: Bertok BI analiza el pasado; esto decide una
operación futura.

## CONTEXTO DE LA OPERACIÓN

Bertok vende siliconas, adhesivos, espumas de poliuretano y discos
abrasivos, importados de China. Dos canales: Mercado Libre y venta local
B2B con remito y factura.

En Mercado Libre hay que distinguir **dos cosas** que se confundían en una
sola regla:

1. **FULFILLMENT DE PEDIDOS:** Bertok **nunca** arma ni despacha un pedido
   Full. Por eso el Sistema de Picking los filtra. Sigue vigente.
2. **REPOSICIÓN DE INVENTARIO A FULL:** sí existe, y es este trabajo.
   Cada ~15 días se manda un envío único de 200 a 300 paquetes de SKU
   repetidos, con flete de Mercado Libre que ML cobra. De ahí en adelante
   ML almacena y entrega.

El `CLAUDE.md` raíz todavía dice «nunca Full» sin esa distinción.
**Corregirlo es parte del trabajo.**

Datos duros:
- Cadencia ~15 días (estimación mía, hay que optimizarla)
- 200-300 paquetes por envío
- Ejecuta Facundo, revisa Antonella (rotativo Facundo↔Federico por ciclo)
- Se arma mínimo 4 días antes; se puede programar hasta un mes
- Las etiquetas de bulto y de producto salen de la plataforma de ML
- **La fecha de recolección no puede caer sábado ni feriado:** genera
  horas extras. El sistema tiene que advertirlo al elegir la fecha.

## LA ECONOMÍA — ES EL CORAZÓN DEL PROBLEMA

Cuánto enviar es **reposición con revisión periódica** (modelo R,S): el
nivel objetivo se elige donde el costo de quedarse corto iguala al de
pasarse. Hay que ponerle número a los dos lados.

**QUEDARSE CORTO:** margen perdido + daño de posicionamiento en ML.

**PASARSE — dos componentes, y el segundo duele:**
- ML cobra almacenamiento **por unidad y por día**, desde que entra hasta
  que se vende o se retira.
- Si un SKU no rota, **ML termina descartándolo**: se pierde la mercadería
  entera, no sólo el almacenaje acumulado.

**COSTO OCULTO — el que más se pasa por alto:**
**No hay reserva de stock.** Lo que va a Full deja de estar disponible para
Flex y para el local. Mandar de más desabastece los otros dos canales.

Por eso el cálculo **no puede ser** «cubrir 15 días de demanda de Full».
Tiene que ser un **reparto entre canales**: el stock es uno solo.

**LA SUGERENCIA DE ML: mostrarla, no obedecerla.**
ML calcula su propia sugerencia en la misma ventana. La salida muestra
**las dos lado a lado con el desvío**, y pide decisión humana cuando se
separan más de un umbral. ML optimiza para ML: más stock en Full es más
ingreso por almacenamiento para ellos, y su sugerencia no sabe nada de
las ventas por Flex ni por el local ni del costo de mercadería.

## PRIMERO RELEVAR, DESPUÉS PROGRAMAR

**No escribas código hasta responderme esto**, mirando los datos reales:

1. ¿Qué tablas tiene `ML.db` hoy? Mostrame el esquema completo, decime
   cuáles se relacionan con Full, y cuál es la convención de nombres.
2. ¿`ML.db` ya trae **stock en Full**? ¿Y los **envíos de reposición**
   (inbounds) con su estado? ¿Y la **sugerencia de cantidades** de ML?
3. En la tabla de cargos reales de ML (~7.051 filas), ¿están identificados
   los **cargos de almacenamiento** de Full? ¿Con qué nombre o código?
   De eso depende poder calcular el costo de pasarse.
4. ¿Hay registro histórico de los envíos de reposición ya hechos? Si no,
   ¿se puede reconstruir desde los cargos de flete?
5. ¿Qué produce hoy `bertok_bi_*` que sirva acá? Necesito demanda por SKU
   **y por canal**, rotación y clasificación de SKU.
6. ¿Cómo está estructurado `actualizar_ml.py` y el `.bat` unificador?

## CÓMO SE INTEGRA

Este módulo **sí** escribe en `ML.db` — no es el Centro de Operaciones,
que es de sólo lectura. Pero respeta las reglas de `ML.db`:

- **Un dueño por tabla.** Declarar qué tablas son de este módulo.
- **Las tablas de hechos se acumulan, nunca se reemplazan en bloque.**
  Reconstruir con DELETE + recarga ya hizo perder 505 filas de facturación
  real, en silencio. No repetirlo.
- La ingesta se integra a `actualizar_ml.py` / al `.bat`, no como un script
  suelto que alguien tiene que acordarse de correr.
- Corta con error si algún dato quedó viejo.

**No duplicar cálculos:** demanda, rotación, margen por SKU y costos ya
están calculados y validados contra la facturación real. Se consumen.

**La salida tiene que ser una tabla estable en `ML.db`**, no un Excel ni un
print, porque el Centro de Operaciones la va a leer para su tarjeta de
Reposición a Full. El contrato de esa tabla es lo más importante que vas
a definir.

## REGLAS DURAS DE BERTOK

- **COT (cotización) siempre cuenta como venta.**
- **Nunca medir demanda en meses con quiebre de stock** (disponibilidad
  <70%): vender 0 por falta de mercadería es demanda reprimida.
  Un SKU pasó de 18 a 3.536 u/mes al corregir esto.
- **Estimador central: mediana, no media.** Los meses posteriores a la
  llegada de un container inflan el promedio hasta un 69%.
- **Toda base de cálculo es sin IVA.**
- **Comisiones y cargo fijo de ML son ALL-IN**, ya incluyen IVA.
  Nunca multiplicar por 1,21.
- Ningún parámetro de ML se escribe a mano: se mide contra la API o la
  factura real.
- **Este módulo no decide precios.** Si necesita un precio o un costo, lo
  pide al motor de precios (`03 - Lista precios`).
- Todo en español, incluida la terminología técnica.
- Sin dependencias nuevas sin mi OK.

## ENTREGABLES, EN ESTE ORDEN

1. El relevamiento, con los datos a la vista.
2. `CLAUDE.md` y `BITACORA.md` del módulo, **antes** de la primera línea
   de código.
3. La ingesta de datos de Full a `ML.db`.
4. El motor de cálculo, con los tres costos en número.
5. La salida: tabla `bertok_full_*` + el contrato para el Centro.

## STOP CONDITIONS — pedime OK antes de

- Tocar tablas de `ML.db` que no sean de este módulo
- Modificar `actualizar_ml.py` o el `.bat`
- Instalar dependencias
- Cambiar cualquier parámetro de negocio
- Borrar archivos

## CONTEXTO ADICIONAL

El Master Plan del Centro de Operaciones especifica la tarjeta de
Reposición a Full como 4 hitos (decidir → generar en ML → armar →
recolección), con el modelo económico y el criterio de la sugerencia de
ML. Punto 22 de:
https://claude.ai/code/artifact/03dc1c35-756b-44d4-bbcf-59d794b480b5

Ese documento define **qué** tiene que mostrar la tarjeta; este trabajo
produce los datos que la tarjeta va a leer.

**Arrancá por el relevamiento. No programes todavía.**
