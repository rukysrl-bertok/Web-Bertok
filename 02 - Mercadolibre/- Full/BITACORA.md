# Reposición a Full — Bitácora

Registro cronológico de decisiones, hallazgos y bloqueos. Se agrega arriba.
Nada se borra: una decisión que se revierte queda, con la razón.

---

## 09/09/2026 — Se fija la ubicación del módulo

**Ruta definitiva:**
`C:\Users\gcorzo\Ruky S.R.L\Bertok - Documentos\02 - Mercadolibre\- Full`

Se propuso `02 - Mercadolibre\Reposición Full\` y Gerardo la ajustó a `- Full`,
siguiendo la convención de ordenamiento que ya usa el resto de las carpetas.

Se escriben `CLAUDE.md` y `BITACORA.md` **antes de la primera línea de código de
producción**, como estaba pedido.

**Pendiente que no avanza sin Gerardo:** el módulo se está desarrollando desde
una sesión remota que no tiene acceso a la PC ni a `ML.db`. El código viaja como
archivos sueltos. Ver decisión abierta 4.

---

## 08/09/2026 — Relevamiento de la API de Full

Se relevó qué datos de Full se pueden bajar. Resultado completo en
`docs/catalogo-datos-full.md`.

**Limitación de método, declarada:** el portal de developers de Mercado Libre y
todos sus espejos están bloqueados por la política de egress de la sesión (403).
El relevamiento se armó desde la documentación oficial indexada, no leyéndola
directo. **Por eso existe `sonda_api_full.py`: nada se codifica sin que la API
real lo confirme.**

### Cuatro hallazgos que desbloquean el modelo económico

1. **El costo de pasarse tiene código propio.** Los `charge_type` de Full son
   `WAREHOUSING`, `AGING`, `INBOUND_COLLECT`, `INBOUND_PENALTY`, `WITHDRAWAL`,
   `OVERAGE`, `SPACE_PURCHASE`, `SPACE_CANCELLATION`. Hay endpoint específico de
   Full y **está disponible en MLA**:
   `/billing/integration/periods/key/$KEY/group/ML/full/details`

2. **El histórico de envíos se reconstruye, por dos vías independientes que se
   validan entre sí.** `INBOUND_COLLECT` es el flete de cada reposición, con
   fecha e importe. Del otro lado, cada envío dejó su grupo de
   `inbound_reception` en las operaciones. De ahí sale la **cadencia real**, no
   la estimación de 15 días.

3. **La antigüedad del stock es calculable hoy**, sin esperar el cargo. FIFO de
   `inbound_reception` contra `sale_confirmation` por `inventory_id` da cuántos
   días lleva cada unidad en el depósito. Convierte el descarte de sorpresa en
   aviso anticipado.

4. **El costo oculto tiene un dato que lo prueba.**
   `GET /user-products/$ID/stock` devuelve `meli_facility` (Full) y
   `selling_address` (Flex y local), modificables por separado. Es el stock único
   repartido en dos lugares, en el dato.

### Dos huecos

- **La sugerencia de cantidades de ML no está en la API pública** para vendedores
  locales. `/marketplace/fbm/replenishment-orders` existe pero es Global Selling /
  *Fully Managed*, para vendedores extranjeros: **no aplica a Bertok.**
  **Decisión propuesta:** carga manual una vez por ciclo, con su fecha. Son ~15
  días entre envíos y el pedido ya se arma a mano. Scraping descartado: es la
  fuente más frágil que tiene Bertok hoy (Contabilium) y no se le suma otra.
  *Pendiente de confirmación de Gerardo.*

- **Crear el inbound por API tampoco existe** para vendedor local. No es un
  problema: ya estaba decidido que el hito 3 cierra por detección contra
  `picking.db`.

### Otro dato del stock que hoy nadie mira

`not_available_detail` desglosa por qué hay unidades que no se pueden vender:
`damaged`, `lost`, `withdrawal`, `internal_process`, `transfer`. Un SKU con poco
disponible y `damaged` alto **no necesita reposición: necesita un reclamo.**

**Entregado:** `docs/catalogo-datos-full.md` y `sonda_api_full.py` (solo GET,
token enmascarado, probada de punta a punta contra un simulador de la API).

---

## 08/09/2026 — Se intenta el relevamiento de ML.db y se bloquea

No se pudo hacer: la sesión remota sólo ve lo que está en GitHub, y ahí hay dos
repositorios — `Web-Bertok` (un README) y `cortex-n8n-workflows` (WhatsApp/Odoo).
El sistema Bertok —`ML.db`, los 44 scripts de BI, `actualizar_ml.py`,
`picking.db`— vive en la PC y no está versionado.

Las seis preguntas del relevamiento son todas «mirando los datos reales».
Inventarlas hubiera sido peor que no contestarlas: el módulo entero se apoya en
ellas.

**Entregado:** `relevamiento_ml_db.py`, de solo lectura estricta (`mode=ro`, así
SQLite rechaza cualquier escritura a nivel motor, no por buena voluntad del
código). Responde las seis preguntas en una corrida. Probado contra una base
sintética de 7.051 filas de cargos: ubicó los conceptos de almacenamiento de Full
con conteo e importe acumulado.

**Se confirmó, leyendo el Master Plan del Centro de Operaciones (punto 25):** las
preguntas 2 y 3 ya figuran ahí en «A verificar (datos, no decisiones)» y nadie
las respondió nunca. No es que se perdió el dato — hace falta abrir `ML.db`.

---

## 08/09/2026 — Punto de partida

Arranca el módulo. Antes de esto: **no había script, ni tablas, ni
documentación. La reposición a Full se hacía a ojo.**

Se corrige la regla que estaba mezclada en una sola frase:

- **Fulfillment de pedidos:** Bertok nunca arma ni despacha un pedido Full.
  Vigente, sin cambios.
- **Reposición de inventario a Full:** sí existe, cada ~15 días, 200 a 300
  paquetes. Es lo que este módulo automatiza.

El `CLAUDE.md` raíz todavía no refleja la distinción. Corregirlo requiere OK
previo: es un archivo ajeno a este módulo.

**Ubicación en el mapa:** este módulo produce los datos que la tarjeta de
Reposición a Full del Centro de Operaciones (punto 22 del Master Plan) va a leer.
El Centro define **qué** se muestra; este trabajo produce **con qué**.
