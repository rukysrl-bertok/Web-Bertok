# BERTOK — Traspaso completo

**Todo lo trabajado entre el 04 y el 09/09/2026 con Claude Code.**
Este documento es autosuficiente: contiene el contexto, las decisiones, las reglas, el estado y los scripts completos. Si el repo no está disponible, todo se puede reconstruir desde acá.

---

## CÓMO USAR ESTE DOCUMENTO

Pegá esto como primer mensaje de una sesión nueva:

> Adjunto el traspaso completo del trabajo hecho hasta ahora. Leelo entero antes de responder. Después decime en qué estado quedó cada cosa y cuál es el primer paso concreto.

Y adjuntá este archivo.

### Antes de nada: la sesión tiene que ser LOCAL

Esto ya hizo perder varios turnos de trabajo. Claude Code puede correr de dos formas y **se ven iguales**:

| | Dónde corre | Qué ve |
|---|---|---|
| **Sesión local** (CLI en la PC) | Tu máquina | Tus carpetas, `ML.db`, los `CLAUDE.md` |
| **Sesión en la nube** (app/web atada a un repo) | Contenedor remoto | Sólo el repo de GitHub clonado |

**Verificación obligatoria al inicio de cada sesión:**

```
Mostrame la carpeta donde estás parado y listame CLAUDE.md y ML.db
```

- Ruta de Windows + los dos archivos → **local, todo bien**
- `/home/user/...` → **es en la nube y no sirve** para este trabajo

### Cómo abrir la sesión local

La app de escritorio, si está configurada contra un repo de GitHub, sólo abre sesiones en la nube. El camino confiable es el CLI:

```powershell
# 1. PowerShell como tu usuario, NO como administrador.
#    Si arranca en C:\Windows\system32 es admin: cerrala y abrila normal.

# 2. Instalar
irm https://claude.ai/install.ps1 | iex

# 3. CERRAR Y REABRIR PowerShell (si no, el comando no se reconoce)

# 4. Arrancar en la carpeta de Bertok
cd "$env:USERPROFILE\Ruky S.R.L\Bertok - Documentos"
claude
```

### Dónde está el resto

- **Repo con todos los archivos:** `github.com/rukysrl-bertok/Web-Bertok`, rama `claude/project-analysis-4iwwdk`, carpeta `_traspaso/`
- **Master Plan completo (26 secciones):** https://claude.ai/code/artifact/03dc1c35-756b-44d4-bbcf-59d794b480b5

Traerlo:

```
git clone https://github.com/rukysrl-bertok/Web-Bertok C:\temp\traspaso
cd C:\temp\traspaso
git checkout claude/project-analysis-4iwwdk
```

Después, mover `_traspaso/` a su lugar:

