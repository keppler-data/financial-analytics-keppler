-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 10_constraints.sql
-- Descripción:
-- Restricciones adicionales del modelo dimensional.
-- ============================================================================

-- ============================================================================
-- FACT_APPLICATION
-- ============================================================================

ALTER TABLE dw.fact_application
ADD CONSTRAINT chk_application_status
CHECK (
    application_status IN (
        'APPROVED',
        'REJECTED',
        'PENDING',
        'CANCELLED'
    )
);

-- ============================================================================
-- FACT_LOAN
-- ============================================================================

ALTER TABLE dw.fact_loan
ADD CONSTRAINT chk_interest_rate_range
CHECK (
    interest_rate IS NULL
    OR (
        interest_rate >= 0
        AND interest_rate <= 100
    )
);

-- ============================================================================
-- FACT_PAYMENT
-- ============================================================================

ALTER TABLE dw.fact_payment
ADD CONSTRAINT chk_payment_components
CHECK (
    principal_paid IS NULL
    OR interest_paid IS NULL
    OR payment_amount >= (principal_paid + interest_paid)
);

-- ============================================================================
-- DIM_CUSTOMER
-- ============================================================================

ALTER TABLE dw.dim_customer
ADD CONSTRAINT chk_gender
CHECK (
    gender IS NULL
    OR gender IN (
        'F',
        'M',
        'OTHER'
    )
);

-- ============================================================================
-- DIM_PRODUCT
-- ============================================================================

ALTER TABLE dw.dim_product
ADD CONSTRAINT chk_currency_format
CHECK (
    currency IS NULL
    OR char_length(currency) = 3
);

-- ============================================================================
-- DIM_RISK_SEGMENT
-- ============================================================================

ALTER TABLE dw.dim_risk_segment
ADD CONSTRAINT chk_default_probability_range
CHECK (
    default_probability IS NULL
    OR (
        default_probability >= 0
        AND default_probability <= 1
    )
);