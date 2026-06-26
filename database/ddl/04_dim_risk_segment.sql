-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 04_dim_risk_segment.sql
-- Tabla      : dw.dim_risk_segment
-- Descripción:
-- Dimensión que almacena la clasificación de riesgo utilizada para segmentar
-- clientes y créditos dentro del Data Warehouse.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.dim_risk_segment (

    -- Clave sustituta
    risk_segment_key SMALLINT GENERATED ALWAYS AS IDENTITY,

    -- Clave de negocio
    risk_code VARCHAR(20) NOT NULL,

    -- Información del segmento
    risk_level VARCHAR(30) NOT NULL,
    score_min SMALLINT,
    score_max SMALLINT,
    default_probability NUMERIC(5,4),
    description VARCHAR(255),

    -- Restricciones
    CONSTRAINT pk_dim_risk_segment
        PRIMARY KEY (risk_segment_key),

    CONSTRAINT uq_dim_risk_code
        UNIQUE (risk_code),

    CONSTRAINT chk_dim_risk_score_min
        CHECK (
            score_min IS NULL
            OR score_min >= 0
        ),

    CONSTRAINT chk_dim_risk_score_max
        CHECK (
            score_max IS NULL
            OR score_max >= 0
        ),

    CONSTRAINT chk_dim_risk_score_range
        CHECK (
            score_min IS NULL
            OR score_max IS NULL
            OR score_min <= score_max
        ),

    CONSTRAINT chk_dim_default_probability
        CHECK (
            default_probability IS NULL
            OR (
                default_probability >= 0
                AND default_probability <= 1
            )
        )

);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.dim_risk_segment IS
'Dimensión que almacena la clasificación corporativa del riesgo crediticio.';

COMMENT ON COLUMN dw.dim_risk_segment.risk_segment_key IS
'Clave sustituta de la dimensión.';

COMMENT ON COLUMN dw.dim_risk_segment.risk_code IS
'Código único del segmento de riesgo.';

COMMENT ON COLUMN dw.dim_risk_segment.risk_level IS
'Nivel de riesgo asociado al segmento.';

COMMENT ON COLUMN dw.dim_risk_segment.score_min IS
'Valor mínimo del rango de puntuación del segmento.';

COMMENT ON COLUMN dw.dim_risk_segment.score_max IS
'Valor máximo del rango de puntuación del segmento.';

COMMENT ON COLUMN dw.dim_risk_segment.default_probability IS
'Probabilidad estimada de incumplimiento para el segmento.';

COMMENT ON COLUMN dw.dim_risk_segment.description IS
'Descripción del segmento de riesgo.';