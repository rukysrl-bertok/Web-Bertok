# Centro de Operaciones Bertok — Reglas del módulo

> **En la pantalla del equipo este sistema se llama «DEJÁ DE ACORDARTE DE TODO».**
> Ese es el nombre que ve la gente. «Centro de Operaciones» es el nombre técnico.

Este archivo son **las reglas**. El registro de sesiones está en `BITACORA.md`.
Arquitectura completa: ver el Master Plan (v5) del 05/09/2026.

---

## 0. Estado del módulo

| | |
|---|---|
| **Estado** | 🔴 Sin implementar. Fase 0 sin arrancar. |
| **Dueños del módulo** | Gerardo y Antonella |
| **Servidor** | PC dedicada, siempre encendida (a definir hostname) |
| **Bases** | `C:\Sistema de Picking\ops.db` — **fuera de OneDrive** |
| **Scripts** | `17 - Centro de Operaciones\.claude\sistema\` |

**Nada de este módulo está en 🟢.** Todo el catálogo está en 🔴 hasta que una persona lo use en la operación real.

---

## 1. Qué es y qué NO es

**Es** una capa de detección, priorización, asignación, control y registro sobre procesos que ya ocurren.

**No es:**
- **No es el sistema operativo de Bertok.** Mercado Libre, Contabilium y Picking siguen haciendo las cosas.
- **No es la capa analítica.** Bertok BI analiza lo que pasó; el Centro actúa sobre lo que está pasando.
- **No recalcula nada** que ya calcule otro módulo.
- **No es un tablero de métricas.** Si un número no dispara una acción, no va.

---

## 2. Reglas duras — no se negocian sin OK de Gerardo

1. **El Centro sólo lee de los sistemas ajenos. Lo único que escribe es `ops.db`, y sólo tablas con prefijo `bertok_ops_*`.** Sin excepciones. Se evaluó una (crear el pedido de reposición Full dentro de Picking) y **se rechazó**.
2. **Guarda de alcance programática.** Toda escritura fuera del prefijo se bloquea *a nivel código*, no por convención. Se prueba con un set de sentencias destructivas que deben fallar todas — igual que en Bertok BI.
3. **No duplicar cálculos.** Rentabilidad, costo por SKU, demanda, punto de quiebre y precios ya están calculados y validados contra facturación real. Se **consumen**, no se rehacen.
4. **Antes de construir una tarjeta, probar la jerarquía de prevención** (§6). La tarjeta existe sólo para lo que no se puede prevenir.
5. **Ninguna tarjeta se construye sin ficha de racionalización completa** (§7) ni sin **dueño y suplente con nombre**.
6. **Toda tarjeta nueva arranca vacía.** Línea de corte: sólo toma hechos desde la fecha de encendido. La deuda vieja no entra a la pantalla.
7. **Modo sombra obligatorio**, mínimo 2 ciclos completos del proceso, antes de mostrar nada.
8. **Informativa por defecto.** Cualquier tarjeta de acción se justifica por escrito: qué es exactamente lo que el sistema no puede observar.
9. **Una tarjeta = un proceso.** Cuando quiere controlar dos cosas, son dos tarjetas.
10. **No existe el estado `descartado`.** Un hallazgo tiene dos salidas: se resuelve, o el detector deja de verlo. Si un detector da falsos positivos, **se apaga la tarjeta, no el síntoma.**
11. **Una persona nunca se borra, se marca inactiva.**
12. **Nada es 🟢 hasta que una persona lo usó en la operación real.**
13. **Todo en español**, incluida la terminología técnica.
14. **Sin dependencias nuevas.** Stack idéntico a Picking: Python + FastAPI + SQLite + HTML/JS sin frameworks.

---

## 3. Stop conditions — requieren OK explícito de Gerardo

- Cambiar **umbrales, dueños, suplentes, cadencias** o cualquier parámetro de `bertok_ops_procesos`.
- **Encender el push** (WhatsApp) de una tarjeta.
- Cualquier **escritura fuera de `ops.db`**.
- Tocar **Picking, `ML.db`, `picking.db`, Contabilium, Odoo** o cualquier módulo ajeno.
- **Instalar dependencias.**
- Registrar **datos sensibles**: correctivos, comercio exterior, cuenta FIMA.
- **Borrar archivos.**
- Cambios que crucen módulos.

---

## 4. Confidencialidad — reglas, no recomendaciones

| Tarjeta | Regla |
|---|---|
| **Comercio exterior** | **NUNCA en la TV.** Contiene la distinción PI Real / PI Declarada. Modo usuario, acceso sólo Gerardo y Antonella. |
| **Rendición de cuentas** | El Centro registra **que el viernes hay un informe para Fernando y si se hizo**. **No registra montos, conceptos ni conciliaciones**, y no se construye detección ni seguimiento de esos importes. |
| **Cobranzas** | No va a la TV. Nombres de clientes y montos en una pantalla por la que pasa gente de afuera. |
| **Correctivos** | Sólo que hubo uno, fecha y referencia. El detalle y el monto van al legajo, fuera del Centro. Visible sólo para Gerardo. **Pendiente: consulta al contador/abogado antes de implementar ese campo** (Ley 25.326). |

> La TV está en la oficina grande donde trabajan los vendedores y se arman los pedidos. Muestra todas las tarjetas marcadas **aptas para TV**. En cada PC, la persona logueada ve **lo asignado a ella más todo lo de los procesos de los que es dueña**.

---

## 5. El motor — no re-derivar esto

**Una tarjeta son dos cosas separadas:**

- **Detector**: función pura. Lee las fuentes de solo lectura y devuelve 0..N *hallazgos*. No escribe, no avisa, no recuerda. Idempotente.
- **Estado**: vive en `ops.db` y es lo único que recuerda.

**La clave natural es el corazón.** Cada hallazgo trae una clave estable derivada del hecho real, no de la corrida:

```
cierre:remito:18432
despacho:2026-09-05:flex
full:ciclo:2026-09-16:armar
ads:aviso:MLA8823:quiebre
cex:container:CT-0042:saldo
```

- Clave que ya existía → mismo problema. Se actualizan datos, **se conserva la fecha de nacimiento**.
- Clave nueva → nace un hallazgo.
- Clave que desapareció → cierra solo, motivo `automático`.

**Sin clave natural no hay antigüedad, y sin antigüedad no hay prioridad creciente, ni escalado, ni auditoría.**

### Ciclo de vida

```
detectado → visible → asignado → en_curso → [en_revisión] → resuelto → archivado
```

- `detectado` ≠ `visible`. Esa separación evita que la pantalla grite todo el tiempo.
- **Nace asignado, nunca huérfano.** Si el asignado se dio de baja → dueño → suplente → Gerardo.
- `resuelto` lleva motivo obligatorio: `automático` o `confirmado` (con nombre).
- Un hallazgo cerrado que reaparece **no revive**: nace uno nuevo, enlazado al anterior.
- `en_curso` sin actividad al cierre del día vuelve a `asignado`.

### Posponer

Sólo el responsable asignado, desde su PC logueado. **A la tercera vez consecutiva sobre el mismo hallazgo, se notifica a Gerardo.**

### Turnos rotativos

| Proceso | Rotan | Cadencia |
|---|---|---|
| Despachos del día | Facundo ↔ Federico | Diaria |
| Preguntas ML | Abril → Facundo → Federico | Diaria |
| Reposición a Full | Facundo ↔ Federico | Por ciclo (~15 días) |

- **El turno define quién nace dueño, no quién queda dueño.** Un hallazgo del martes se queda con el dueño del martes aunque siga abierto el jueves.
- **Hay que poder marcar ausencias**, o la rotación asigna a alguien que no está y todo escala.

### Asignación por dato

> **La asignación puede venir de configuración o venir del dato. Cuando puede venir del dato, siempre es mejor.**

En Pendientes de cierre canal ML, el responsable sale de `picking.db`: quien armó ese paquete. Escala al dueño del turno de Despachos de ese día.

### Prioridad

Verde/amarillo/rojo son **salidas**, no estados. Insumos: **tiempo restante, antigüedad, magnitud**. Es **monótona**: si nadie hace nada, no baja. **El orden en pantalla lo decide ella, no la maqueta.**

Para tarjetas con reloj duro, la prioridad sale de **la proyección**, no del conteo: *«al ritmo actual no llegás»*. El ritmo sale de `picking.db`, **mediana de los últimos 30 días, no promedio**.

---

## 6. Jerarquía de prevención — filtro obligatorio

> **La inspección no previene defectos. Sólo los encuentra después.** (Shingo, TPS)

| | Nivel | |
|---|---|---|
| 1 | Eliminación | El error no puede ocurrir |
| 2 | Reemplazo | Se cambia el proceso |
| 3 | Facilitación | Tan fácil hacerlo bien que casi nadie falla |
| 4 | **Detección** | **Acá vive el Centro** |
| 5 | Mitigación | Se limita el daño |

**Antes de construir una tarjeta hay que probar los niveles 1 a 3.** El Centro usa por defecto la cuarta herramienta más fuerte de cinco: eso obliga a preguntar antes si hay una mejor.

**Corolario:** *un bloqueo que impide la acción incorrecta pero no ofrece camino para el caso legítimo no previene el error: genera atajos.* Cuando un control obligatorio no se puede cumplir, no se cumple: se rodea, y los datos se contaminan en silencio.

---

## 7. Ficha de racionalización — antes de programar

| Campo | Qué responde |
|---|---|
| Causa | Qué hecho real hace nacer el hallazgo |
| Consecuencia | Qué pasa si nadie actúa. **Si no se puede escribir una consecuencia real, la tarjeta no debería existir** |
| Acción correctiva | Qué hace la persona. **Una acción, no «revisar»** |
| Tiempo de respuesta | Cuánto tiene antes de que sea tarde. De acá salen los umbrales |
| Condición de cierre | Qué dato prueba que se resolvió |
| Clave natural | Si no se puede nombrar una estable, la tarjeta no está bien pensada |
| Dueño y suplente | Nombres |
| Apta para TV | Sí / No |

**Prueba de fuego:** si la acción correctiva queda como «mirar», «revisar» o «estar atento», es información, no alarma. Va al digest semanal, no a la pantalla.

---

## 8. Modelo de datos

`ops.db` — SQLite, WAL, `synchronous=FULL`, fuera de OneDrive.

| Tabla | Qué guarda |
|---|---|
| `bertok_ops_hallazgos` | **Verdad del estado actual.** Un renglón por clave natural |
| `bertok_ops_eventos` | **Registro de auditoría**, append-only. Con persona, hora y campo `version` |
| `bertok_ops_personas` | Padrón desde Odoo + PIN local + rol. Nunca se borra un renglón |
| `bertok_ops_procesos` | Dueño, suplente, revisor, umbrales, cadencia, ventana, apta para TV, modo sombra |
| `bertok_ops_turnos` | Rotaciones, participantes, cadencia, ausencias |
| `bertok_ops_corridas` | Cada ejecución de cada detector. 90 días de detalle |
| `bertok_ops_frescura` | Última actualización conocida de cada fuente |
| `bertok_ops_calendario` | Feriados nacionales. Carga anual manual, ~20 fechas |

**El estado es autoritativo, no una reconstrucción.** Se escriben las dos tablas, pero el estado no se rearma desde el evento cero. Motivo: el versionado de eventos es el asesino silencioso de los sistemas reconstruibles, y ese impuesto no tiene retorno al tamaño de Bertok. La auditabilidad se conserva entera.

**Dos precauciones baratas:** campo `version` en cada evento, y **nunca cambiarle el significado a un tipo de evento existente** — se crea uno nuevo.

### Retención

- `bertok_ops_eventos`: **nunca se borra.**
- `bertok_ops_hallazgos`: se conservan todos, mínimo 13 meses en línea.
- `bertok_ops_corridas`: 90 días de detalle, resumen diario más atrás.

---

## 9. Trampas conocidas — no repetir estos errores

1. **Una SQLite en WAL no se copia con un `copy`.** Son tres archivos. El backup se hace con **`VACUUM INTO`**, que genera un archivo único y consistente, y recién ese se copia a OneDrive. Rotación 7 diarios + 4 semanales, **nunca pisar el mismo archivo**. **Restauración de prueba una vez por mes.**
1b. **`PRAGMA integrity_check` no detecta toda la corrupción.** Medido: con 3.000 bytes ensuciados en páginas libres devolvió «ok» y la base abrió normal. Por eso cada copia lleva un **SHA-256 al lado** (`.sha256`), y la restauración lo verifica primero. Es lo único que detecta un byte cambiado en una carpeta sincronizada.
1c. **Al verificar un backup, contar las filas del origen ANTES de copiar.** Si se cuenta después, con la base en uso el origen siempre tiene más y toda corrida da falso negativo — justo en el escenario para el que existe el backup.
2. **`busy_timeout` es obligatorio.** Sin él una escritura concurrente falla al instante. 3 a 5 segundos. Más `BEGIN IMMEDIATE` en transacciones de escritura y `wal_autocheckpoint` ~1000 páginas. **Hipótesis a verificar: esto puede ser la causa de las caídas de Picking.**
3. **`ML.db` está dentro de OneDrive.** Nunca escribir. Y los scripts de actualización corren **en la PC dedicada**; el Centro lee el archivo local, no el sincronizado.
4. **El Centro nunca llama a la API de Mercado Libre.** La cuota es compartida y opaca — «incluso una frecuencia baja puede activar límites». Todo pasa por `ML.db`. Reclamos entran **por webhook a n8n**, no por polling.
5. **Un detector que falla deja la tarjeta en gris «sin datos», nunca en verde.** Verde = «miré y está bien». Gris = «no pude mirar». Si falla N corridas seguidas, escala.
6. **Verde sobre datos viejos es peor que no tener pantalla.** Cada hallazgo lleva su `datos_al`. Tolerancias: `picking.db` 15 min · `ML.db` 1 h · Excel de Contabilium su cadencia + margen.
7. **La TV negra no cubre el caso peligroso**: PC viva con el Centro colgado muestra la última página, en verde. Por eso el **reloj de último refresco** en pantalla, y el latido externo a n8n (pendiente).
8. **El 40-50% de remitos sin cerrar es una hipótesis, no un dato.** Surgió durante la depuración de Picking. Se mide antes de diseñar contra él.
9. **Ollama y generación de imágenes van en OTRA máquina.** La PC servidor tiene un solo trabajo: no estar caída entre las 9 y las 15:30.

---

## 10. Los trece procesos

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

**⚠️ Antonella es dueña de 6 de 13 procesos.** Si falta una semana, se cae la mitad de Bertok. Es una decisión abierta de organización, no de arquitectura.

### Parámetros fijos

- **Despachos:** Flex venta hasta 13:00, moto 13:30. Mercado Envíos hasta 15:00. **Lunes a sábado**, sin domingos ni feriados. Cero pedidos pasa a amarillo a las **11:00**.
- **«Listo» = orden emitida y bultos cerrados.** No «etiqueta impresa», no «escaneo completo».
- **«Hoy» termina a las 13:00.**
- **Insumos** cada 10 días · **Redes** 4 por mes · **Google Ads** y **Mercado Ads** semanales · **Full** cada 15 días · **Rendición** los viernes.
- **Sync de padrón desde Odoo** cada 6 h, con botón de sincronizar ahora. **Un alta puede esperar, una baja no**: se hace local e inmediata. Si el Centro y Odoo se contradicen, **gana la restricción**.

---

## 11. Escalado

| Nivel | Cuándo | A quién |
|---|---|---|
| 0 | Se vuelve visible | Pantalla y modo usuario del asignado |
| 1 | Umbral de la tarjeta | WhatsApp al asignado |
| 2 | Umbral de escalado | WhatsApp al suplente o supervisor |
| 3 | Vence el límite duro, o 3ª posposición | **Gerardo. Sólo acá.** |

**El reloj corre desde el acuse de recibido, no desde la aparición.** Si no hay acuse dentro del umbral, eso mismo escala — distingue «no lo vio» de «lo vio y no lo hizo».

**Si algo no requiere que alguien deje lo que está haciendo, no manda WhatsApp.**

Gerardo tiene dos salidas y ninguna es un tablero: **nivel 3 por excepción** y **digest semanal**.

---

## 12. Umbrales

Tres orígenes, no mezclarlos:

- **Externo** — lo impone un tercero (ML, la moto, el vencimiento de un container). No se elige, se averigua.
- **De política** — lo decide Gerardo (cada 10 días, 4 por mes).
- **Derivado** — sale de la distribución observada en modo sombra.

> **El umbral derivado se pone donde los casos normales ya terminaron: percentil 80-90 de lo que sí se resolvió.**

**Tope de trabajo en curso: arrancar sin tope y medir.** Si rutinariamente es 1 o 2, no hace falta nunca. Un tope que nunca se toca es puro estorbo.

---

## 13. Modo sombra — compuerta obligatoria

| Etapa | Qué pasa | Cómo se avanza |
|---|---|---|
| 🔴 Sombra | Corre y registra. **No se muestra ni se avisa** | Mínimo 2 ciclos del proceso |
| 🟡 Visible sin push | Aparece en pantalla, sin WhatsApp | Revisión con el dueño: qué era real y qué ruido |
| 🟢 Completa | Push y escalado activos | Una persona la usó y sirvió |

**Métricas del sistema sobre sí mismo**, al digest semanal: avisos por día y persona · tasa de acción · tasa de posposición · tiempo hasta el acuse.

> **Una tarjeta que grita en falso se apaga. No se tolera, no se ignora: se apaga y se rediseña.**
> Si una tarjeta genera más de un puñado de pushes por día, **la tarjeta está rota, no el equipo.**

---

## 14. Cómo agregar una tarjeta nueva

1. Probar la **jerarquía de prevención** (§6). ¿Se puede evitar en vez de detectar?
2. Completar la **ficha de racionalización** (§7).
3. Nombrar la **clave natural**.
4. Elegir tipo — **informativa por defecto**.
5. Nombrar **dueño y suplente**.
6. Definir **línea de corte** y qué se hace con la deuda vieja.
7. Correr en **sombra**, mínimo 2 ciclos.
8. **Derivar umbrales** con el dueño presente.
9. Encender **sin push**, después **con push**.
10. Anotar en `BITACORA.md` qué se verificó y quién.

---

## 15. Al empezar una sesión

1. Leer este archivo y la última entrada de `BITACORA.md`.
2. Identificar al operador por `hostname` (tabla en el `CLAUDE.md` raíz).
3. **Avisar si otra sesión tocó este módulo el mismo día** — la coordinación por OneDrive es manual y ya se perdieron cambios.
4. Verificar en qué fase está el módulo antes de proponer nada.
5. Los scripts van en `.claude\sistema\`. Los reemplazados a `Superados\` con fecha.

---

## 16. Decisiones abiertas

| # | Decisión | Cuándo |
|---|---|---|
| 01 | **La carga de Antonella (6 procesos) y la de Gerardo (5 suplencias)** | Antes de encender |
| 02 | Que el motor de precios publique el **precio mínimo por SKU** | Fase 7 · módulo 03 |
| 03 | **Valores** de los umbrales derivados | Se miden en sombra |
| 04 | **Latido externo hacia n8n** | Fase 2 |
| 05 | **UPS** | Enero |
| 06 | **Consulta legal** sobre el registro de correctivos | Antes de ese campo |
| 07 | **¿El remito digital de ARCA alcanza a Bertok?** Cronograma jul-2026 → mar-2027 | **Fase 1** |

### A verificar (datos, no decisiones)

- **Hoy, en depuración, ¿qué pasa con los pedidos que no se pueden cerrar?** ¿Se acumulan, hay cierre forzado, o se cierra con lo que haya? **Es la pregunta más importante que queda.**
- ¿El expreso da **número de guía con constancia de entrega**? De eso depende el nivel B de cierre.
- ¿**Cuántos expresos** se usan? Define si el scorecard es simple.
- ¿`ML.db` ya ingiere **reclamos**? ¿Ya trae **stock en Full, envíos de reposición y la sugerencia de cantidades de ML**?
- ¿Los **cargos de almacenamiento de Full** están identificados dentro de las 7.051 filas de cargos reales?
- ¿El **sábado** rige el mismo horario de corte?

### Fuera de este módulo, pero urgente

> El `CLAUDE.md` de **Cortex** dice que Bertok vende «tintas, sustratos e insumos gráficos». Eso alimenta los prompts del agente que responde a leads B2B reales. **Es independiente de este proyecto y es más urgente que él.**

---

## 17. Cómo se presenta al equipo

> **«Dejá de acordarte de todo.»**

Un sistema percibido como vigilancia recibe datos falsos: se marca hecho lo que no se hizo, se descarta lo incómodo.

La evidencia sobre por qué fracasan estos sistemas en PyMEs es consistente: **el equipo no se resiste a la tecnología, se resiste a aceptar que el sistema muestra una realidad distinta de la asumida.** Ese choque va a ocurrir el día uno, con el número de remitos sin cerrar.

**Presentarlo como problema de proceso, no de personas.** Si se lee como «el sistema nos está marcando», se defiende. Si se lee como «esto se perdía y nadie se había dado cuenta», colabora.

**La capacitación es un entregable de Fase 1, no una buena intención.** Media hora con el equipo, con el sistema andando, antes de encender el push.
