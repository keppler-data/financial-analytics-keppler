{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/intermediate/int_lending_club_consolidated/',
    s3_data_dir='s3://keppler-data-architecture/intermediate/int_lending_club_consolidated/',
    format='parquet'
) }}

-- Modelo base temporal. Se reemplazará con la lógica JOIN real cuando el pipeline Silver esté completamente auditado.
SELECT * 
FROM {{ source('silver', 'accepted_2007_to_2018q4') }}
