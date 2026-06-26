-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 01_dim_customer.sql
-- Tabla      : dw.dim_customer
-- Descripción:
-- Dimensión que almacena la información descriptiva de los clientes.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.dim_customer (

    -- Clave sustituta
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY,

    -- Clave de negocio
    customer_id VARCHAR(50) NOT NULL,

    -- Información demográfica
    gender VARCHAR(20),
    age SMALLINT,

    -- Información socioeconómica
    education VARCHAR(100),
    occupation VARCHAR(100),

    -- Información financiera
    monthly_income NUMERIC(18,2),
    debt_ratio NUMERIC(10,4),

    -- Restricciones
    CONSTRAINT pk_dim_customer
        PRIMARY KEY (customer_key),

    CONSTRAINT uq_dim_customer_customer_id
        UNIQUE (customer_id),

    CONSTRAINT chk_customer_age
        CHECK (age IS NULL OR age >= 18),

    CONSTRAINT chk_customer_income
        CHECK (monthly_income IS NULL OR monthly_income >= 0),

    CONSTRAINT chk_customer_debt_ratio
        CHECK (
            debt_ratio IS NULL
            OR debt_ratio >= 0
        )
);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.dim_customer IS
'Dimensión conformada que almacena la información corporativa de los clientes.';

COMMENT ON COLUMN dw.dim_customer.customer_key IS
'Clave sustituta de la dimensión.';

COMMENT ON COLUMN dw.dim_customer.customer_id IS
'Identificador único del cliente dentro del Data Warehouse.';

COMMENT ON COLUMN dw.dim_customer.gender IS
'Género del cliente.';

COMMENT ON COLUMN dw.dim_customer.age IS
'Edad del cliente.';

COMMENT ON COLUMN dw.dim_customer.education IS
'Nivel educativo del cliente.';

COMMENT ON COLUMN dw.dim_customer.occupation IS
'Ocupación o actividad económica principal.';

COMMENT ON COLUMN dw.dim_customer.monthly_income IS
'Ingreso mensual del cliente.';

COMMENT ON COLUMN dw.dim_customer.debt_ratio IS
'Relación deuda/ingreso utilizada para análisis de riesgo.';