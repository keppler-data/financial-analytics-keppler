{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/dim_lc_details/',
    s3_data_dir='s3://keppler-data-architecture/gold/dim_lc_details/',
    format='parquet'
) }}

SELECT
    to_hex(md5(to_utf8(concat(cast(id as varchar), 'LC')))) as loan_key,
    *
FROM {{ ref('int_lending_club_consolidated') }}
