-- ============================================================================
-- Proyecto   : Plataforma Analítica Financiera
-- Esquema    : Data Warehouse
-- Archivo    : 00_create_schema.sql
-- Descripción:
-- Creación del esquema del Data Warehouse.
-- ============================================================================

-- Crear esquema
CREATE SCHEMA IF NOT EXISTS dw;

COMMENT ON SCHEMA dw IS
'Esquema que almacena el modelo dimensional del Data Warehouse.';