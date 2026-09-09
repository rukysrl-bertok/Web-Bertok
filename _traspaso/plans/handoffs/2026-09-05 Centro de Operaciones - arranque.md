# Handoff — Centro de Operaciones Bertok

**Fecha:** 05/09/2026 · **De:** sesión remota de Claude Code (teléfono) · **Para:** primera sesión en la PC

Todo lo definido en esa sesión, listo para continuar. **Leer esto primero, después el `CLAUDE.md` del módulo.**

> **Antes de nada: confirmá que la sesión es LOCAL.** Claude Code desde la web o el celular corre en un contenedor remoto que **no ve `ML.db` ni la carpeta de Bertok**. Ya pasó una vez.
> `pwd` tiene que devolver la ruta de Windows, no `/home/user/...`, y `dir CLAUDE.md ML.db` tiene que listar los dos archivos.

---

## 1. Lo primero: sacar los archivos de la rama y ponerlos donde van

Los archivos llegaron por una rama del repo `Web-Bertok`, porque la sesión corría en un contenedor efímero y había que sacarlos de ahí. **Ese repo no es su lugar definitivo.**

```
git clone <repo Web-Bertok>
git checkout claude/project-analysis-4iwwdk
```

Y mover la carpeta `_traspaso/` a donde corresponde:

| Del repo | A OneDrive |
|---|---|
| `_traspaso/17 - Centro de Operaciones/` | `Bertok - Documentos\17 - Centro de Operaciones\` |
| `_traspaso/plans/handoffs/...` | `Bertok - Documentos\plans\handoffs\` |
| `_traspaso/Master Plan v5*.html` | `Bertok - Documentos\17 - Centro de Operaciones\` |

Después, **borrar la rama**: `git push origin --delete claude/project-analysis-4iwwdk`

> El número de módulo **17** es una propuesta. Si se usa otro, hay que actualizar las rutas en `crear_ops_db.py` y `backup_bases.py`.

---

## 2. Qué hay y en qué estado

### Documentos

| Archivo | Qué es |
|---|---|
| **Master Plan v5** (HTML) | Arquitectura completa, 26 secciones. La referencia de diseño. También publicado en https://claude.ai/code/artifact/03dc1c35-756b-44d4-bbcf-59d794b480b5 |
| **`CLAUDE.md`** | Las reglas del módulo. **Es lo que hay que leer al empezar cada sesión.** |
| **`BITACORA.md`** | Tres entradas del 05/09: diseño, esquema+guarda, backup. |

### Scripts — `\.claude\sistema\`

| Script | Estado | Qué hace |
|---|---|---|
| `esquema_ops.sql` | 🟡 | 9 tablas, 1 vista, 4 triggers, 8 índices |
| `guarda_alcance.py` | 🟡 | Bloquea escrituras fuera de `bertok_ops_*` vía el autorizador de SQLite |
| `crear_ops_db.py` | 🟡 | Crea `ops.db` con pragmas. Idempotente. Aborta si la ruta está en OneDrive |
| `probar_guarda.py` | 🟡 | **33 comprobaciones, todas OK** |
| `backup_bases.py` | 🟡 | `VACUUM INTO` + verificación + SHA-256 + rotación 7+4 |
| `restaurar_prueba.py` | 🟡 | Restauración mensual con verificación de firma e integridad |

**🟡 = probado por código, no por una persona. Nada corrió todavía en la máquina real.**

---

## 3. Lo primero que hay que correr en la PC

```
cd "17 - Centro de Operaciones\.claude\sistema"
python probar_guarda.py          # tiene que dar 33/33
python crear_ops_db.py           # crea C:\Sistema de Picking\ops.db
python backup_bases.py           # necesita ajustar antes DESTINO_POR_DEFECTO
python restaurar_prueba.py       # y anotar el resultado en BITACORA.md
```

Si `probar_guarda.py` no da 33/33, **parar y revisar** antes de seguir.

---

## 4. El plan de fases, en una línea cada una

| Fase | Qué |
|---|---|
| **0 · Terminar Picking** | PC dedicada · mudar Picking **antes** de terminar de depurar · los 4 niveles de cierre · roles cerrados · pragmas de SQLite · `ops.db` + backup · padrón desde Odoo · login unificado |
| 1 · Motor + 1ª tarjeta | Detectores, clave natural, estados, turnos, TV, modo usuario, push, auditoría **+ Pendientes de cierre** + capacitación |
| 2 · Salud de datos | Frescura, tarjeta de salud, latido externo a n8n |
| 3 · Despachos + Insumos | Se calibra el ritmo por pedido |
| 4 · Mercado Ads | Punto de quiebre publicitario, sobre datos ya existentes |
| 5 · Comercio exterior | Hitos de container desde `05 - Compras`. Nunca en TV |
| 6 · Full | 4 hitos, feriados, cantidades vs. sugerencia de ML |
| 7 · Preguntas + Promociones + Reclamos | Hermes v2 |
| 8 · Calendario | Rendición, Google Ads, Redes. Sin push |
| 9 · Cobranzas | Después de completar Finanzas |

**Fase 0 termina cuando Picking corre estable en la máquina nueva, sin caídas, dos semanas de uso normal.**

---

## 5. Decisiones abiertas

| # | Decisión | Cuándo |
|---|---|---|
| **01** | **La carga de Antonella (6 de 13 procesos) y la de Gerardo (5 suplencias).** No la resuelve la arquitectura | **Antes de encender** |
| 02 | Que el motor de precios publique el **precio mínimo por SKU** | Fase 7 · módulo 03 |
| 03 | Valores de los umbrales derivados | Se miden en sombra |
| 04 | Latido externo hacia n8n | Fase 2 |
| 05 | UPS | Enero |
| 06 | Consulta legal sobre el registro de correctivos | Antes de ese campo |
| 07 | **¿El remito digital de ARCA alcanza a Bertok?** Cronograma jul-2026 → mar-2027 | **Fase 1** |

## 6. A verificar (datos, no decisiones)

- ⚠️ **Hoy, en depuración, ¿qué pasa con los pedidos que no se pueden cerrar en Picking?** ¿Se acumulan, hay cierre forzado, o se cierra con lo que haya? **Es la más importante:** define si el punto de partida es un problema a medir o un dato ya contaminado.
- ¿El expreso da **número de guía con constancia de entrega**? De eso depende el nivel B de cierre.
- ¿**Cuántos expresos** se usan? Define si el scorecard es simple.
- ¿`ML.db` ya ingiere **reclamos**? ¿Ya trae **stock en Full, envíos de reposición y la sugerencia de cantidades de ML**?
- ¿Los **cargos de almacenamiento de Full** están identificados dentro de las 7.051 filas de cargos reales?
- ¿El **sábado** rige el mismo horario de corte?
- **Verificar la hipótesis de `busy_timeout`** como causa de las caídas de Picking, durante la mudanza.

---

## 7. Fuera de este módulo, pendiente

- **El `CLAUDE.md` raíz no documenta la reposición a Full.** La regla vigente dice «nunca Full» y hay que partirla en dos: nunca se *arma* un pedido Full / sí existe una *reposición* cada 15 días.
- **El `CLAUDE.md` de Cortex dice que Bertok vende «tintas, sustratos e insumos gráficos».** Eso alimenta los prompts del agente que responde a leads B2B reales. **Es independiente de este proyecto y es más urgente que él.**

---

## 8. Hardware — decidido en la misma sesión

| | |
|---|---|
| Placa | ASUS PRIME Z390-A · LGA1151 · DDR4 |
| **RAM a comprar** | **DDR4 UDIMM 8 GB 3200** — evaluada: `Raptor RAP-UD4-8G-3200`, tienda oficial. Dos módulos si el presupuesto da (slots **A2 y B2**) |
| Disco | SSD 256 GB — alcanza, **si la carpeta de OneDrive entra**. Usar «Archivos a pedido» y dejar en local sólo lo que los scripts tocan |
| Ollama | **En otra máquina.** Nunca en el servidor |

**Lo que NO sirve:** DDR5, RDIMM, ECC, REG, LRDIMM, SODIMM. La etiqueta tiene que decir **`PC4-25600U`** — la **U** final es de UDIMM.

---

## 9. Prompt para arrancar la primera sesión en la PC

```
Vengo de una sesión remota donde se definió el Centro de Operaciones.
Leé, en este orden:
  1. plans\handoffs\2026-09-05 Centro de Operaciones - arranque.md
  2. 17 - Centro de Operaciones\CLAUDE.md
  3. 17 - Centro de Operaciones\BITACORA.md

