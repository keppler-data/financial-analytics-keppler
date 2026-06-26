{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/dim_hc_details/',
    s3_data_dir='s3://keppler-data-architecture/gold/dim_hc_details/',
    format='parquet'
) }}

SELECT
    to_hex(md5(to_utf8(concat(cast(sk_id_curr as varchar), 'HC')))) as loan_key,
    *
FROM {{ ref('int_home_credit_consolidated') }}
