-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 07_fact_loan.sql
-- Tabla      : dw.fact_loan
-- Descripción:
-- Tabla de hechos que almacena los créditos aprobados y desembolsados.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.fact_loan (

    -- Clave sustituta
    loan_key BIGINT GENERATED ALWAYS AS IDENTITY,

    -- Identificador de negocio
    loan_id VARCHAR(50) NOT NULL,

    -- Dimensiones
    customer_key BIGINT NOT NULL,
    time_key INTEGER NOT NULL,
    product_key SMALLINT NOT NULL,
    risk_segment_key SMALLINT NOT NULL,
    source_system_key SMALLINT NOT NULL,

    -- Métricas
    loan_amount NUMERIC(18,2) NOT NULL,
    interest_rate NUMERIC(8,4),
    term_months SMALLINT,
    outstanding_balance NUMERIC(18,2),

    -- Restricciones
    CONSTRAINT pk_fact_loan
        PRIMARY KEY (loan_key),

    CONSTRAINT uq_fact_loan_id
        UNIQUE (loan_id),

    CONSTRAINT chk_loan_amount
        CHECK (loan_amount > 0),

    CONSTRAINT chk_interest_rate
        CHECK (
            interest_rate IS NULL
            OR interest_rate >= 0
        ),

    CONSTRAINT chk_term_months
        CHECK (
            term_months IS NULL
            OR term_months > 0
        ),

    CONSTRAINT chk_outstanding_balance
        CHECK (
            outstanding_balance IS NULL
            OR outstanding_balance >= 0
        ),

    -- Relaciones
    CONSTRAINT fk_fact_loan_customer
        FOREIGN KEY (customer_key)
        REFERENCES dw.dim_customer(customer_key),

    CONSTRAINT fk_fact_loan_time
        FOREIGN KEY (time_key)
        REFERENCES dw.dim_time(time_key),

    CONSTRAINT fk_fact_loan_product
        FOREIGN KEY (product_key)
        REFERENCES dw.dim_product(product_key),

    CONSTRAINT fk_fact_loan_risk
        FOREIGN KEY (risk_segment_key)
        REFERENCES dw.dim_risk_segment(risk_segment_key),

    CONSTRAINT fk_fact_loan_source
        FOREIGN KEY (source_system_key)
        REFERENCES dw.dim_source_system(source_system_key)

);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.fact_loan IS
'Tabla de hechos que almacena los créditos aprobados y desembolsados.';

COMMENT ON COLUMN dw.fact_loan.loan_key IS
'Clave sustituta de la tabla de hechos.';

COMMENT ON COLUMN dw.fact_loan.loan_id IS
'Identificador de negocio del crédito.';

COMMENT ON COLUMN dw.fact_loan.loan_amount IS
'Monto desembolsado del crédito.';

COMMENT ON COLUMN dw.fact_loan.interest_rate IS
'Tasa de interés aplicada al crédito.';

COMMENT ON COLUMN dw.fact_loan.term_months IS
'Plazo del crédito expresado en meses.';

COMMENT ON COLUMN dw.fact_loan.outstanding_balance IS
'Saldo pendiente del crédito.';