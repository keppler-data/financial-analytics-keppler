{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/dim_customer/',
    s3_data_dir='s3://keppler-data-architecture/gold/dim_customer/',
    format='parquet'
) }}

WITH home_credit AS (
    SELECT 
        -- Claves
        md5(cast(sk_id_curr as varchar)) as customer_key,
        cast(sk_id_curr as varchar) as customer_id,
        'Home Credit' as source_system,
        
        -- Top Variables de ML (Demográficas y de Comportamiento)
        ext_source_1,
        ext_source_2,
        ext_source_3,
        cast(days_birth / -365.0 as integer) as years_birth,
        cast(days_employed / -365.0 as integer) as years_employed,
        own_car_age,
        apartments_mode,
        floorsmax_mode,
        region_rating_client_w_city,
        flag_document_3,
        flag_emp_phone,
        cast(days_id_publish / -365.0 as integer) as years_id_publish,
        livingarea_mode,
        def_30_cnt_social_circle,
        region_rating_client,
        floorsmax_avg
        
    FROM {{ ref('int_home_credit_consolidated') }}
),

give_me_some_credit AS (
    SELECT
        md5(cast("Unnamed: 0" as varchar)) as customer_key,
        cast("Unnamed: 0" as varchar) as customer_id,
        'Give Me Some Credit' as source_system,
        
        -- Mapeo de lo que existe
        cast(null as double) as ext_source_1,
        cast(null as double) as ext_source_2,
        cast(null as double) as ext_source_3,
        cast(age as integer) as years_birth,
        cast(null as integer) as years_employed,
        cast(null as double) as own_car_age,
        cast(null as double) as apartments_mode,
        cast(null as double) as floorsmax_mode,
        cast(null as double) as region_rating_client_w_city,
        cast(null as integer) as flag_document_3,
        cast(null as integer) as flag_emp_phone,
        cast(null as integer) as years_id_publish,
        cast(null as double) as livingarea_mode,
        cast(null as double) as def_30_cnt_social_circle,
        cast(null as double) as region_rating_client,
        cast(null as double) as floorsmax_avg
        
    -- FROM source('silver', 'cs_training')
    -- Usamos un dummy hasta que el pipeline Silver para este banco esté activo
    FROM (SELECT 1 as "Unnamed: 0", 30 as age LIMIT 0) AS dummy
)

SELECT * FROM home_credit
UNION ALL
SELECT * FROM give_me_some_credit
