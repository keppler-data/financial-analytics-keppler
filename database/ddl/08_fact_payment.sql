-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 08_fact_payment.sql
-- Tabla      : dw.fact_payment
-- Descripción:
-- Tabla de hechos que almacena los pagos realizados sobre los créditos.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.fact_payment (

    -- Clave sustituta
    payment_key BIGINT GENERATED ALWAYS AS IDENTITY,

    -- Identificador de negocio
    payment_id VARCHAR(50) NOT NULL,

    -- Relación con el crédito
    loan_key BIGINT NOT NULL,

    -- Dimensiones
    customer_key BIGINT NOT NULL,
    time_key INTEGER NOT NULL,
    product_key SMALLINT NOT NULL,
    risk_segment_key SMALLINT NOT NULL,
    source_system_key SMALLINT NOT NULL,

    -- Métricas
    payment_amount NUMERIC(18,2) NOT NULL,
    principal_paid NUMERIC(18,2),
    interest_paid NUMERIC(18,2),
    days_past_due INTEGER,

    -- Restricciones
    CONSTRAINT pk_fact_payment
        PRIMARY KEY (payment_key),

    CONSTRAINT uq_fact_payment_id
        UNIQUE (payment_id),

    CONSTRAINT chk_payment_amount
        CHECK (payment_amount > 0),

    CONSTRAINT chk_principal_paid
        CHECK (
            principal_paid IS NULL
            OR principal_paid >= 0
        ),

    CONSTRAINT chk_interest_paid
        CHECK (
            interest_paid IS NULL
            OR interest_paid >= 0
        ),

    CONSTRAINT chk_days_past_due
        CHECK (
            days_past_due IS NULL
            OR days_past_due >= 0
        ),

    -- Claves foráneas
    CONSTRAINT fk_fact_payment_loan
        FOREIGN KEY (loan_key)
        REFERENCES dw.fact_loan (loan_key),

    CONSTRAINT fk_fact_payment_customer
        FOREIGN KEY (customer_key)
        REFERENCES dw.dim_customer (customer_key),

    CONSTRAINT fk_fact_payment_time
        FOREIGN KEY (time_key)
        REFERENCES dw.dim_time (time_key),

    CONSTRAINT fk_fact_payment_product
        FOREIGN KEY (product_key)
        REFERENCES dw.dim_product (product_key),

    CONSTRAINT fk_fact_payment_risk
        FOREIGN KEY (risk_segment_key)
        REFERENCES dw.dim_risk_segment (risk_segment_key),

    CONSTRAINT fk_fact_payment_source
        FOREIGN KEY (source_system_key)
        REFERENCES dw.dim_source_system (source_system_key)

);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.fact_payment IS
'Tabla de hechos que almacena los pagos realizados sobre los créditos.';

COMMENT ON COLUMN dw.fact_payment.payment_key IS
'Clave sustituta de la tabla de hechos.';

COMMENT ON COLUMN dw.fact_payment.payment_id IS
'Identificador de negocio del pago.';

COMMENT ON COLUMN dw.fact_payment.loan_key IS
'Referencia al crédito sobre el cual se realiza el pago.';

COMMENT ON COLUMN dw.fact_payment.payment_amount IS
'Monto total pagado.';

COMMENT ON COLUMN dw.fact_payment.principal_paid IS
'Valor aplicado al capital del crédito.';

COMMENT ON COLUMN dw.fact_payment.interest_paid IS
'Valor aplicado a intereses.';

COMMENT ON COLUMN dw.fact_payment.days_past_due IS
'Días de mora registrados al momento del pago.';