-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 03_dim_product.sql
-- Tabla      : dw.dim_product
-- Descripción:
-- Dimensión que almacena la información descriptiva de los productos
-- financieros ofrecidos por la entidad.
-- ============================================================================

CREATE TABLE IF NOT EXISTS dw.dim_product (

    -- Clave sustituta
    product_key SMALLINT GENERATED ALWAYS AS IDENTITY,

    -- Clave de negocio
    product_code VARCHAR(30) NOT NULL,

    -- Información del producto
    product_name VARCHAR(100) NOT NULL,
    product_category VARCHAR(50),
    loan_type VARCHAR(50),
    currency CHAR(3),

    -- Restricciones
    CONSTRAINT pk_dim_product
        PRIMARY KEY (product_key),

    CONSTRAINT uq_dim_product_code
        UNIQUE (product_code),

    CONSTRAINT chk_dim_product_currency
        CHECK (
            currency IS NULL
            OR LENGTH(currency) = 3
        )

);

-- ============================================================================
-- Comentarios
-- ============================================================================

COMMENT ON TABLE dw.dim_product IS
'Dimensión que almacena el catálogo corporativo de productos financieros.';

COMMENT ON COLUMN dw.dim_product.product_key IS
'Clave sustituta de la dimensión.';

COMMENT ON COLUMN dw.dim_product.product_code IS
'Código único del producto financiero.';

COMMENT ON COLUMN dw.dim_product.product_name IS
'Nombre del producto financiero.';

COMMENT ON COLUMN dw.dim_product.product_category IS
'Categoría del producto financiero.';

COMMENT ON COLUMN dw.dim_product.loan_type IS
'Tipo de crédito asociado al producto.';

COMMENT ON COLUMN dw.dim_product.currency IS
'Código ISO de la moneda utilizada por el producto.';