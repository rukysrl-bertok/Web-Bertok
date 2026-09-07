# Centro de Operaciones — Bitácora

> Registro de sesiones. Las **reglas** están en `CLAUDE.md`.
> Entrada más reciente arriba. Cada entrada se firma con el `hostname` del operador.

## Cómo se escribe una entrada

```
## AAAA-MM-DD · Operador (HOSTNAME)

**Qué se hizo**
- …

**Qué se verificó, y cómo**
- 🟢 lo usó una persona en la operación real
- 🟡 probado por código, no por una persona
- 🔴 roto o sin hacer

**Qué quedó pendiente**
- …

**Trampas encontradas** (si las hubo → pasarlas a CLAUDE.md §9)
- …
```

**Regla:** nada se anota como 🟢 sin decir **quién** lo usó y **cuándo**.

---

## 2026-09-05 (c) · Gerardo (DESKTOP-O7FNU0O)

**Qué se hizo**

- **`backup_bases.py`** — backup con `VACUUM INTO`, verificación, rotación 7 diarios + 4 semanales, firma SHA-256 por copia y manifiesto `ultimo_backup.json`.
- **`restaurar_prueba.py`** — la restauración mensual: toma el backup más nuevo, lo copia a una carpeta descartable, verifica firma, integridad, claves foráneas, esquema completo y conteo de filas contra la base viva.

**Qué se verificó, y cómo**

- 🟡 **Backup con la base en uso**, con un hilo escribiendo en paralelo: 222 escrituras concurrentes durante la copia, `integrity_check` ok, y **ningún archivo `-wal` ni `-shm` en el destino** — `VACUUM INTO` produce un solo archivo cerrado, que es todo el punto.
- 🟡 **Rotación probada sobre 12 días simulados**: quedaron exactamente 7 diarios y las semanales por semana ISO.
- 🟡 **No pisa**: correr dos veces el mismo día falla con mensaje claro en vez de sobrescribir.
- 🟡 **Códigos de salida correctos** para la tarea programada: 0 si todo bien, 1 si falló alguna base, 2 si el SQLite no soporta `VACUUM INTO`.
- 🟡 **Restauración detecta corrupción** que `integrity_check` no ve (ver abajo).
- 🔴 No corrió sobre las máquinas reales ni contra `picking.db` de verdad.

**Trampas encontradas — las dos las encontró la prueba, no la lectura del código**

1. **La verificación del backup estaba mal, justo en el escenario para el que existe.** Contaba las filas del origen *después* del `VACUUM INTO`, así que con la base en uso el origen siempre tenía más filas que la copia y **toda corrida con escritura concurrente daba falso negativo**. Corregido: el conteo de referencia se toma *antes* de copiar, y la copia puede tener filas de más, nunca de menos.

2. **`PRAGMA integrity_check` NO detecta toda la corrupción.** Medido sobre esta misma base: con **3.000 bytes ensuciados en páginas libres del medio del archivo, devolvió «ok»** y la base abrió y consultó normal. Recién con ~20% del archivo corrompido tira `database disk image is malformed`.
   **Por eso se agregó un SHA-256 al lado de cada copia.** Verificado: sobre esa misma corrupción que `integrity_check` aprueba, el checksum la rechaza y la restauración devuelve error. Es lo único que detecta un byte cambiado después de la copia — sincronización a medias de OneDrive, bit-rot, escritura parcial.

**Qué quedó pendiente**

- Programar la tarea de Windows, una vez por día en horario no operativo.
- Confirmar la ruta real del destino en OneDrive (hoy es una constante en el script).
- **Primera restauración de prueba real**, y anotarla acá con fecha y quién.

---

## 2026-09-05 (b) · Gerardo (DESKTOP-O7FNU0O)

**Qué se hizo**

- Se escribió el **esquema de `ops.db`** (`.claude\sistema\esquema_ops.sql`): 9 tablas, 1 vista, 4 triggers, 8 índices. Todo con prefijo `bertok_ops_`.
- Se escribió la **guarda de alcance** (`guarda_alcance.py`). **No es un filtro por texto del SQL: usa el autorizador del propio SQLite**, que corre dentro del motor antes de compilar cada sentencia. No se puede esquivar con comentarios, mayúsculas, comillas ni sentencias encadenadas.
- Se escribió el **creador de la base** (`crear_ops_db.py`), idempotente, con verificación de que la ruta **no esté dentro de una carpeta sincronizada**.
- Se escribió y ejecutó la **prueba destructiva** (`probar_guarda.py`): 33 comprobaciones.

**Qué se verificó, y cómo**

- 🟡 **33/33 comprobaciones OK**, ejecutadas por código. Cubren: 15 sentencias destructivas bloqueadas, 8 reglas de integridad del esquema mordiendo, 5 operaciones legítimas funcionando, y 3 del modo lectura.
- 🟡 Creación de la base verificada: `journal_mode = wal`, `synchronous = FULL`, `busy_timeout = 5000 ms`.
- 🟡 Idempotencia verificada: segunda corrida sobre base existente, sin errores.
- 🟡 El chequeo de OneDrive aborta correctamente ante una ruta sincronizada.
- 🔴 **Nada de esto es verde.** No lo usó ninguna persona todavía, y no corrió sobre la máquina real.

**Decisiones de implementación tomadas acá**

