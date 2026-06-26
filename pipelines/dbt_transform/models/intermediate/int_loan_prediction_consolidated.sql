{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/intermediate/int_loan_prediction_consolidated/',
    s3_data_dir='s3://keppler-data-architecture/intermediate/int_loan_prediction_consolidated/',
    format='parquet'
) }}

-- Modelo base temporal.
SELECT * 
FROM {{ source('silver', 'train_u6lujux_cvtuz9i') }}