Después corré probar_guarda.py y confirmame que da 33/33.
No avances a Fase 0 hasta que eso pase en esta máquina.
```

---

## 10. Cómo se llegó hasta acá

El punto de partida fue un plan conceptual escrito por otra IA sin contexto real. Se corrigió el inventario (no existe Power BI, Contabilium no tiene API, Picking está en uso diario pero en depuración, faltaban n8n/Odoo/Cortex/Hermes), se pasó de 7 a 13 procesos, y se revisó todo contra fuentes externas: **ISA-18.2** (gestión de alarmas), **Andon**, **Google SRE**, **poka-yoke**, **reposición periódica (R,S)**, costos de almacenamiento de ML Full, **Kanban**, **OWASP**, **Ley 25.326**, SQLite en producción, event sourcing, pantallas 24/7, API de ML y literatura de adopción en PyMEs.

Las fuentes están listadas en el punto 26 del Master Plan.

**Dos ideas que conviene no perder:**

1. **La jerarquía de prevención (Shingo).** El Centro vive en el nivel 4 de 5 — detección. Antes de construir cualquier tarjeta hay que probar si el error se puede *evitar* en vez de *detectar*. Cumplir esa regla probablemente achique el catálogo, y eso es bueno.

2. **El riesgo número uno no es técnico.** Los equipos que reciben muchas alertas de baja calidad no responden peor a las malas: **dejan de responder a todas.** Por eso el modo sombra, la línea de corte y la regla de que una tarjeta que grita en falso se apaga y se rediseña.
