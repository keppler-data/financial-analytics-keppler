-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 06_fact_application.sql
-- Tabla      : dw.fact_application
-- Descripción:
-- Tabla de hechos que almacena las solicitudes de crédito realizadas por los
-- clientes.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.fact_application (

    -- Clave sustituta
    application_key BIGINT GENERATED ALWAYS AS IDENTITY,

    -- Identificador de negocio
    application_id VARCHAR(50) NOT NULL,

    -- Dimensiones
    customer_key BIGINT NOT NULL,
    time_key INTEGER NOT NULL,
    product_key SMALLINT NOT NULL,
    risk_segment_key SMALLINT NOT NULL,
    source_system_key SMALLINT NOT NULL,

    -- Métricas
    requested_amount NUMERIC(18,2) NOT NULL,
    approved_amount NUMERIC(18,2),
    application_score NUMERIC(10,4),

    -- Estado de la solicitud
    application_status VARCHAR(30) NOT NULL,

    -- Restricciones
    CONSTRAINT pk_fact_application
        PRIMARY KEY (application_key),

    CONSTRAINT uq_fact_application_id
        UNIQUE (application_id),

    CONSTRAINT chk_requested_amount
        CHECK (requested_amount > 0),

    CONSTRAINT chk_approved_amount
        CHECK (
            approved_amount IS NULL
            OR approved_amount >= 0
        ),

    CONSTRAINT chk_application_score
        CHECK (
            application_score IS NULL
            OR application_score >= 0
        ),

    -- Relaciones
    CONSTRAINT fk_fact_application_customer
        FOREIGN KEY (customer_key)
        REFERENCES dw.dim_customer(customer_key),

    CONSTRAINT fk_fact_application_time
        FOREIGN KEY (time_key)
        REFERENCES dw.dim_time(time_key),

    CONSTRAINT fk_fact_application_product
        FOREIGN KEY (product_key)
        REFERENCES dw.dim_product(product_key),

    CONSTRAINT fk_fact_application_risk
        FOREIGN KEY (risk_segment_key)
        REFERENCES dw.dim_risk_segment(risk_segment_key),

    CONSTRAINT fk_fact_application_source
        FOREIGN KEY (source_system_key)
        REFERENCES dw.dim_source_system(source_system_key)

);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.fact_application IS
'Tabla de hechos que almacena las solicitudes de crédito realizadas por los clientes.';

COMMENT ON COLUMN dw.fact_application.application_key IS
'Clave sustituta de la tabla de hechos.';

COMMENT ON COLUMN dw.fact_application.application_id IS
'Identificador de negocio de la solicitud.';

COMMENT ON COLUMN dw.fact_application.requested_amount IS
'Monto solicitado por el cliente.';

COMMENT ON COLUMN dw.fact_application.approved_amount IS
'Monto aprobado para la solicitud.';

COMMENT ON COLUMN dw.fact_application.application_score IS
'Puntaje obtenido durante el proceso de evaluación.';

COMMENT ON COLUMN dw.fact_application.application_status IS
'Estado de la solicitud de crédito.';