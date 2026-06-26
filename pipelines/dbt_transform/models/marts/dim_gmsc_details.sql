{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/dim_gmsc_details/',
    s3_data_dir='s3://keppler-data-architecture/gold/dim_gmsc_details/',
    format='parquet'
) }}

SELECT
    to_hex(md5(to_utf8(concat(cast(unnamed_0 as varchar), 'GMSC')))) as loan_key,
    *
FROM {{ ref('int_give_me_some_credit_consolidated') }}
