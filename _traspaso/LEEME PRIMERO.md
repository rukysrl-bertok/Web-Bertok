# LEEME PRIMERO

Traspaso del trabajo hecho con Claude Code entre el **04 y el 09/09/2026**, desde el celular y en un contenedor remoto. **Nada de esto está todavía en OneDrive.**

Son **dos proyectos** en distinto estado:

| | Proyecto | Estado |
|---|---|---|
| **A** | **Centro de Operaciones** — «Dejá de acordarte de todo» | Arquitectura cerrada + cimientos escritos y probados 🟡 |
| **B** | **Reposición a Full** | Sólo el encuadre. Sin relevar, sin código |

---

## Paso 1 — Mover todo a OneDrive

Esta carpeta `_traspaso/` está dentro del repo `Web-Bertok` **sólo para transportar los archivos**. No es su lugar.

| Del repo | A OneDrive |
|---|---|
| `_traspaso/17 - Centro de Operaciones/` | `Bertok - Documentos\17 - Centro de Operaciones\` |
| `_traspaso/plans/handoffs/*.md` | `Bertok - Documentos\plans\handoffs\` |
| `_traspaso/Master Plan v5*.html` | `Bertok - Documentos\17 - Centro de Operaciones\` |

Después: `git push origin --delete claude/project-analysis-4iwwdk`

> El número **17** es una propuesta. Si se cambia, hay rutas que actualizar en `crear_ops_db.py` y `backup_bases.py`.

---

## Paso 2 — Verificar que la sesión es LOCAL

**Esto ya causó una confusión.** Claude Code desde la web o el celular corre en un contenedor remoto que **no ve `ML.db` ni la carpeta de Bertok**. Todo el trabajo real necesita el CLI local.

Cómo confirmarlo, en la primera sesión:

```
pwd                    →  tiene que ser la ruta de Windows, no /home/user/...
dir CLAUDE.md ML.db    →  tiene que listar los dos
```

Si `pwd` devuelve algo tipo `/home/user/...`, **es remota y no sirve** para este trabajo.

Para abrir la local:

```
cd /d "%USERPROFILE%\Ruky S.R.L\Bertok - Documentos"
claude
```

---

## Paso 3 — Elegir por dónde seguir

### Proyecto A · Centro de Operaciones

Leer, en orden:

1. `plans\handoffs\2026-09-05 Centro de Operaciones - arranque.md`
2. `17 - Centro de Operaciones\CLAUDE.md` ← **las reglas**
3. `17 - Centro de Operaciones\BITACORA.md`

Master Plan completo (26 secciones):
https://claude.ai/code/artifact/03dc1c35-756b-44d4-bbcf-59d794b480b5

Primer comando a correr:

```
cd "17 - Centro de Operaciones\.claude\sistema"
python probar_guarda.py        # tiene que dar 33/33
```

**Si no da 33/33, parar.** Los scripts se probaron en Linux con Python 3.13 y SQLite 3.45; en Windows puede tomar el Python de ZKBioTime, que quizás tenga un SQLite viejo sin `VACUUM INTO`.

### Proyecto B · Reposición a Full

Leer `plans\handoffs\2026-09-09 Reposición Full - arranque.md` y usarlo como prompt inicial de una sesión dedicada. **Ese archivo se pega tal cual.**

Arranca por un relevamiento de `ML.db`. No hay que programar nada antes de eso.

---

## Lo que está pendiente y no es de ningún módulo

- **El `CLAUDE.md` raíz no documenta la reposición a Full.** Dice «nunca Full» sin distinguir que eso vale para el *fulfillment de pedidos*, y que sí existe una *reposición de inventario* cada 15 días.
- **El `CLAUDE.md` de Cortex dice que Bertok vende «tintas, sustratos e insumos gráficos».** Eso alimenta los prompts del agente que le responde a leads B2B reales. **Es independiente de los dos proyectos y es más urgente que ambos.**

---

## Hardware decidido en el camino

| | |
|---|---|
| Placa del servidor | ASUS PRIME Z390-A · LGA1151 · DDR4 |
| RAM | **DDR4 UDIMM 8 GB 3200.** Evaluada: `Raptor RAP-UD4-8G-3200`, tienda oficial. Dos módulos si el presupuesto da → slots **A2 y B2** |
| Disco | SSD 256 GB. Alcanza **si la carpeta de OneDrive entra**: usar «Archivos a pedido» y dejar en local sólo lo que los scripts tocan |
| Ollama | **En otra máquina.** Nunca en el servidor |

**No sirve:** DDR5, RDIMM, ECC, REG, LRDIMM, SODIMM.
La etiqueta tiene que decir **`PC4-25600U`** — la **U** final es de UDIMM.
