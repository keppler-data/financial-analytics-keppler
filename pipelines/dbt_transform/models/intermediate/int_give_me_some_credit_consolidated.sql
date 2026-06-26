{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/intermediate/int_give_me_some_credit_consolidated/',
    s3_data_dir='s3://keppler-data-architecture/intermediate/int_give_me_some_credit_consolidated/',
    format='parquet'
) }}

-- Modelo base temporal. 
SELECT 
    SeriousDlqin2yrs as is_default,
    * 
FROM {{ source('silver', 'cs_training') }}
