-- PostgreSQL Control Tables for Data Pipeline
-- Ejecutar en PostgreSQL para crear tablas de auditoría

-- Crear schema de control si no existe
CREATE SCHEMA IF NOT EXISTS control;

-- Tabla de control de ingestas
CREATE TABLE IF NOT EXISTS control.ingesta_log (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL,
    dataset_nombre VARCHAR(100) NOT NULL,
    fuente VARCHAR(100) NOT NULL,
    registro_count INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20),  -- 'success', 'failed'
    error_message TEXT,
    s3_path VARCHAR(500)
);

-- Tabla de control de Bronze structuring
CREATE TABLE IF NOT EXISTS control.bronze_log (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL,
    dataset_nombre VARCHAR(100) NOT NULL,
    input_count INTEGER,
    output_count INTEGER,
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20),
    output_path VARCHAR(500)
);

-- Índices para queries rápidas
CREATE INDEX IF NOT EXISTS idx_ingesta_batch ON control.ingesta_log(batch_id);
CREATE INDEX IF NOT EXISTS idx_bronze_batch ON control.bronze_log(batch_id);

-- Comentarios
COMMENT ON TABLE control.ingesta_log IS 'Log de ingestas de datos desde fuentes originales';
COMMENT ON TABLE control.bronze_log IS 'Log de procesamiento de capa Bronze';
