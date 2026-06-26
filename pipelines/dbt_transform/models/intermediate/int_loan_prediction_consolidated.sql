{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/intermediate/int_loan_prediction_consolidated/',
    s3_data_dir='s3://keppler-data-architecture/intermediate/int_loan_prediction_consolidated/',
    format='parquet'
) }}

-- Modelo base temporal.
SELECT 
    CASE WHEN Loan_Status = 'N' THEN 1 ELSE 0 END as is_default,
    * 
FROM {{ source('silver', 'train_u6lujux_cvtuz9i') }}
