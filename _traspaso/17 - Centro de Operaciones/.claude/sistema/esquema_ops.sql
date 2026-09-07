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
