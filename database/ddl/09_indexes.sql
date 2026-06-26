-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 09_indexes.sql
-- Descripción:
-- Creación de índices para optimizar el rendimiento de consultas analíticas
-- y operaciones JOIN del modelo dimensional.
-- ============================================================================

-- ============================================================================
-- DIM_CUSTOMER
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dim_customer_customer_id
    ON dw.dim_customer (customer_id);

-- ============================================================================
-- DIM_TIME
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dim_time_full_date
    ON dw.dim_time (full_date);

CREATE INDEX IF NOT EXISTS idx_dim_time_year_month
    ON dw.dim_time (year, month);

-- ============================================================================
-- DIM_PRODUCT
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dim_product_code
    ON dw.dim_product (product_code);

-- ============================================================================
-- DIM_RISK_SEGMENT
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dim_risk_code
    ON dw.dim_risk_segment (risk_code);

-- ============================================================================
-- DIM_SOURCE_SYSTEM
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dim_source_code
    ON dw.dim_source_system (source_code);

-- ============================================================================
-- FACT_APPLICATION
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_fact_application_customer
    ON dw.fact_application (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_application_time
    ON dw.fact_application (time_key);

CREATE INDEX IF NOT EXISTS idx_fact_application_product
    ON dw.fact_application (product_key);

CREATE INDEX IF NOT EXISTS idx_fact_application_risk
    ON dw.fact_application (risk_segment_key);

CREATE INDEX IF NOT EXISTS idx_fact_application_source
    ON dw.fact_application (source_system_key);

-- ============================================================================
-- FACT_LOAN
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_fact_loan_customer
    ON dw.fact_loan (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_loan_time
    ON dw.fact_loan (time_key);

CREATE INDEX IF NOT EXISTS idx_fact_loan_product
    ON dw.fact_loan (product_key);

CREATE INDEX IF NOT EXISTS idx_fact_loan_risk
    ON dw.fact_loan (risk_segment_key);

CREATE INDEX IF NOT EXISTS idx_fact_loan_source
    ON dw.fact_loan (source_system_key);

-- ============================================================================
-- FACT_PAYMENT
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_fact_payment_loan
    ON dw.fact_payment (loan_key);

CREATE INDEX IF NOT EXISTS idx_fact_payment_customer
    ON dw.fact_payment (customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_payment_time
    ON dw.fact_payment (time_key);

CREATE INDEX IF NOT EXISTS idx_fact_payment_product
    ON dw.fact_payment (product_key);

CREATE INDEX IF NOT EXISTS idx_fact_payment_risk
    ON dw.fact_payment (risk_segment_key);

CREATE INDEX IF NOT EXISTS idx_fact_payment_source
    ON dw.fact_payment (source_system_key);