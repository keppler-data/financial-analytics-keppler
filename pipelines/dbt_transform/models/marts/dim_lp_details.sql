{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/dim_lp_details/',
    s3_data_dir='s3://keppler-data-architecture/gold/dim_lp_details/',
    format='parquet'
) }}

SELECT
    to_hex(md5(to_utf8(concat(cast(loan_id as varchar), 'LP')))) as loan_key,
    *
FROM {{ ref('int_loan_prediction_consolidated') }}
