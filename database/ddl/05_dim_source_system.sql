-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 05_dim_source_system.sql
-- Tabla      : dw.dim_source_system
-- Descripción:
-- Dimensión que almacena la información de los sistemas de origen integrados
-- en el Data Warehouse.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.dim_source_system (

    -- Clave sustituta
    source_system_key SMALLINT GENERATED ALWAYS AS IDENTITY,

    -- Clave de negocio
    source_code VARCHAR(20) NOT NULL,

    -- Información del sistema
    source_name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50),
    source_description VARCHAR(255),

    -- Restricciones
    CONSTRAINT pk_dim_source_system
        PRIMARY KEY (source_system_key),

    CONSTRAINT uq_dim_source_system_code
        UNIQUE (source_code),

    CONSTRAINT uq_dim_source_system_name
        UNIQUE (source_name)

);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.dim_source_system IS
'Dimensión que identifica el origen de los datos integrados en el Data Warehouse.';

COMMENT ON COLUMN dw.dim_source_system.source_system_key IS
'Clave sustituta de la dimensión.';

COMMENT ON COLUMN dw.dim_source_system.source_code IS
'Código único del sistema de origen.';

COMMENT ON COLUMN dw.dim_source_system.source_name IS
'Nombre del sistema de origen.';

COMMENT ON COLUMN dw.dim_source_system.source_type IS
'Tipo de sistema de origen (Dataset, API, Base de datos, Archivo, etc.).';

COMMENT ON COLUMN dw.dim_source_system.source_description IS
'Descripción del sistema de origen.';