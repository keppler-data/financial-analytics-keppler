-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 02_dim_time.sql
-- Tabla      : dw.dim_time
-- Descripción:
-- Dimensión de tiempo utilizada para el análisis temporal de todas las tablas
-- de hechos del Data Warehouse.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.dim_time (

    -- Clave sustituta (formato YYYYMMDD)
    time_key INTEGER NOT NULL,

    -- Fecha
    full_date DATE NOT NULL,

    -- Componentes de la fecha
    day SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter SMALLINT NOT NULL,
    year SMALLINT NOT NULL,
    week SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    day_name VARCHAR(20) NOT NULL,

    -- Indicadores
    is_weekend BOOLEAN NOT NULL,

    -- Restricciones
    CONSTRAINT pk_dim_time
        PRIMARY KEY (time_key),

    CONSTRAINT uq_dim_time_date
        UNIQUE (full_date),

    CONSTRAINT chk_dim_time_day
        CHECK (day BETWEEN 1 AND 31),

    CONSTRAINT chk_dim_time_month
        CHECK (month BETWEEN 1 AND 12),

    CONSTRAINT chk_dim_time_quarter
        CHECK (quarter BETWEEN 1 AND 4),

    CONSTRAINT chk_dim_time_week
        CHECK (week BETWEEN 1 AND 53),

    CONSTRAINT chk_dim_time_day_of_week
        CHECK (day_of_week BETWEEN 1 AND 7)

);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.dim_time IS
'Dimensión de tiempo utilizada para el análisis histórico del Data Warehouse.';

COMMENT ON COLUMN dw.dim_time.time_key IS
'Clave sustituta de la dimensión con formato YYYYMMDD.';

COMMENT ON COLUMN dw.dim_time.full_date IS
'Fecha completa.';

COMMENT ON COLUMN dw.dim_time.day IS
'Día del mes.';

COMMENT ON COLUMN dw.dim_time.month IS
'Número del mes.';

COMMENT ON COLUMN dw.dim_time.month_name IS
'Nombre del mes.';

COMMENT ON COLUMN dw.dim_time.quarter IS
'Trimestre del año.';

COMMENT ON COLUMN dw.dim_time.year IS
'Año calendario.';

COMMENT ON COLUMN dw.dim_time.week IS
'Semana del año.';

COMMENT ON COLUMN dw.dim_time.day_of_week IS
'Día de la semana (1-7).';

COMMENT ON COLUMN dw.dim_time.day_name IS
'Nombre del día de la semana.';

COMMENT ON COLUMN dw.dim_time.is_weekend IS
'Indica si la fecha corresponde a un fin de semana.';