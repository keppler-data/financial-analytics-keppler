{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/diamond/diamond_risk_features/',
    s3_data_dir='s3://keppler-data-architecture/diamond/diamond_risk_features/',
    format='parquet'
) }}

-- =======================================================================
-- NOTA: Este es un modelo semilla/plantilla.
-- Una vez ejecutes el script de Machine Learning (gold_to_diamond_ml.py)
-- revisa el archivo Markdown de Feature Importance en S3.
-- Reemplaza el SELECT * por las 20 columnas que ganaron en importancia.
-- Esto eliminará el "ruido" y la "fuga de datos" para siempre.
-- =======================================================================

SELECT
    sk_id_curr,
    is_default,
    
    -- [INSERTA AQUÍ LAS TOP 20 VARIABLES OBTENIDAS POR RANDOM FOREST]
    -- Ejemplo:
    -- ext_source_1,
    -- ext_source_2,
    -- ext_source_3,
    -- total_bureau_loans,
    -- avg_bureau_debt
    
    -- Por ahora traemos todo para evitar que dbt falle al compilar
    *

FROM {{ ref('int_home_credit_consolidated') }}