- **Se agregó una novena tabla, `bertok_ops_ausencias`**, que el plan tenía metida dentro de turnos. Separada queda más limpia y es la que evita que la rotación asigne a alguien que está de franco.
- **Append-only reforzado con triggers**, no sólo por convención: `bertok_ops_eventos` rechaza UPDATE y DELETE a nivel base. Igual `bertok_ops_personas` con DELETE, y `nacido_en` es inmutable.
- **Unicidad parcial de la clave natural**: sólo puede haber una clave viva a la vez. Una archivada puede volver a nacer enlazada por `hallazgo_previo_id`, que es la regla de «un hallazgo cerrado que reaparece no revive».
- **`contraparte_tipo` / `contraparte_id`** como columnas de primera clase, para que el scorecard por expreso sea posible desde el día uno.
- **Dos modos de conexión**: `escritura` (sólo `bertok_ops_*`) y `lectura` (nada, ni con prefijo). Las fuentes ajenas se abren siempre en modo lectura.

**Trampas encontradas**

- **La primera versión de la guarda bloqueaba la creación del propio esquema.** Todo DDL escribe por debajo en `sqlite_master`, y el autorizador lo reporta como un INSERT sobre esa tabla. Se permitió el prefijo `sqlite_` — es seguro porque escribirlas a mano exige `PRAGMA writable_schema`, que está denegado, y porque el CREATE/DROP/ALTER que las provoca se autoriza aparte por el nombre real. **La prueba destructiva encontró esto sola, antes de que llegara a la máquina.**

**Qué quedó pendiente**

- Correr los tres scripts **en la PC dedicada**, contra la ruta real `C:\Sistema de Picking\ops.db`.
- El **script de backup** con `VACUUM INTO`, rotación 7+4 y restauración de prueba.
- Cargar la **semilla de `bertok_ops_procesos`** con los 13 procesos, sus dueños y sus turnos. Requiere confirmar antes la decisión abierta #01.
- Cargar el **calendario de feriados** del año.

---

## 2026-09-05 (a) · Gerardo (DESKTOP-O7FNU0O)

**Qué se hizo**

- Se definió el **Master Plan Arquitectónico v5** del Centro de Operaciones, en sesión con Claude, partiendo de un plan conceptual previo escrito sin contexto real.
- Se corrigió el inventario de partida: no existe Power BI (Bertok BI son 44 scripts y 17 tablas dentro de `ML.db`), Contabilium no tiene API sino scraping, Picking está en **uso diario pero todavía en depuración**, y el plan original ignoraba n8n, Odoo, Cortex y Hermes.
- Se partió en dos la regla de Full: **nunca se arma un pedido Full** (vigente) / **sí existe una reposición de inventario a Full** cada ~15 días, 200-300 paquetes, que no estaba documentada en ningún lado. **Pendiente: reflejarlo en el `CLAUDE.md` raíz.**
- Se pasó de 7 a **13 procesos**, con dueño y suplente definidos para todos.
- Se cerraron **más de 40 decisiones** de arquitectura, operación e infraestructura.
- Se revisó el plan contra fuentes externas: ISA-18.2 (gestión de alarmas), Andon, Google SRE, poka-yoke, modelos de reposición periódica, costos de almacenamiento de ML Full, Kanban, OWASP, Ley 25.326, SQLite en producción, event sourcing, pantallas 24/7, API de ML y literatura de adopción en PyMEs.
- Se creó este módulo con su `CLAUDE.md` y su `BITACORA.md`, antes de escribir código.

**Qué se verificó, y cómo**

- 🔴 **Nada del módulo está implementado.** Fase 0 sin arrancar.
- 🔴 Todo el catálogo de 13 procesos está en rojo.
- El Master Plan es un documento de arquitectura, no una verificación.

**Cambios de diseño que salieron de la revisión con fuentes**

- **Jerarquía de prevención antes de cada tarjeta.** El Centro opera en el nivel 4 de 5 (detección); hay que probar antes los niveles 1 a 3.
- **Los cuatro niveles de cierre (A/B/C/D) van en Picking, no en el Centro.** Picking ya exige foto y número de remito, pero no ofrece camino legítimo cuando la prueba no va a llegar — y un control que no se puede cumplir se rodea.
- **Fase 0 pasa a llamarse «Terminar Picking»**, y se muda antes de terminar de depurar.
- **Estado autoritativo + log de auditoría**, en vez de reconstrucción desde eventos.
- **Reclamos de ML por webhook**, no por polling.
- **Pragmas de SQLite** (`busy_timeout`, `BEGIN IMMEDIATE`, `wal_autocheckpoint`) en las dos bases.
- **Capacitación** como entregable de Fase 1.
- El **40-50% de remitos sin cerrar** pasó de dato establecido a **hipótesis a medir**.

**Qué quedó pendiente**

- **Arrancar Fase 0 — Terminar Picking.** Ver `CLAUDE.md` §16 y el plan de fases del Master Plan.
- **7 decisiones abiertas.** La #01 (carga de Antonella y de Gerardo) es la más importante y no es técnica.
- **6 verificaciones de datos.** La más importante: qué pasa hoy con los pedidos que no se pueden cerrar en Picking — determina si el punto de partida es un problema a medir o un dato ya contaminado.
- **Consulta al contador** sobre el remito digital de ARCA, antes de terminar la primera tarjeta.
- **Fuera de este módulo:** el `CLAUDE.md` de Cortex describe un rubro equivocado y alimenta los prompts que responden a leads reales.

**Trampas encontradas**

- Todas las conocidas al día de hoy quedaron cargadas en `CLAUDE.md` §9. La que más puede rendir: **la hipótesis de que las caídas de Picking sean falta de `busy_timeout`**, verificable en Fase 0 durante la mudanza.