| Del repo | A OneDrive |
|---|---|
| `_traspaso/17 - Centro de Operaciones/` | `Bertok - Documentos\17 - Centro de Operaciones\` |
| `_traspaso/plans/handoffs/*.md` | `Bertok - Documentos\plans\handoffs\` |
| `_traspaso/Master Plan v5*.html` | `Bertok - Documentos\17 - Centro de Operaciones\` |

Y borrar la rama: `git push origin --delete claude/project-analysis-4iwwdk`

> El número de módulo **17** es una propuesta. Si se cambia, hay rutas que actualizar en `crear_ops_db.py` y `backup_bases.py`.

---

# PARTE 1 · LA EMPRESA Y EL ENTORNO

**Bertok / Ruky S.R.L.** (Argentina). Dueño y decisor final: **Gerardo Corzo**. Socio: **Fernando**.

Vende siliconas, adhesivos, espumas de poliuretano y discos abrasivos, **importados de China**. Catálogo acotado: ~27 SKU base, ~205 filas contando packs y combos.

**Dos canales que no deben canibalizarse:**
- **Mercado Libre** — Flex, Mercado Envíos y **reposición a Full**
- **Local / Offline** — B2B a distribuidores, con remito y factura
- Regla dura: `precio_ML >= precio_lista_local × 1.15`

**Equipo:** Gerardo (dueño) · Antonella (supervisora / compras) · Abril, Facundo y Federico (vendedores) · personal de depósito.

**ERP:** Contabilium. **No tiene API contratada** → los datos se obtienen con scraping controlado (Playwright, sesión persistente que vence cada pocos días).

## El entorno de trabajo — lo más atípico

No hay repositorio tradicional ni CI/CD. **El «sistema» es una carpeta de OneDrive operada con Claude Code.**

```
C:\Users\<perfil>\Ruky S.R.L\Bertok - Documentos\
```

| Aspecto | Cómo es |
|---|---|
| **Versionado** | Git local sobre OneDrive, rama única `main`, commits directos. Sin PRs, sin CI, sin tests formales |
| **Concurrencia** | Varias personas, cada una con su PC, misma cuenta de Claude Code, misma carpeta sincronizada. **Coordinación 100% manual.** Ya se perdieron cambios |
| **Documentación como contrato** | Cada módulo tiene un `CLAUDE.md` (las reglas) y un `BITACORA.md` (el registro de sesiones). Hay 16 y 13 respectivamente |
| **Identificación de operador** | Por `hostname`. Tabla hostname→persona en el `CLAUDE.md` raíz |
| **Estados** | 🔴 roto/sin hacer · 🟡 probado por código, **no** por una persona · 🟢 verificado por una persona en la app real. **Nada es 🟢 hasta que un humano lo usó** |
| **Idioma** | Todo en español, incluida la terminología técnica. Regla explícita |
| **Scripts** | En `<módulo>\.claude\sistema\`. Los reemplazados van a `Superados\` con fecha. 117 scripts `.py` activos |

## Los módulos

```
Bertok - Documentos\
├── CLAUDE.md                 <- contexto raíz, se carga siempre
├── ML.db                     <- FUENTE ÚNICA de Mercado Libre (SQLite, 47 tablas)
├── 00 - Básicos\             <- catálogo maestro de SKUs
├── 01 - Contabilium\         <- exports del ERP (READ ONLY) + Finanzas
├── 02 - Mercadolibre\        <- analítica ML + Hermes + Mercado Ads
├── 03 - Lista precios\       <- MOTOR DE PRECIOS (el más maduro, r056)
├── 04 - Logística\           <- stock + Sistema de Picking
├── 05 - Compras\             <- containers, pagos, planning
├── 06 - Marketing\           <- Google Ads, Apex (Meta), Cortex (WhatsApp)
├── 07 - Contactos\
├── 10 - Pagina web\
├── 11 - Software\
├── 15 - Nuevos Productos\
└── 16 - Bertok BI\           <- capa analítica, 44 scripts, 17 tablas bertok_bi_*
```

**Infraestructura fuera de la carpeta:** VPS Hetzner con EasyPanel · **n8n** (orquestador) · **Odoo CRM** · PostgreSQL · **WhatsApp Cloud API de Meta** · LLMs en producción: Groq y Gemini.

- **Cortex:** captación de leads por WhatsApp → Odoo. 10 workflows. Reparte leads **uno por uno a medida que entran** entre Abril, Facundo y Federico.
- **Hermes:** preguntas pre-venta de ML. 9 workflows, polling cada 3 min. **En `dry_run`.** Hay un rediseño v2 aprobado y no implementado.

## Sistema de Picking

`04 - Logística\- Sistema de Picking\`. Python + FastAPI + SQLite + HTML/JS **sin frameworks**. Corre en la PC de Gerardo, puerto 8000, se usa **desde los celulares del depósito por WiFi**.

**Uso diario real, pero todavía en depuración**: roles abiertos, flujo en ajuste. **Se cae solo por causa desconocida** (hay watchdog). Comparte la instalación de Python con ZKBioTime, lo que ya generó efectos colaterales.

`picking.db` vive **fuera de OneDrive** (`C:\Sistema de Picking\`) a propósito: una SQLite en WAL usa tres archivos que deben estar coherentes, y la sincronización los rompe.

**Exige foto y número de remito para cerrar un pedido.**

## Reglas de datos ya resueltas — NO re-derivarlas

- **`COT` (cotización) SIEMPRE cuenta como venta.** Son ventas en efectivo sin factura que mueven stock.
- **Nunca medir demanda en meses con quiebre de stock** (disponibilidad < 70%). Un SKU pasó de 18 a 3.536 u/mes al corregirlo.
- **Estimador central = mediana, no media.** Los meses post-container inflan el promedio hasta 69%.
- **Las tablas de hechos se acumulan, nunca se reemplazan en bloque.** DELETE + recarga hizo perder 505 filas de facturación real, en silencio.
- **Toda base de cálculo es sin IVA.**

## Reglas de negocio duras

1. **Anti-canibalización:** `precio_ML >= precio_lista_local × 1.15`
2. **Punto de Quiebre publicitario:** ningún aviso activo si su ACoS real supera `(precio − costo_pack_cIVA − comisión − cargo fijo − IIBB − IVA percepción − overhead) / precio`
3. **Prohibido «markup bruto sobre costo».** Sólo markup operativo pre-ADS y markup neto sobre costo (piso 45%)
4. **Comisiones y cargo fijo de ML son ALL-IN** (ya incluyen IVA). Nunca multiplicar por 1,21
5. **Ningún parámetro de ML se escribe a mano** — se mide contra la API o la factura real
6. **Frontera:** Mercado Ads decide campañas, nunca precios; el motor de precios decide precios, nunca qué aviso se pausa
7. **Los precios no bajan:** lo que se libera de la fórmula va a utilidad

---

# PARTE 2 · PROYECTO A — CENTRO DE OPERACIONES

> En la pantalla del equipo se llama **«DEJÁ DE ACORDARTE DE TODO»**.
> «Centro de Operaciones» es el nombre técnico.

**Estado: 🔴 sin implementar. Arquitectura cerrada, cimientos escritos y probados por código (🟡).**

## Principio rector

> **Si una tarea es importante para Bertok y alguien tiene que acordarse de hacerla, el sistema todavía está incompleto.**

Las personas ejecutan procesos definidos. El sistema detecta, fecha, muestra, asigna, controla, registra, escala y deja evidencia.

**Límite honesto:** el software hace *visible* la ausencia de un dueño, no la crea. Una tarjeta roja sin dueño y sin consecuencia se vuelve paisaje en tres semanas.

## Qué es y qué no es

**Es** una capa de detección, priorización, asignación, control y registro sobre procesos que ya ocurren.

**No es:**
- No es el sistema operativo de Bertok. ML, Contabilium y Picking siguen haciendo las cosas
- No es la capa analítica. Bertok BI analiza el pasado; el Centro actúa sobre el presente
- No recalcula nada que ya calcule otro módulo
- No es un tablero de métricas. Si un número no dispara una acción, no va

> **El Centro sólo lee de los sistemas ajenos. Lo único que escribe es su propia `ops.db`.** Sin excepciones. Se evaluó una (crear el pedido de reposición Full dentro de Picking) y **se rechazó**; se resolvió por detección.

## Fundamentos externos

Lo que se diseñó tiene nombre en cinco disciplinas y en tres hay estándares maduros:

| Disciplina | Qué aporta |
|---|---|
| **ISA-18.2** (alarmas) | *Toda alarma debe ser un llamado necesario y accionable a una respuesta humana*, documentada antes de encenderla → la ficha de racionalización |
| **Andon** (Toyota) | La pantalla es un tablero Andon digital. *Las plantas que le sacan valor definen quién responde y en cuánto tiempo antes de colgar el display* |
| **Google SRE** | Separa **aviso** (acción inmediata), **ticket** (acción, no ahora) y **registro** (nadie se entera) |
| **Revisión periódica (R,S)** | El nivel objetivo se elige donde el costo de quedarse corto iguala al de pasarse |
| **Kanban** | Límites de trabajo en curso |

**El dato que más debería preocupar:** los equipos reciben del orden de **2.000 alertas por semana y sólo ~3% requiere acción inmediata**. El resultado no es que respondan peor a las malas — **dejan de responder a todas**.

> El riesgo número uno del proyecto no es técnico. Es que funcione, grite de más tres semanas, y el equipo aprenda a no mirar la pantalla.

## La jerarquía de prevención — filtro obligatorio

De Shingo (Toyota): **la inspección no previene defectos, sólo los encuentra después.**

| | Nivel | |
|---|---|---|
| 1 | Eliminación | El error no puede ocurrir |
| 2 | Reemplazo | Se cambia el proceso |
| 3 | Facilitación | Tan fácil hacerlo bien que casi nadie falla |
| 4 | **Detección** | **Acá vive el Centro** |
| 5 | Mitigación | Se limita el daño |

> **Antes de construir una tarjeta hay que probar los niveles 1 a 3. La tarjeta existe sólo para lo que no se puede prevenir.**

**Corolario:** *un bloqueo que impide la acción incorrecta pero no ofrece camino para el caso legítimo no previene el error: genera atajos.*

## El motor

**Una tarjeta son dos cosas separadas:**

- **Detector**: función pura. Lee las fuentes de solo lectura y devuelve 0..N *hallazgos*. No escribe, no avisa, no recuerda. Idempotente.
- **Estado**: vive en `ops.db` y es lo único que recuerda.

**La clave natural es el corazón.** Cada hallazgo trae una clave estable derivada del hecho real:

```
cierre:remito:18432
despacho:2026-09-05:flex
full:ciclo:2026-09-16:armar
ads:aviso:MLA8823:quiebre
cex:container:CT-0042:saldo
```

- Clave que ya existía → mismo problema. Se actualizan datos, **se conserva la fecha de nacimiento**
- Clave nueva → nace un hallazgo
- Clave que desapareció → cierra solo, motivo `automático`

**Sin clave natural no hay antigüedad, y sin antigüedad no hay prioridad creciente, ni escalado, ni auditoría.**

### Ciclo de vida

```
detectado → visible → asignado → en_curso → [en_revisión] → resuelto → archivado
```

- `detectado` ≠ `visible`. Esa separación evita que la pantalla grite todo el tiempo
- **Nace asignado, nunca huérfano.** Si el asignado se dio de baja → dueño → suplente → Gerardo
- `resuelto` lleva motivo obligatorio: `automático` o `confirmado` (con nombre)
- Un hallazgo cerrado que reaparece **no revive**: nace uno nuevo, enlazado
- `en_curso` sin actividad al cierre del día vuelve a `asignado`

**No existe el estado `descartado`.** Un hallazgo tiene dos salidas: se resuelve, o el detector deja de verlo. Si un detector da falsos positivos, **se apaga la tarjeta, no el síntoma.**

### Posponer

Sólo el responsable asignado, desde su PC logueado. **A la tercera vez consecutiva sobre el mismo hallazgo, se notifica a Gerardo.**

### Turnos rotativos

| Proceso | Rotan | Cadencia |
|---|---|---|
| Despachos del día | Facundo ↔ Federico | Diaria |
| Preguntas ML | Abril → Facundo → Federico | Diaria |
| Reposición a Full | Facundo ↔ Federico | Por ciclo (~15 días) |

- **El turno define quién nace dueño, no quién queda dueño.** Un hallazgo del martes se queda con el dueño del martes aunque siga abierto el jueves
- **Hay que poder marcar ausencias**, o la rotación asigna a alguien que no está y todo escala

### Asignación por dato

> **La asignación puede venir de configuración o venir del dato. Cuando puede venir del dato, siempre es mejor.**

En Pendientes de cierre canal ML, el responsable sale de `picking.db`: quien armó ese paquete. Escala al dueño del turno de Despachos de ese día.

### Prioridad

Verde/amarillo/rojo son **salidas**, no estados. Insumos: **tiempo restante, antigüedad, magnitud**. Es **monótona**: si nadie hace nada, no baja. **El orden en pantalla lo decide ella, no la maqueta.**

Para tarjetas con reloj duro, la prioridad sale de **la proyección**, no del conteo:

```
DESPACHOS · FLEX 13:30
18 de 24 listos
4 en armado · 2 sin empezar
ritmo 3 min/pedido → termina 13:04
```

A las 12:40 con 12 pendientes: 36 minutos, termina 13:16, **no alcanza — y eso es rojo antes de que venza el plazo**. El ritmo sale de `picking.db`, **mediana de los últimos 30 días**.

## Ficha de racionalización — antes de programar

| Campo | Qué responde |
|---|---|
| Causa | Qué hecho real hace nacer el hallazgo |
| Consecuencia | Qué pasa si nadie actúa. **Si no se puede escribir una consecuencia real, la tarjeta no debería existir** |
| Acción correctiva | Qué hace la persona. **Una acción, no «revisar»** |
| Tiempo de respuesta | Cuánto tiene antes de que sea tarde |
| Condición de cierre | Qué dato prueba que se resolvió |
| Clave natural | Si no se puede nombrar una estable, la tarjeta no está bien pensada |
| Dueño y suplente | Nombres |
| Apta para TV | Sí / No |

**Prueba de fuego:** si la acción correctiva queda como «mirar» o «revisar», es información, no alarma.

## Tipos de tarjeta y línea de corte

**Dos familias:**
- **De excepción** — pasó algo y el sistema detecta lo que quedó mal
- **De compromiso** — nada las dispara; son cosas que deberían ocurrir seguido y se abandonan. Van como **medidor de cumplimiento, no como alarma**, y **nunca mandan push**

**Tres mecanismos de cierre:** informativa (se cierra sola) · de acción (una persona confirma) · de calendario (nace por cadencia).

> **Ante la duda, informativa. Una tarjeta de acción es una promesa de que alguien va a ser honesto todos los días durante años.**

> **LÍNEA DE CORTE: toda tarjeta nueva arranca vacía. La deuda vieja no entra a la pantalla.**

**Estado «sin pendientes»:** gris neutro, no verde y no oculta. Cero pedidos a media mañana **es en sí mismo una señal** — puede ser que no entraron ventas, o que se rompió la integración. Si sigue en cero **a las 11:00** de un día hábil, pasa a amarillo con «verificar integración».

## Modelo de datos

`ops.db` — SQLite, WAL, `synchronous=FULL`, **fuera de OneDrive**, en `C:\Sistema de Picking\`.

| Tabla | Qué guarda |
|---|---|
| `bertok_ops_hallazgos` | **Verdad del estado actual.** Un renglón por clave natural |
| `bertok_ops_eventos` | **Auditoría**, append-only. Con persona, hora y campo `version` |
| `bertok_ops_personas` | Padrón desde Odoo + PIN local + rol. Nunca se borra un renglón |
| `bertok_ops_procesos` | Dueño, suplente, revisor, umbrales, cadencia, ventana, apta TV, modo sombra |
| `bertok_ops_turnos` | Rotaciones |
| `bertok_ops_ausencias` | Sin esto la rotación asigna a quien está de franco |
| `bertok_ops_corridas` | Cada ejecución de cada detector. 90 días de detalle |
| `bertok_ops_frescura` | Última actualización de cada fuente |
| `bertok_ops_calendario` | Feriados. Carga anual manual, ~20 fechas |

**El estado es autoritativo, no una reconstrucción.** Se escriben las dos tablas, pero el estado no se rearma desde el evento cero. Motivo: el versionado de eventos es el asesino silencioso de los sistemas reconstruibles, y ese impuesto no tiene retorno al tamaño de Bertok. Precauciones baratas: campo `version` en cada evento, y **nunca cambiarle el significado a un tipo de evento existente**.

**Guarda de alcance:** toda escritura fuera del prefijo `bertok_ops_*` se bloquea **a nivel del autorizador de SQLite**, no por convención.

**Por qué un cuarto almacén:** `ML.db` está dentro de OneDrive; varias máquinas escribiendo en simultáneo contra una SQLite sincronizada rompe el WAL. El Postgres del VPS es remoto. `picking.db` tiene su propio dueño.

## Los trece procesos

| # | Proceso | Dueño | Suplente | TV |
|---|---|---|---|---|
| 01 | Pendientes de cierre — ML | quien armó el paquete *(por dato)* | turno de Despachos | Sí |
| 02 | Pendientes de cierre — offline | Federico | Facundo | Sí |
| 03 | Despachos del día | Facundo ↔ Federico *(rotativo)* | el otro | Sí |
| 04 | Preguntas ML | Abril → Facundo → Federico *(rotativo)* | el siguiente | Sí |
| 05 | Reclamos ML | Antonella | Abril | Sí |
| 06 | Reposición a Full | Facundo ↔ Federico *(rotativo)* · revisa Antonella | el otro | Sí |
| 07 | Compras de insumos | Antonella | Gerardo | Sí |
| 08 | Mercado Ads | Facundo | Federico | Sí |
| 09 | Promociones ML | Facundo | Federico | Sí |
| 10 | Google Ads | Abril | Antonella | Sí |
| 11 | Posteo en redes | Antonella | Gerardo | Informativa |
| 12 | Rendición de cuentas | Antonella | Abril | **No** |
| 13 | Comercio exterior | Antonella | Gerardo | **Nunca** |
| — | Cobranzas 🔴 bloqueada | Antonella | Gerardo | No |

> ⚠️ **Antonella es dueña de 6 de 13 procesos**, incluidos los dos de mayor riesgo económico. Si falta una semana, se cae la mitad de Bertok. **Gerardo figura como suplente en cinco** — el objetivo era que la empresa dependa menos de él y la tabla dice lo contrario. **Es la decisión abierta más importante y no la resuelve la arquitectura.**

### Parámetros fijos

- **Despachos:** Flex venta hasta 13:00, moto 13:30. Mercado Envíos hasta 15:00. **Lunes a sábado**, sin domingos ni feriados. Cero pedidos → amarillo a las **11:00**
- **«Listo» = orden emitida y bultos cerrados.** No «etiqueta impresa», no «escaneo completo»
- **«Hoy» termina a las 13:00**
- Insumos cada 10 días · Redes 4 por mes · Google Ads y Mercado Ads semanales · Full cada 15 días · Rendición los viernes
- **Sync de padrón desde Odoo cada 6 h**, con botón de sincronizar ahora. **Un alta puede esperar, una baja no**: se hace local e inmediata. Si el Centro y Odoo se contradicen, **gana la restricción**

## Confidencialidad — reglas, no recomendaciones

| Tarjeta | Regla |
|---|---|
| **Comercio exterior** | **NUNCA en la TV.** Contiene la distinción PI Real / PI Declarada. Acceso sólo Gerardo y Antonella |
| **Rendición de cuentas** | El Centro registra **que el viernes hay un informe para Fernando (socio) y si se hizo**. **No registra montos, conceptos ni conciliaciones** |
| **Cobranzas** | No va a la TV |
| **Correctivos** | Sólo que hubo uno, fecha y referencia. El detalle y el monto van al legajo, fuera del Centro. **Pendiente: consulta al contador/abogado antes de implementar ese campo** (Ley 25.326) |

**La TV** está en la oficina grande donde trabajan los vendedores y se arman los pedidos. Muestra todas las tarjetas **aptas para TV**. En cada PC, la persona logueada ve **lo asignado a ella más todo lo de los procesos de los que es dueña**.

## Escalado

| Nivel | Cuándo | A quién |
|---|---|---|
| 0 | Se vuelve visible | Pantalla y modo usuario del asignado |
| 1 | Umbral de la tarjeta | WhatsApp al asignado |
| 2 | Umbral de escalado | WhatsApp al suplente o supervisor |
| 3 | Vence el límite duro, o 3ª posposición | **Gerardo. Sólo acá** |

**El reloj corre desde el acuse de recibido, no desde la aparición.** Si no hay acuse dentro del umbral, eso mismo escala — distingue «no lo vio» de «lo vio y no lo hizo».

**Si algo no requiere que alguien deje lo que está haciendo, no manda WhatsApp.**

Gerardo tiene dos salidas y ninguna es un tablero: **nivel 3 por excepción** y **digest semanal**.

El canal no se construye: **n8n + WhatsApp Cloud API** ya están en producción.

## Umbrales

Tres orígenes, no mezclarlos:
- **Externo** — lo impone un tercero (ML, la moto, el vencimiento de un container)
- **De política** — lo decide Gerardo
- **Derivado** — sale de la distribución observada en modo sombra

> **El umbral derivado se pone donde los casos normales ya terminaron: percentil 80-90 de lo que sí se resolvió.**

**Hipótesis de arranque** (no son recomendaciones; la sombra las confirma o corrige):

| Tarjeta | Visible | Aviso | Escalado | Origen |
|---|---|---|---|---|
| Pendientes de cierre — offline | ~4 días | ~7 días | ~10 días | Derivado |
| Pendientes de cierre — ML | ~1 día | ~2 días | ~4 días | Derivado |
| Despachos | **por proyección** | | | Externo |
| Preguntas ML | ~30 min | ~2 h | ~4 h | Externo |
| Reclamos ML | ~4 h | ~1 día | ~2 días | Externo |
| Mercado Ads | inmediato | ~1 día | ~3 días | Derivado |
| Compras de insumos | día 10 | día 12 | día 14 | Política |
| Full · hito 1 | T−7 | T−5 | T−4 | Externo |
| Comercio exterior | T−15 | T−7 | T−3 | Externo |

**Tope de trabajo en curso: arrancar sin tope y medir.** Si rutinariamente es 1 o 2, no hace falta nunca. Un tope que nunca se toca es puro estorbo.

## Modo sombra — compuerta obligatoria

| Etapa | Qué pasa | Cómo se avanza |
|---|---|---|
| 🔴 Sombra | Corre y registra. **No se muestra ni se avisa** | Mínimo 2 ciclos del proceso |
| 🟡 Visible sin push | Aparece en pantalla, sin WhatsApp | Revisión con el dueño: qué era real y qué ruido |
| 🟢 Completa | Push y escalado activos | Una persona la usó y sirvió |

**Métricas del sistema sobre sí mismo:** avisos por día y persona · tasa de acción · tasa de posposición · tiempo hasta el acuse.

> **Una tarjeta que grita en falso se apaga. No se tolera, no se ignora: se apaga y se rediseña.**
> Si genera más de un puñado de pushes por día, **la tarjeta está rota, no el equipo.**

## La primera tarjeta · Pendientes de cierre

Todos los datos están en `picking.db`: cero ingesta nueva, ninguna regla de negocio nueva, cero riesgo externo.

**El problema, bien planteado.** El remito **siempre se emite**. Y Picking **ya exige foto y número de remito para cerrar**, así que el control de nivel 2 ya existe. Lo que falla está afuera: el papel sale con el expreso o el cliente y muchas veces **no vuelve, o vuelve sin firmar**.

**Son tres problemas distintos que hoy se ven iguales:**

| | Dónde falla | ¿Bajo control de Bertok? |
|---|---|---|
| a | El expreso o el cliente **nunca firma** | No |
| b | Firma pero **no lo devuelve** | No |
| c | Vuelve y **nadie lo carga** | Sí |

**El 40-50% es una hipótesis, no un dato.** Surgió durante la depuración de Picking, con la gente aprendiendo el flujo. Se mide antes de diseñar contra él.

**El arreglo va en Picking, no en una tarjeta.** Picking exige la prueba pero **no ofrece un camino legítimo para cuando esa prueba genuinamente no va a llegar**. La solución es cerrar **con niveles de prueba**:

| Nivel | Qué se cargó | Peso probatorio |
|---|---|---|
| **A** | Remito firmado — foto + número | Alto |
| **B** | Constancia del expreso — guía + acuse de entrega | Medio-alto. **No depende del papel** |
| **C** | Confirmación del cliente por WhatsApp | Medio. La infraestructura ya existe |
| **D** | Sin prueba — con motivo escrito y autorización | Bajo. **Es una incidencia** |

Con esto el pedido **siempre se puede cerrar honestamente**, y lo que se mide pasa a ser **«con qué calidad cerraron»**.

**El reframe:** si el problema es (a) o (b), la tarjeta no es un recordatorio sino un **scorecard de proveedores**: ¿qué expreso devuelve los remitos y cuál no? Eso no se arregla insistiéndole a nadie de adentro — **se arregla renegociando o cambiando de expreso**.

> **Consecuencia de diseño:** el hallazgo debe llevar **el expreso y el cliente como atributos**. Y el modo sombra tiene que **separar las tres causas desde el día uno**.

**Contexto legal:** el remito no es comprobante fiscal obligatorio, pero es la prueba clave de recepción; su fuerza depende de la firma y la trazabilidad. Conservación mínima 2 años el duplicado, y para documentación fiscal 5 años después de operada la prescripción.

## Reposición a Full — la tarjeta

**Cuatro hitos, una sola tarjeta:**

```
1 · Decidir      Qué SKU y cuánto. T−7 o antes
2 · Generar      Crear el envío en ML, bajar etiquetas, fijar recolección. T−4 mín
3 · Armar        Escaneo, bultos, etiquetado, en Picking
4 · Recolección  ML retira. Cierra con el acuse del inbound
```

**Cómo cierra el hito 3 sin escribir en ningún lado:** el Centro **produce la lista**, una persona la carga en Picking, y el Centro **cierra el hito por detección** — ve el pedido terminado en `picking.db`. Consigue lo mismo que la excepción de escritura que se descartó, pero por lectura pura.

**La fecha de recolección no puede caer sábado ni feriado.** El sistema tiene que advertirlo al elegir la fecha.

**Cuánto enviar** — ver la Parte 3, que es donde se desarrolla.

## Infraestructura

| Pieza | Definición |
|---|---|
| **Servidor** | PC dedicada, siempre encendida |
| **Migración de Picking** | Se muda a esa PC. **Mudar antes de terminar de depurar**, no después: se depura donde el sistema va a vivir, se sale del Python compartido con ZKBioTime, y se puede probar el `busy_timeout` en el mismo movimiento |
| **Actualización de datos** | `actualizar_ml.py`, el downloader y el `.bat` **corren en la PC dedicada**. El Centro lee el archivo local |
| **Ollama / generación de imágenes** | **En otra máquina.** La PC servidor tiene un solo trabajo: no estar caída entre las 9 y las 15:30 |
| **Stack** | Idéntico al de Picking. Cero dependencias nuevas |
| **TV** | Conectada directo a una salida de video del servidor. Kiosco, sólo lectura, **con reloj de último refresco visible** |
| **UPS** | Pendiente, para enero |
| **Acceso remoto** | RustDesk, ya instalado |

**La TV 24/7:** reinicio programado en horario no operativo · refresco programado · watchdog que reinicie el navegador · pantalla completa sin barra de tareas. Un tablero donde las tarjetas aparecen y desaparecen **castiga mucho menos la pantalla** que un dashboard fijo.

**Plan B:** backup diario + **procedimiento en papel para el depósito**. Se descartó la PC de repuesto fría — consecuencia: si la máquina no arranca, la recuperación pasa de ~1 hora a varios días. Mitigación gratis: tener escrito el procedimiento de instalación y los instaladores guardados.

> **El plan B se prueba una vez, a propósito, un sábado. Un plan B no probado no existe.**

## Salud de datos

> **Una pantalla en verde sobre datos de anteayer es peor que no tener pantalla.**

- Cada hallazgo lleva su `datos_al`
- **Un detector que falla no deja la tarjeta en verde: la deja en gris «sin datos»**. Verde = «miré y está bien»; gris = «no pude mirar»
- Si un detector falla N corridas seguidas, escala

**Tolerancia por fuente:** `picking.db` 15 min · `ML.db` 1 hora · Excel de Contabilium su cadencia + margen (si baja 1 vez/día → 26 h).

**El caso que la TV negra no cubre:** PC viva con el Centro colgado muestra la última página, en verde. El **reloj en pantalla** resuelve la mayor parte; el **latido externo hacia n8n** queda pendiente.

## Seguridad

| Riesgo | Medida |
|---|---|
| **PIN adivinable** | 4 dígitos son 10.000 combinaciones. OWASP: **bloqueo tras 3-5 intentos**, más límite de tasa. Los fallidos quedan en la auditoría |
| **Roles abiertos** | El Centro **nace con roles cerrados**. Sólo Gerardo cambia configuración |
| **PIN compartido** | Arruina la auditoría. Se combate haciendo el login barato y midiéndolo |
| **Acceso remoto** | RustDesk con contraseña fuerte distinta por máquina. **No exponer el puerto del Centro a internet** |

## Frecuencia por detector

| Detector | Frecuencia |
|---|---|
| Despachos | **5 min**, sólo 9:00–15:30 |
| Salud de datos | 15 min |
| Pendientes de cierre · Reclamos ML | 30 min |
| Preguntas ML | lee lo que trae Hermes |
| Mercado Ads · Promociones | 1 vez por día |
| Full · Comercio exterior | 1 vez por día, a la mañana |
| Insumos · Redes · Rendición · Google Ads | 1 vez por día |

## Relación con cada sistema

| Sistema | Acceso | Qué usa |
|---|---|---|
| **ML.db** | Lectura | **Única fuente de datos de ML.** El Centro nunca llama a la API |
| **bertok_bi_*** | Lectura | Rentabilidad, rotación, ABC, demanda. No se recalcula nada |
| **picking.db** | Lectura | Base de Despachos, Pendientes de cierre y el cierre de Full |
| **05 · Compras** | Lectura | Hitos de container: anticipo, saldo, embarque, arribo |
| **Motor de precios** | A construir | Promociones ML necesita **el precio mínimo por SKU** como salida del motor |
| **Hermes** | Ingestor | **Vuelca sus preguntas a `ML.db`.** El Centro pasa a ser la cara visible de **Hermes v2** |
| **Contabilium** | Lectura | Vía los Excel del scraper. El Centro no hace scraping propio |
| **Odoo** | Lectura | Padrón de empleados, sync cada 6 h a caché local |
| **n8n** | Entrada y salida | Webhook de salida para WhatsApp. Y de entrada: **las notificaciones de ML** — ML recomienda webhooks en lugar de polling para reclamos |
| **Bertok BI** | Recíproco | El Centro lee `bertok_bi_*`. Más adelante BI podrá leer `bertok_ops_*` para medir cumplimiento |

## Plan de fases

| Fase | Qué | Termina cuando |
|---|---|---|
| **0 · Terminar Picking** | PC dedicada · mudar Picking · scripts a la misma máquina · Ollama a otra · **los 4 niveles de cierre** · roles cerrados · **pragmas de SQLite** · `ops.db` + backup · padrón desde Odoo · login unificado · `CLAUDE.md` y `BITACORA.md` | **Picking estable en la máquina nueva, sin caídas, dos semanas de uso normal**, y el backup restauró bien una vez |
| 1 · Motor + 1ª tarjeta | Detectores, clave natural, estados, turnos, guarda, TV con reloj, modo usuario, push por n8n, auditoría **+ Pendientes de cierre** con línea de corte **+ capacitación** | Una persona del depósito cerró un pendiente real que la tarjeta le mostró |
| 2 · Salud de datos | Frescura, tarjeta de salud, latido externo a n8n | Detecta una sesión de Contabilium vencida antes que una persona |
| 3 · Despachos + Insumos | En sombra primero. Acá se calibra el ritmo por pedido | Un día de despacho salió completo sin que Gerardo preguntara nada |
| 4 · Mercado Ads | Punto de quiebre publicitario sobre datos ya existentes | Se pausó un aviso perdedor que nadie había notado |
| 5 · Comercio exterior | Hitos de container desde `05 - Compras`. Fuera de la TV | El sistema avisó un vencimiento antes que Antonella |
| 6 · Full | 4 hitos, feriados, cantidades vs. sugerencia de ML | Un ciclo se armó desde la lista que produjo el sistema |
| 7 · Preguntas + Promociones + Reclamos | Hermes v2, precio mínimo por SKU, ingesta de reclamos | Hermes sale de `dry_run` |
| 8 · Calendario | Rendición, Google Ads, Redes. Sin push | Un mes cerró con los 4 posteos hechos |
| 9 · Cobranzas | Después de completar Finanzas | — |

**Corrección de método:** el motor y la primera tarjeta van **juntos**. Una arquitectura conceptual sin contacto con datos reales se ve preciosa y se rompe en el primer `JOIN`.

**Capacitación** es entregable de Fase 1, no una buena intención. La evidencia sobre por qué fracasan estos sistemas en PyMEs es consistente: **«el equipo no se resiste a la tecnología, se resiste a aceptar que el sistema muestra una realidad distinta de la asumida»**. Ese choque va a ocurrir el día uno con el número de remitos. **Presentarlo como problema de proceso, no de personas.**

## Cómo agregar una tarjeta nueva

1. Probar la **jerarquía de prevención**. ¿Se puede evitar en vez de detectar?
2. Completar la **ficha de racionalización**
3. Nombrar la **clave natural**
4. Elegir tipo — **informativa por defecto**
5. Nombrar **dueño y suplente**
6. Definir **línea de corte**
7. Correr en **sombra**, mínimo 2 ciclos
8. **Derivar umbrales** con el dueño presente
9. Encender **sin push**, después **con push**
10. Anotar en `BITACORA.md` qué se verificó y quién

**Una tarjeta = un proceso.**

## Estado de los cimientos — 🟡 probado por código

| Script | Qué hace |
|---|---|
| `esquema_ops.sql` | 9 tablas, 1 vista, 4 triggers, 8 índices |
| `guarda_alcance.py` | Bloquea escrituras fuera de `bertok_ops_*` vía el **autorizador de SQLite** |
| `crear_ops_db.py` | Crea `ops.db` con pragmas. Idempotente. Aborta si la ruta está en OneDrive |
| `probar_guarda.py` | **33 comprobaciones, todas OK** |
| `backup_bases.py` | `VACUUM INTO` + verificación + SHA-256 + rotación 7+4 |
| `restaurar_prueba.py` | Restauración mensual con verificación de firma e integridad |

**Primer comando en la PC:**

```
cd "17 - Centro de Operaciones\.claude\sistema"
python probar_guarda.py        # tiene que dar 33/33
```

**Si no da 33/33, parar.** Se probaron en Linux con Python 3.13 y SQLite 3.45; en Windows puede tomar el Python de ZKBioTime, que quizás tenga un SQLite viejo sin `VACUUM INTO`.

## Trampas conocidas — NO repetir

1. **Una SQLite en WAL no se copia con un `copy`.** Son tres archivos. Backup con **`VACUUM INTO`**, rotación 7+4, **nunca pisar el mismo archivo**, restauración de prueba mensual.
2. **`PRAGMA integrity_check` no detecta toda la corrupción.** Medido: con **3.000 bytes ensuciados en páginas libres devolvió «ok»** y la base abrió normal. Por eso cada copia lleva un **SHA-256 al lado**.
3. **Al verificar un backup, contar las filas del origen ANTES de copiar.** Si se cuenta después, con la base en uso el origen siempre tiene más y toda corrida da falso negativo.
4. **`busy_timeout` es obligatorio.** Sin él una escritura concurrente falla al instante. 3-5 s, más `BEGIN IMMEDIATE` y `wal_autocheckpoint` ~1000. **Hipótesis a verificar: esto puede ser la causa de las caídas de Picking.**
5. **`ML.db` está dentro de OneDrive.** Nunca escribir desde el Centro.
6. **El Centro nunca llama a la API de ML.** La cuota es compartida y opaca.
7. **Un detector que falla deja gris, nunca verde.**
8. **El 40-50% de remitos sin cerrar es hipótesis, no dato.**
9. **Ollama va en OTRA máquina.**
10. **La guarda de alcance debe permitir el prefijo `sqlite_`.** Todo DDL escribe por debajo en `sqlite_master`; sin eso no se puede crear ni el propio esquema. Es seguro porque escribirlas a mano exige `PRAGMA writable_schema`, que está denegado.

## Decisiones abiertas

| # | Decisión | Cuándo |
|---|---|---|
| **01** | **La carga de Antonella (6 de 13) y la de Gerardo (5 suplencias).** No la resuelve la arquitectura | **Antes de encender** |
| 02 | Que el motor de precios publique el **precio mínimo por SKU** | Fase 7 · módulo 03 |
| 03 | **Valores** de los umbrales derivados. El método ya está definido | Se miden en sombra |
| 04 | **Latido externo hacia n8n** | Fase 2 |
| 05 | **UPS** | Enero |
| 06 | **Consulta legal** sobre el registro de correctivos | Antes de ese campo |
| 07 | **¿El remito digital de ARCA alcanza a Bertok?** Cronograma jul-2026 → mar-2027 (RG 5866/2026). Si alcanza, la tarjeta de Pendientes de cierre cambia de forma | **Fase 1** |

## A verificar (datos, no decisiones)

- ⚠️ **Hoy, en depuración, ¿qué pasa con los pedidos que no se pueden cerrar en Picking?** ¿Se acumulan, hay cierre forzado, o se cierra con lo que haya? **Es la más importante:** define si el punto de partida es un problema a medir o un dato ya contaminado
- ¿El expreso da **número de guía con constancia de entrega**? De eso depende el nivel B
- ¿**Cuántos expresos** se usan?
- ¿`ML.db` ya ingiere **reclamos**? ¿Ya trae **stock en Full, envíos de reposición y la sugerencia de cantidades de ML**?
- ¿Los **cargos de almacenamiento de Full** están identificados dentro de las 7.051 filas de cargos reales?
- ¿El **sábado** rige el mismo horario de corte?
- **Verificar la hipótesis de `busy_timeout`** durante la mudanza de Picking

---

# PARTE 3 · PROYECTO B — REPOSICIÓN A FULL

**Estado: 🔴 no existe. Sin relevar, sin tablas, sin código.**

> Lo que sigue se pega **tal cual** como primer mensaje de una sesión dedicada, en una sesión **local**.

## DÓNDE VA — YA DECIDIDO

El módulo vive en: **`02 - Mercadolibre\Reposición Full\`**

Razón: escribe en `ML.db`, y el módulo 02 es el dueño de Mercado Libre. Además hay precedente — Hermes y Mercado Ads ya son submódulos de 02.

Las tablas que escriba son de **DOS CLASES que no se mezclan**:

1. **DATOS CRUDOS DE ML** (stock en Full, envíos de reposición, sugerencia de cantidades). Son **ingesta**, le pertenecen a `actualizar_ml.py`, y siguen **la convención de nombres que ya usa `ML.db`**. No inventar prefijo nuevo.
2. **EL CÁLCULO DE REPOSICIÓN** (lista propuesta por SKU, los tres costos, el desvío contra ML, la decisión). Es **derivado** y lleva prefijo propio: **`bertok_full_*`**

Si se mezclan, en seis meses nadie sabe qué vino de ML y qué calculamos nosotros. **No va en `bertok_bi_*`:** BI analiza el pasado, esto decide una operación futura.

## LA OPERACIÓN

Hay que distinguir **dos cosas** que estaban confundidas en una sola regla:

1. **FULFILLMENT DE PEDIDOS:** Bertok **nunca** arma ni despacha un pedido Full. Por eso Picking los filtra. Sigue vigente.
2. **REPOSICIÓN DE INVENTARIO A FULL:** sí existe. Cada ~15 días, envío único de **200 a 300 paquetes** de SKU repetidos, con flete de ML que ML cobra. Después ML almacena y entrega.

**El `CLAUDE.md` raíz todavía dice «nunca Full» sin esa distinción. Corregirlo es parte del trabajo.**

Datos duros:
- Cadencia ~15 días (estimación, hay que optimizarla)
- Ejecuta **Facundo**, revisa **Antonella** (rotativo Facundo↔Federico por ciclo)
- Se arma mínimo 4 días antes; se puede programar hasta un mes
- Las etiquetas de bulto y de producto salen de la plataforma de ML
- **La fecha de recolección no puede caer sábado ni feriado:** genera horas extras

## LA ECONOMÍA — EL CORAZÓN DEL PROBLEMA

Es **reposición con revisión periódica** (modelo R,S): el nivel objetivo se elige donde el costo de quedarse corto iguala al de pasarse.

**QUEDARSE CORTO:** margen perdido + daño de posicionamiento en ML.

**PASARSE — dos componentes, y el segundo duele:**
- ML cobra almacenamiento **por unidad y por día**, desde que entra hasta que se vende o se retira
- Si un SKU no rota, **ML termina descartándolo**: se pierde la mercadería entera

**COSTO OCULTO — el que más se pasa por alto:**
**No hay reserva de stock.** Lo que va a Full deja de estar disponible para Flex y para el local.

> **Mandar de más a Full tiene triple castigo: pagás almacenaje, arriesgás que ML tire la mercadería, y desabastecés los otros dos canales.**

Por eso el cálculo **no puede ser** «cubrir 15 días de demanda de Full». Tiene que ser un **reparto entre canales**: el stock es uno solo.

**LA SUGERENCIA DE ML: mostrarla, no obedecerla.** ML calcula su propia sugerencia en la misma ventana. La salida muestra **las dos lado a lado con el desvío**, y pide decisión humana cuando se separan más de un umbral. **ML optimiza para ML**: más stock en Full es más ingreso por almacenamiento para ellos, y su sugerencia no sabe nada de las ventas por Flex ni por el local ni del costo de mercadería.

## PRIMERO RELEVAR, DESPUÉS PROGRAMAR

**No escribir código hasta responder esto**, mirando los datos reales:

1. ¿Qué tablas tiene `ML.db` hoy? Esquema completo, cuáles se relacionan con Full, y cuál es la convención de nombres
2. ¿`ML.db` ya trae **stock en Full**? ¿Y los **envíos de reposición** (inbounds) con su estado? ¿Y la **sugerencia de cantidades** de ML?
3. En la tabla de cargos reales (~7.051 filas), ¿están identificados los **cargos de almacenamiento** de Full? ¿Con qué nombre o código?
4. ¿Hay registro histórico de los envíos ya hechos? Si no, ¿se puede reconstruir desde los cargos de flete?
5. ¿Qué produce hoy `bertok_bi_*` que sirva acá? Hace falta demanda por SKU **y por canal**, rotación y clasificación
6. ¿Cómo está estructurado `actualizar_ml.py` y el `.bat` unificador?

## CÓMO SE INTEGRA

Este módulo **sí** escribe en `ML.db` — no es el Centro, que es de sólo lectura. Pero respeta las reglas de `ML.db`:

- **Un dueño por tabla**
- **Las tablas de hechos se acumulan, nunca se reemplazan en bloque**
- La ingesta se integra a `actualizar_ml.py` / al `.bat`
- Corta con error si algún dato quedó viejo

**No duplicar cálculos.** **La salida tiene que ser una tabla estable en `ML.db`**, porque el Centro la va a leer. El contrato de esa tabla es lo más importante a definir.

## ENTREGABLES, EN ESTE ORDEN

1. El relevamiento, con los datos a la vista
2. `CLAUDE.md` y `BITACORA.md` del módulo, **antes** de la primera línea de código
3. La ingesta de datos de Full a `ML.db`
4. El motor de cálculo, con los tres costos en número
5. La salida: tabla `bertok_full_*` + el contrato para el Centro

## STOP CONDITIONS

Pedir OK antes de: tocar tablas de `ML.db` ajenas · modificar `actualizar_ml.py` o el `.bat` · instalar dependencias · cambiar parámetros de negocio · borrar archivos.

---

# PARTE 4 · PENDIENTES FUERA DE LOS DOS MÓDULOS

- **El `CLAUDE.md` raíz no documenta la reposición a Full.** Hay que partir la regla en dos.
- ⚠️ **El `CLAUDE.md` de Cortex dice que Bertok vende «tintas, sustratos e insumos gráficos».** Eso alimenta los prompts del agente que le responde a **leads B2B reales por WhatsApp**. **Es independiente de los dos proyectos y es más urgente que ambos.**

---

# PARTE 5 · HARDWARE

| | |
|---|---|
| Placa del servidor | ASUS PRIME Z390-A · LGA1151 · DDR4 |
| **RAM** | **DDR4 UDIMM 8 GB 3200.** Evaluada: `Raptor RAP-UD4-8G-3200`, tienda oficial. Dos módulos si el presupuesto da → slots **A2 y B2** (2º y 4º desde el micro) |
| Disco | SSD 256 GB. Alcanza **si la carpeta de OneDrive entra**: usar «Archivos a pedido» y dejar en local sólo lo que los scripts tocan. No pasar del 80% |
| Ollama | **En otra máquina** |

**No sirve:** DDR5, RDIMM, ECC, REG, LRDIMM, SODIMM.
La etiqueta tiene que decir **`PC4-25600U`** — la **U** final es de UDIMM.

Al instalar: **XMP en la BIOS** (`Ai Tweaker → Ai Overclock Tuner → XMP`), y **MemTest86 una pasada** antes de poner el servidor en producción.

---

# PARTE 6 · FUENTES CONSULTADAS

- **ISA-18.2 — gestión de alarmas.** [ISA-18 Series](https://www.isa.org/standards-and-publications/isa-standards/isa-18-series-of-standards) · [Understanding ISA-18.2](https://www.isa.org/getmedia/55b4210e-6cb2-4de4-89f8-2b5b6b46d954/PAS-Understanding-ISA-18-2.pdf)
- **Andon y gestión visual.** [Lean Manufacturing](https://www.l2l.com/blog/andon-in-lean-manufacturing) · [Visual Management](https://tervene.com/blog/visual-management/)
- **Google SRE — alertas y guardias.** [Being On-Call](https://sre.google/sre-book/being-on-call/) · [SRE alerting practices](https://incident.io/blog/sre-alerting-best-practices)
- **Poka-yoke — jerarquía de prevención.** [Lean Enterprise Institute](https://www.lean.org/lexicon-terms/poka-yoke/) · [ASQ](https://asq.org/quality-resources/mistake-proofing)
- **Reposición con revisión periódica.** [Periodic Review (R,T)](https://pubsonline.informs.org/doi/10.1287/msom.5.1.37.12761)
- **Costos de almacenamiento en ML Full.** [Cómo reducirlos](https://base.com/es-AR/blog/costo-almacenamiento-mercado-libre/) · [Almacenamiento prolongado](https://blog.real-trends.com/2022/03/04/cuales-son-los-costos-por-almacenar-stock-en-mercado-envios-full/)
- **Kanban — límites de WIP.** [Atlassian](https://www.atlassian.com/agile/kanban/wip-limits)
- **OWASP — autenticación.** [Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- **Ley 25.326 — datos personales.** [Texto actualizado](https://www.argentina.gob.ar/normativa/nacional/ley-25326-64790/actualizacion)
- **Remito en Argentina.** [Valor probatorio (SAIJ)](https://www.saij.gob.ar/instrumentos-privados-remito-valor-probatorio-sul0003111/123456789-0abc-defg1113-000lsoiramus) · [ARCA remito digital](https://www.iprofesional.com/impuestos/426852-arca-remito-digital-plazos-obligaciones-y-todas-las-claves-del-nuevo-documento)
- **SQLite en producción.** [WAL y concurrencia](https://micrologics.org/blog/sqlite-in-production-optimizing-wal-mode-concurrency-and-vfs-layers-for-low-latency-app-servers)
- **Event sourcing.** [Schema evolution (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0164121221000674)
- **Pantallas 24/7.** [Chromium kiosk](https://smartupworld.com/chromium-kiosk-mode/) · [Burn-in](https://us.ktcplay.com/blogs/support-tips/burn-in-prevention-24-7-monitoring-displays)
- **API de Mercado Libre.** [Rate limits](https://global-selling.mercadolibre.com/devsite/manage-questions-answers-global-selling/question-3) · [Claims](https://developers.mercadolibre.com.bo/en_us/working-with-claims)
- **Adopción en PyMEs.** [Por qué fracasa la digitalización](https://www.tacticasoft.com/en/sistema-no-se-usa-digitalizacion-pyme/) · [Por qué no se usan los dashboards](https://www.ixpantia.com/es/blog/por-que-tus-colaboradores-no-utilizan-los-dashboards)

---

# APÉNDICE · LOS SEIS SCRIPTS COMPLETOS

Van en `17 - Centro de Operaciones\.claude\sistema\`.

Están **probados por código (🟡)**: 33/33 comprobaciones de la guarda, backup verificado bajo escritura concurrente, rotación probada sobre 12 días simulados. **Ninguno corrió en la máquina real todavía.**


## esquema_ops.sql

```sql
-- =====================================================================
-- Centro de Operaciones Bertok — esquema de ops.db
-- «Dejá de acordarte de todo»
--
-- Todas las tablas llevan el prefijo bertok_ops_ sin excepción.
-- La guarda de alcance (guarda_alcance.py) bloquea cualquier escritura
-- fuera de ese prefijo, a nivel del autorizador de SQLite.
--
-- Fechas: TEXT en ISO-8601 local, formato 'AAAA-MM-DD HH:MM:SS'.
-- Booleanos: INTEGER 0/1.
-- Cargas variables por tarjeta: TEXT con JSON.
-- =====================================================================

PRAGMA foreign_keys = ON;


-- ---------------------------------------------------------------------
-- PERSONAS
-- Padrón sincronizado desde Odoo. Nunca se borra un renglón.
-- Un alta puede esperar al sync; una baja no: activo_local permite
-- desactivar en el acto. Si Odoo y el Centro se contradicen,
-- GANA LA RESTRICCIÓN (ver vista bertok_ops_personas_habilitadas).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_personas (
    persona_id        TEXT PRIMARY KEY,
    nombre            TEXT    NOT NULL,
    odoo_user_id      INTEGER UNIQUE,
    pin_hash          TEXT,
    rol               TEXT    NOT NULL DEFAULT 'operador'
                              CHECK (rol IN ('operador','supervisor','admin')),
    activo_odoo       INTEGER NOT NULL DEFAULT 1 CHECK (activo_odoo IN (0,1)),
    activo_local      INTEGER NOT NULL DEFAULT 1 CHECK (activo_local IN (0,1)),
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta   TEXT,
    sincronizado_en   TEXT,
    creado_en         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Gana la restricción: habilitado sólo si las dos banderas están en 1.
CREATE VIEW IF NOT EXISTS bertok_ops_personas_habilitadas AS
    SELECT * FROM bertok_ops_personas
     WHERE activo_odoo = 1 AND activo_local = 1;


-- ---------------------------------------------------------------------
-- AUSENCIAS
-- Sin esto, la rotación asigna a quien no está, nadie acusa recibo,
-- y a las dos horas escala todo.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_ausencias (
    ausencia_id    INTEGER PRIMARY KEY,
    persona_id     TEXT NOT NULL REFERENCES bertok_ops_personas(persona_id),
    desde          TEXT NOT NULL,          -- AAAA-MM-DD inclusive
    hasta          TEXT NOT NULL,          -- AAAA-MM-DD inclusive
    motivo         TEXT,
    registrado_por TEXT REFERENCES bertok_ops_personas(persona_id),
    registrado_en  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    CHECK (hasta >= desde)
);

CREATE INDEX IF NOT EXISTS ix_ops_ausencias_persona
    ON bertok_ops_ausencias (persona_id, desde, hasta);


-- ---------------------------------------------------------------------
-- TURNOS
-- Rotaciones. El turno define QUIÉN NACE DUEÑO, no quién queda dueño:
-- un hallazgo nacido el martes se queda con el dueño del martes.
-- participantes: JSON array ordenado de persona_id.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_turnos (
    turno_id      TEXT PRIMARY KEY,
    nombre        TEXT NOT NULL,
    participantes TEXT NOT NULL,           -- JSON: ["p1","p2",...]
    cadencia      TEXT NOT NULL CHECK (cadencia IN ('diaria','ciclo')),
    dias_ciclo    INTEGER,                 -- sólo si cadencia='ciclo'
    fecha_inicio  TEXT NOT NULL,           -- AAAA-MM-DD, ancla de la rotación
    activo        INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
    creado_en     TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    CHECK (cadencia <> 'ciclo' OR dias_ciclo IS NOT NULL)
);


-- ---------------------------------------------------------------------
-- PROCESOS
-- Un renglón por tarjeta. Sólo Gerardo modifica esta tabla (stop condition).
-- Cambiar un umbral acá puede autodesactivar el sistema en silencio.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_procesos (
    proceso_id        TEXT PRIMARY KEY,
    nombre            TEXT NOT NULL,
    tipo              TEXT NOT NULL
                           CHECK (tipo IN ('informativa','accion','calendario')),
    familia           TEXT NOT NULL DEFAULT 'excepcion'
                           CHECK (familia IN ('excepcion','compromiso')),

    -- Compuerta de madurez. Ninguna tarjeta nace en 'completa'.
    madurez           TEXT NOT NULL DEFAULT 'sombra'
                           CHECK (madurez IN ('sombra','visible_sin_push','completa','apagada')),

    -- Asignación: fija, por turno, o derivada del dato.
    modo_asignacion   TEXT NOT NULL DEFAULT 'fijo'
                           CHECK (modo_asignacion IN ('fijo','turno','por_dato')),
    dueno_id          TEXT REFERENCES bertok_ops_personas(persona_id),
    suplente_id       TEXT REFERENCES bertok_ops_personas(persona_id),
    revisor_id        TEXT REFERENCES bertok_ops_personas(persona_id),
    turno_id          TEXT REFERENCES bertok_ops_turnos(turno_id),
    escala_a_proceso  TEXT REFERENCES bertok_ops_procesos(proceso_id),

    -- Umbrales en minutos. NULL = no aplica (p. ej. prioridad por proyección).
    origen_umbral     TEXT NOT NULL DEFAULT 'derivado'
                           CHECK (origen_umbral IN ('externo','politica','derivado','proyeccion')),
    umbral_visible    INTEGER,
    umbral_aviso      INTEGER,
    umbral_escalado   INTEGER,

    -- Ventana de vigencia. dias: L M X J V S D presentes = corre ese día.
    cadencia_min      INTEGER NOT NULL DEFAULT 1440,
    ventana_dias      TEXT    NOT NULL DEFAULT 'LMXJVSD',
    ventana_desde     TEXT,                -- 'HH:MM'
    ventana_hasta     TEXT,                -- 'HH:MM'
    respeta_feriados  INTEGER NOT NULL DEFAULT 1 CHECK (respeta_feriados IN (0,1)),

    apta_tv           INTEGER NOT NULL DEFAULT 1 CHECK (apta_tv IN (0,1)),
    linea_corte       TEXT,                -- AAAA-MM-DD: no toma hechos previos
    tope_en_curso     INTEGER,             -- NULL = sin tope (arrancar así)

    notas             TEXT,
    creado_en         TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    actualizado_en    TEXT NOT NULL DEFAULT (datetime('now','localtime')),

    -- Coherencia de la asignación
    CHECK (modo_asignacion <> 'fijo'  OR dueno_id IS NOT NULL),
    CHECK (modo_asignacion <> 'turno' OR turno_id IS NOT NULL)
);


-- ---------------------------------------------------------------------
-- CORRIDAS
-- Una fila por ejecución de cada detector. Es lo que permite saber que
-- el sistema está ciego. Retención: 90 días de detalle.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_corridas (
    corrida_id   INTEGER PRIMARY KEY,
    proceso_id   TEXT NOT NULL REFERENCES bertok_ops_procesos(proceso_id),
    iniciada_en  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    terminada_en TEXT,
    duracion_ms  INTEGER,
    detectados   INTEGER NOT NULL DEFAULT 0,
    nacidos      INTEGER NOT NULL DEFAULT 0,
    cerrados     INTEGER NOT NULL DEFAULT 0,
    ok           INTEGER NOT NULL DEFAULT 0 CHECK (ok IN (0,1)),
    error        TEXT,
    datos_al     TEXT                       -- antigüedad de la fuente leída
);

CREATE INDEX IF NOT EXISTS ix_ops_corridas_proceso
    ON bertok_ops_corridas (proceso_id, iniciada_en DESC);


-- ---------------------------------------------------------------------
-- HALLAZGOS
-- VERDAD DEL ESTADO ACTUAL. No es una reconstrucción del log de eventos.
--
-- clave_natural es estable y derivada del hecho real, no de la corrida.
-- Un hallazgo archivado que reaparece NO revive: nace uno nuevo enlazado
-- al anterior por hallazgo_previo_id. Por eso la unicidad es parcial:
-- sólo puede haber una clave viva a la vez.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_hallazgos (
    hallazgo_id       INTEGER PRIMARY KEY,
    proceso_id        TEXT NOT NULL REFERENCES bertok_ops_procesos(proceso_id),
    clave_natural     TEXT NOT NULL,
    subtipo           TEXT,                 -- p.ej. 'ml' | 'offline'

    estado            TEXT NOT NULL DEFAULT 'detectado'
                           CHECK (estado IN ('detectado','visible','asignado',
                                             'en_curso','en_revision',
                                             'resuelto','archivado')),
    prioridad         INTEGER NOT NULL DEFAULT 0,
    nivel             TEXT NOT NULL DEFAULT 'oculto'
                           CHECK (nivel IN ('oculto','gris','verde','amarillo','rojo')),

    -- El reloj. nacido_en NUNCA se modifica: es la base de la antigüedad.
    nacido_en         TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    visible_desde     TEXT,
    vence_en          TEXT,                 -- límite duro, si lo hay
    datos_al          TEXT NOT NULL,        -- de cuándo son los datos de origen

    asignado_a        TEXT REFERENCES bertok_ops_personas(persona_id),
    asignado_en       TEXT,
    acusado_en        TEXT,                 -- el escalado corre desde acá
    tomado_en         TEXT,

    pospuesto_hasta   TEXT,
    posposiciones     INTEGER NOT NULL DEFAULT 0,
    nivel_escalado    INTEGER NOT NULL DEFAULT 0 CHECK (nivel_escalado BETWEEN 0 AND 3),

    resuelto_en       TEXT,
    resuelto_motivo   TEXT CHECK (resuelto_motivo IN ('automatico','confirmado')),
    resuelto_por      TEXT REFERENCES bertok_ops_personas(persona_id),
    nivel_prueba      TEXT,                 -- A|B|C|D en cierres con prueba
    archivado_en      TEXT,

    -- Para scorecards por tercero (expreso, cliente, proveedor).
    contraparte_tipo  TEXT,
    contraparte_id    TEXT,

    corrida_id        INTEGER REFERENCES bertok_ops_corridas(corrida_id),
    hallazgo_previo_id INTEGER REFERENCES bertok_ops_hallazgos(hallazgo_id),
    datos             TEXT NOT NULL DEFAULT '{}',   -- JSON propio de la tarjeta

    -- Un hallazgo resuelto tiene que decir por qué.
    CHECK (estado NOT IN ('resuelto','archivado') OR resuelto_motivo IS NOT NULL)
);

-- Una sola clave natural viva a la vez; las archivadas no cuentan.
CREATE UNIQUE INDEX IF NOT EXISTS ux_ops_hallazgos_clave_viva
    ON bertok_ops_hallazgos (clave_natural)
    WHERE estado <> 'archivado';

CREATE INDEX IF NOT EXISTS ix_ops_hallazgos_tablero
    ON bertok_ops_hallazgos (estado, prioridad DESC);
CREATE INDEX IF NOT EXISTS ix_ops_hallazgos_proceso
    ON bertok_ops_hallazgos (proceso_id, estado);
CREATE INDEX IF NOT EXISTS ix_ops_hallazgos_asignado
    ON bertok_ops_hallazgos (asignado_a, estado);
CREATE INDEX IF NOT EXISTS ix_ops_hallazgos_contraparte
    ON bertok_ops_hallazgos (contraparte_tipo, contraparte_id, nivel_prueba);


-- ---------------------------------------------------------------------
-- EVENTOS
-- REGISTRO DE AUDITORÍA. Append-only, y no por convención: los triggers
-- de abajo hacen fallar cualquier UPDATE o DELETE.
--
-- version: nunca cambiarle el significado a un tipo de evento existente.
-- Si cambia, se crea un tipo nuevo.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_eventos (
    evento_id   INTEGER PRIMARY KEY,
    hallazgo_id INTEGER REFERENCES bertok_ops_hallazgos(hallazgo_id),
    proceso_id  TEXT REFERENCES bertok_ops_procesos(proceso_id),
    tipo        TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    persona_id  TEXT REFERENCES bertok_ops_personas(persona_id),
    ocurrido_en TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    datos       TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_ops_eventos_hallazgo
    ON bertok_ops_eventos (hallazgo_id, ocurrido_en);
CREATE INDEX IF NOT EXISTS ix_ops_eventos_persona
    ON bertok_ops_eventos (persona_id, ocurrido_en);
CREATE INDEX IF NOT EXISTS ix_ops_eventos_tipo
    ON bertok_ops_eventos (tipo, ocurrido_en);

CREATE TRIGGER IF NOT EXISTS tr_ops_eventos_sin_update
BEFORE UPDATE ON bertok_ops_eventos
BEGIN
    SELECT RAISE(ABORT, 'bertok_ops_eventos es append-only: no se actualiza');
END;

CREATE TRIGGER IF NOT EXISTS tr_ops_eventos_sin_delete
BEFORE DELETE ON bertok_ops_eventos
BEGIN
    SELECT RAISE(ABORT, 'bertok_ops_eventos es append-only: no se borra');
END;

-- Una persona no se borra, se marca inactiva.
CREATE TRIGGER IF NOT EXISTS tr_ops_personas_sin_delete
BEFORE DELETE ON bertok_ops_personas
BEGIN
    SELECT RAISE(ABORT, 'Una persona no se borra: se marca inactiva');
END;

-- nacido_en es la base de la antigüedad y no se toca nunca.
CREATE TRIGGER IF NOT EXISTS tr_ops_hallazgos_nacido_en_inmutable
BEFORE UPDATE OF nacido_en ON bertok_ops_hallazgos
WHEN NEW.nacido_en <> OLD.nacido_en
BEGIN
    SELECT RAISE(ABORT, 'nacido_en es inmutable: es la base de la antigüedad');
END;


-- ---------------------------------------------------------------------
-- FRESCURA
-- Verde sobre datos de anteayer es peor que no tener pantalla.
-- Un detector que falla deja la tarjeta en gris, nunca en verde.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_frescura (
    fuente         TEXT PRIMARY KEY,
    descripcion    TEXT,
    actualizado_en TEXT,                    -- última actualización de la fuente
    tolerancia_min INTEGER NOT NULL,
    verificado_en  TEXT
);


-- ---------------------------------------------------------------------
-- CALENDARIO
-- Feriados nacionales y días no laborables. Carga anual manual (~20 filas).
-- Sin esto, la fecha de recolección de Full cae en feriado y son horas extra.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bertok_ops_calendario (
    fecha       TEXT PRIMARY KEY,           -- AAAA-MM-DD
    tipo        TEXT NOT NULL
                     CHECK (tipo IN ('feriado','no_laborable','cierre_empresa')),
    descripcion TEXT
);


-- =====================================================================
-- Semilla mínima: tolerancias de frescura por fuente (punto 19 del plan).
-- =====================================================================
INSERT OR IGNORE INTO bertok_ops_frescura (fuente, descripcion, tolerancia_min) VALUES
    ('picking.db',         'Operación del depósito. Local y viva.',              15),
    ('ML.db',              'Fuente única de Mercado Libre.',                     60),
    ('contabilium_excel',  'Excel del scraper. Tolerancia = cadencia + margen.', 1560),
    ('odoo',               'Padrón de empleados. Sync cada 6 h.',                480);
```


## guarda_alcance.py

```python
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
```


## crear_ops_db.py

```python
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
```


## probar_guarda.py

```python
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
```


## backup_bases.py

```python
"""
Centro de Operaciones Bertok — backup de ops.db y picking.db.

POR QUÉ NO ALCANZA UN «copy»
    Una SQLite en modo WAL usa tres archivos (.db, .db-wal, .db-shm) que
    deben estar coherentes entre sí. Copiar el .db con transacciones en
    vuelo produce una base incompleta, y NO SE NOTA hasta el día que hace
    falta. Por eso acá se usa VACUUM INTO, que genera un archivo único,
    consistente y ya cerrado, sin frenar la operación.

Qué hace, en orden:
    1. VACUUM INTO sobre un archivo nuevo (la base sigue en uso).
    2. Verifica el resultado: integrity_check + conteo de filas.
       Si no verifica, NO reemplaza el backup anterior.
    3. Lo deja en diario/, y asegura una copia semanal de la semana ISO.
    4. Poda: 7 diarios + 4 semanales. Nunca pisa un archivo existente.
    5. Escribe ultimo_backup.json, para que el Centro pueda avisar si el
       backup dejó de correr.

Uso:
    python backup_bases.py
    python backup_bases.py --destino "D:\\OneDrive\\Backups"
    python backup_bases.py --fecha 2026-09-12      # para probar la rotación

Se programa como tarea de Windows, una vez por día, en horario no operativo.
Código de salida distinto de 0 = algo falló y hay que mirarlo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# --- configuración ----------------------------------------------------

BASES = {
    "ops":     Path(r"C:\Sistema de Picking\ops.db"),
    "picking": Path(r"C:\Sistema de Picking\picking.db"),
}

DESTINO_POR_DEFECTO = Path(
    r"C:\Users\Gerardo\Ruky S.R.L\Bertok - Documentos"
    r"\17 - Centro de Operaciones\Backups"
)

RETENER_DIARIOS = 7
RETENER_SEMANALES = 4

# VACUUM INTO existe desde SQLite 3.27 (2019).
SQLITE_MINIMO = (3, 27, 0)


class BackupFallido(Exception):
    pass


# --- utilidades -------------------------------------------------------

def _version_sqlite_ok() -> bool:
    return tuple(int(x) for x in sqlite3.sqlite_version.split(".")) >= SQLITE_MINIMO


def _tablas_y_filas(ruta: Path) -> dict[str, int]:
    """Cuenta filas por tabla. Sirve para comparar origen contra copia."""
    cx = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    try:
        tablas = [r[0] for r in cx.execute(
            "SELECT name FROM sqlite_master "
            " WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {t: cx.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                for t in tablas}
    finally:
        cx.close()


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def _verificar(copia: Path) -> dict[str, int]:
    """
    Un backup no verificado no es un backup. Se abre la copia, se corre
    integrity_check y se cuentan las filas. Si algo falla, se descarta.

    OJO CON EL ALCANCE DE integrity_check: recorre la estructura del árbol,
    pero NO detecta toda la corrupción. Medido sobre esta misma base: con
    3.000 bytes ensuciados en páginas libres del medio del archivo, devolvió
    «ok» igual. Por eso además se guarda un SHA-256 al lado de cada copia
    (.sha256): eso sí detecta cualquier byte cambiado, que es lo que hace
    falta cuando el backup vive en una carpeta sincronizada.
    """
    cx = sqlite3.connect(f"file:{copia}?mode=ro", uri=True)
    try:
        estado = cx.execute("PRAGMA integrity_check").fetchone()[0]
        if estado != "ok":
            raise BackupFallido(f"integrity_check devolvió «{estado}»")
    finally:
        cx.close()
    return _tablas_y_filas(copia)


def _podar(carpeta: Path, patron: str, retener: int) -> list[str]:
    archivos = sorted(carpeta.glob(patron))
    sobrantes = archivos[:-retener] if len(archivos) > retener else []
    for a in sobrantes:
        a.unlink()
        firma = a.with_suffix(a.suffix + ".sha256")
        if firma.exists():
            firma.unlink()
    return [a.name for a in sobrantes]


# --- backup de una base ----------------------------------------------

def respaldar(nombre: str, origen: Path, destino: Path,
              momento: datetime) -> dict:
    resultado: dict = {"base": nombre, "origen": str(origen), "ok": False}

    if not origen.exists():
        resultado["error"] = "la base de origen no existe"
        return resultado

    carpeta_diaria = destino / nombre / "diario"
    carpeta_semanal = destino / nombre / "semanal"
    carpeta_diaria.mkdir(parents=True, exist_ok=True)
    carpeta_semanal.mkdir(parents=True, exist_ok=True)

    sello = momento.strftime("%Y-%m-%d_%H%M")
    anio, semana, _ = momento.isocalendar()
    destino_diario = carpeta_diaria / f"{nombre}_{sello}.db"
    destino_semanal = carpeta_semanal / f"{nombre}_{anio}-W{semana:02d}.db"

    # Nunca pisar: si algo se corrompió el lunes y se nota el jueves,
    # sobrescribir habría destruido las copias buenas.
    if destino_diario.exists():
        resultado["error"] = f"ya existe {destino_diario.name}, no se pisa"
        return resultado

    parcial = destino_diario.with_suffix(".db.parcial")
    if parcial.exists():
        parcial.unlink()

    try:
        # El conteo de referencia se toma ANTES del VACUUM. Si se tomara
        # después, con la base en uso el origen siempre tendría más filas
        # que la copia y toda corrida daría falso negativo — que es
        # exactamente el escenario para el que existe este backup.
        filas_antes = _tablas_y_filas(origen)

        # VACUUM INTO: archivo único, consistente, cerrado. Sin frenar la base.
        cx = sqlite3.connect(str(origen))
        try:
            cx.execute("PRAGMA busy_timeout = 30000")
            cx.execute("VACUUM INTO ?", (str(parcial),))
        finally:
            cx.close()

        filas_copia = _verificar(parcial)

        faltantes = [t for t in filas_antes if t not in filas_copia]
        if faltantes:
            raise BackupFallido(f"faltan tablas en la copia: {faltantes}")

        # La copia es una foto posterior al conteo de referencia: puede
        # tener filas de más (entraron durante el VACUUM), nunca de menos.
        cortas = {t: (filas_antes[t], filas_copia[t])
                  for t in filas_antes if filas_copia[t] < filas_antes[t]}
        if cortas:
            raise BackupFallido(f"la copia tiene menos filas que el origen "
                                f"antes de copiar: {cortas}")

        parcial.rename(destino_diario)

        # Firma del archivo final. Es lo único que detecta un byte cambiado
        # después de la copia: sincronización a medias, bit-rot, escritura
        # parcial. integrity_check no llega ahí.
        firma = sha256(destino_diario)
        destino_diario.with_suffix(".db.sha256").write_text(
            f"{firma}  {destino_diario.name}\n", encoding="utf-8")

        if not destino_semanal.exists():
            shutil.copy2(destino_diario, destino_semanal)
            destino_semanal.with_suffix(".db.sha256").write_text(
                f"{firma}  {destino_semanal.name}\n", encoding="utf-8")
            resultado["semanal_creado"] = destino_semanal.name

        resultado.update(
            ok=True,
            archivo=str(destino_diario),
            tamano_mb=round(destino_diario.stat().st_size / 1_048_576, 2),
            tablas=len(filas_copia),
            filas=sum(filas_copia.values()),
            sha256=firma,
            podados_diarios=_podar(carpeta_diaria, f"{nombre}_*.db", RETENER_DIARIOS),
            podados_semanales=_podar(carpeta_semanal, f"{nombre}_*.db", RETENER_SEMANALES),
        )

    except Exception as e:
        # Si algo falló, el backup anterior sigue intacto: nunca se tocó.
        if parcial.exists():
            parcial.unlink()
        resultado["error"] = f"{type(e).__name__}: {e}"

    return resultado


# --- principal --------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Backup de las bases del Centro")
    p.add_argument("--destino", type=Path, default=DESTINO_POR_DEFECTO)
    p.add_argument("--fecha", help="AAAA-MM-DD, para probar la rotación")
    p.add_argument("--base", action="append",
                   help="nombre=ruta, repetible; reemplaza la config")
    args = p.parse_args(argv)

    if not _version_sqlite_ok():
        print(f"\n  ABORTADO: SQLite {sqlite3.sqlite_version} no soporta "
              f"VACUUM INTO (hace falta {'.'.join(map(str, SQLITE_MINIMO))}+).\n"
              f"  Sin VACUUM INTO no hay backup confiable: copiar el .db a mano\n"
              f"  con el WAL activo produce una base incompleta.\n")
        return 2

    bases = BASES
    if args.base:
        bases = {}
        for spec in args.base:
            nombre, _, ruta = spec.partition("=")
            bases[nombre] = Path(ruta)

    momento = (datetime.strptime(args.fecha, "%Y-%m-%d")
               if args.fecha else datetime.now())

    print(f"\n  Backup — {momento:%Y-%m-%d %H:%M}")
    print(f"  Destino: {args.destino}")
    print("  " + "-" * 58)

    resultados = [respaldar(n, r, args.destino, momento) for n, r in bases.items()]

    for r in resultados:
        if r["ok"]:
            print(f"  OK    {r['base']:<8} {r['tamano_mb']:>7.2f} MB   "
                  f"{r['tablas']} tablas · {r['filas']} filas")
            if r.get("semanal_creado"):
                print(f"        semanal: {r['semanal_creado']}")
            for tipo in ("podados_diarios", "podados_semanales"):
                if r[tipo]:
                    print(f"        podados ({tipo.split('_')[1]}): "
                          f"{', '.join(r[tipo])}")
        else:
            print(f"  FALLA {r['base']:<8} {r['error']}")

    # Para que el Centro pueda avisar si el backup dejó de correr.
    args.destino.mkdir(parents=True, exist_ok=True)
    (args.destino / "ultimo_backup.json").write_text(
        json.dumps({"momento": momento.isoformat(timespec="seconds"),
                    "resultados": resultados}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    fallidos = [r for r in resultados if not r["ok"]]
    if fallidos:
        print(f"\n  {len(fallidos)} base(s) sin respaldar. REVISAR.\n")
        return 1

    print("\n  Todas las bases respaldadas y verificadas.")
    print("  Recordatorio: la restauración de prueba va una vez por mes "
          "(restaurar_prueba.py).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


## restaurar_prueba.py

```python
"""
Centro de Operaciones Bertok — restauración de prueba.

    UN BACKUP QUE NUNCA SE RESTAURÓ NO ES UN BACKUP.

Se corre UNA VEZ POR MES. Cinco minutos, y es la diferencia entre tener
backup y creer que se tiene.

Qué hace:
    1. Toma el backup más reciente de cada base.
    2. Lo copia a una carpeta descartable (nunca toca la base real).
    3. Lo abre, corre integrity_check y foreign_key_check.
    4. Cuenta filas y las compara contra la base viva.
    5. Verifica que el esquema esté completo: tablas, vistas y triggers.
    6. Informa la antigüedad del backup: uno de hace diez días no sirve.

Uso:
    python restaurar_prueba.py
    python restaurar_prueba.py --destino "D:\\OneDrive\\Backups"

Al terminar hay que anotar el resultado en BITACORA.md, con fecha y quién.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from backup_bases import BASES, DESTINO_POR_DEFECTO, _tablas_y_filas, sha256

VERDE, ROJO, AMARILLO, GRIS, FIN = (
    "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m")

ANTIGUEDAD_ACEPTABLE_H = 30      # un backup diario no debería pasar de esto


def _mas_reciente(carpeta: Path, nombre: str) -> Path | None:
    archivos = sorted(carpeta.glob(f"{nombre}_*.db"))
    return archivos[-1] if archivos else None


def _inventario(ruta: Path) -> dict:
    cx = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    try:
        return {
            tipo: sorted(r[0] for r in cx.execute(
                "SELECT name FROM sqlite_master "
                " WHERE type=? AND name NOT LIKE 'sqlite_%'", (tipo,)))
            for tipo in ("table", "view", "trigger", "index")
        }
    finally:
        cx.close()


def probar(nombre: str, viva: Path, destino: Path, taller: Path) -> bool:
    print(f"\n  {nombre}")
    print("  " + "-" * 58)

    carpeta = destino / nombre / "diario"
    backup = _mas_reciente(carpeta, nombre) if carpeta.exists() else None
    if backup is None:
        print(f"  {ROJO}FALLA{FIN} no hay ningún backup diario en {carpeta}")
        return False

    edad_h = (datetime.now() - datetime.fromtimestamp(
        backup.stat().st_mtime)).total_seconds() / 3600
    marca = VERDE if edad_h <= ANTIGUEDAD_ACEPTABLE_H else AMARILLO
    print(f"  Backup:  {backup.name}   {GRIS}({backup.stat().st_size/1_048_576:.2f} MB){FIN}")
    print(f"  Antigüedad: {marca}{edad_h:.1f} h{FIN}"
          + (f"   {AMARILLO}← el backup diario dejó de correr{FIN}"
             if edad_h > ANTIGUEDAD_ACEPTABLE_H else ""))

    ok = True

    # PRIMERO el checksum: es lo único que detecta un byte cambiado desde
    # que se creó la copia. integrity_check no llega ahí — medido: con
    # 3.000 bytes ensuciados en páginas libres devuelve «ok» igual.
    firma_guardada = backup.with_suffix(".db.sha256")
    if firma_guardada.exists():
        esperado = firma_guardada.read_text(encoding="utf-8").split()[0]
        obtenido = sha256(backup)
        coincide = esperado == obtenido
        print(f"  SHA-256: {VERDE + 'coincide' if coincide else ROJO + 'NO COINCIDE'}{FIN}"
              f"   {GRIS}{obtenido[:16]}…{FIN}")
        if not coincide:
            print(f"  {ROJO}        El archivo cambió desde que se creó."
                  f" No sirve como backup.{FIN}")
            print(f"  {GRIS}        esperado {esperado[:16]}…{FIN}")
        ok &= coincide
    else:
        print(f"  {AMARILLO}SHA-256: sin firma guardada (backup anterior "
              f"a esta versión del script){FIN}")

    # Restaurar de verdad: copiar a otro lado y abrir esa copia.
    copia = taller / f"restaurado_{nombre}.db"
    shutil.copy2(backup, copia)

    cx = sqlite3.connect(str(copia))
    try:
        estado = cx.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"  integrity_check: {VERDE if estado=='ok' else ROJO}{estado}{FIN}")
        ok &= estado == "ok"

        fks = cx.execute("PRAGMA foreign_key_check").fetchall()
        print(f"  foreign_key_check: "
              f"{VERDE + 'sin violaciones' if not fks else ROJO + str(len(fks)) + ' violaciones'}{FIN}")
        ok &= not fks
    finally:
        cx.close()

    inv_backup = _inventario(copia)
    if viva.exists():
        inv_viva = _inventario(viva)
        for tipo in ("table", "view", "trigger"):
            faltan = set(inv_viva[tipo]) - set(inv_backup[tipo])
            if faltan:
                print(f"  {ROJO}FALLA{FIN} faltan {tipo}s en el backup: {sorted(faltan)}")
                ok = False
        if ok:
            print(f"  Esquema: {VERDE}completo{FIN}   "
                  f"{GRIS}{len(inv_backup['table'])} tablas · "
                  f"{len(inv_backup['view'])} vistas · "
                  f"{len(inv_backup['trigger'])} triggers{FIN}")

        filas_v, filas_b = _tablas_y_filas(viva), _tablas_y_filas(copia)
        perdidas = {t: (filas_v[t], filas_b.get(t, 0))
                    for t in filas_v if filas_b.get(t, 0) < filas_v[t]}
        total_b = sum(filas_b.values())
        if perdidas:
            print(f"  {AMARILLO}Filas: el backup tiene menos que la base viva{FIN}")
            for t, (v, b) in sorted(perdidas.items()):
                print(f"        {t}: viva {v} · backup {b}")
            print(f"  {GRIS}  (esperable si hubo actividad desde el backup;"
                  f" alarmante si la diferencia es grande){FIN}")
        else:
            print(f"  Filas: {VERDE}{total_b} en el backup, ninguna tabla corta{FIN}")
    else:
        print(f"  {AMARILLO}La base viva no existe: sólo se validó el backup.{FIN}")

    if ok:
        print(f"  {VERDE}El backup abre, está íntegro y trae el esquema completo.{FIN}")
    return ok


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Restauración de prueba mensual")
    p.add_argument("--destino", type=Path, default=DESTINO_POR_DEFECTO)
    p.add_argument("--base", action="append", help="nombre=ruta, repetible")
    args = p.parse_args(argv)

    bases = BASES
    if args.base:
        bases = {}
        for spec in args.base:
            nombre, _, ruta = spec.partition("=")
            bases[nombre] = Path(ruta)

    taller = Path(tempfile.mkdtemp(prefix="restauracion_"))
    print(f"\n  RESTAURACIÓN DE PRUEBA — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"  {GRIS}Taller descartable: {taller}{FIN}")
    print(f"  {GRIS}Las bases vivas no se tocan en ningún momento.{FIN}")

    resultados = {n: probar(n, r, args.destino, taller) for n, r in bases.items()}

    print("\n  " + "=" * 58)
    fallidas = [n for n, ok in resultados.items() if not ok]
    if fallidas:
        print(f"  {ROJO}NO RESTAURAN: {', '.join(fallidas)}{FIN}")
        print("  Hay que arreglarlo hoy: el backup no sirve como está.\n")
        return 1
    print(f"  {VERDE}Todas las bases restauran correctamente.{FIN}")
    print("  Anotar en BITACORA.md: fecha, quién lo corrió y este resultado.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


---

*Fin del traspaso. Generado el 09/09/2026.*
