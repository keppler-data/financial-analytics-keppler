{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/fact_loan/',
    s3_data_dir='s3://keppler-data-architecture/gold/fact_loan/',
    format='parquet'
) }}

WITH home_credit AS (
    SELECT 
        -- Claves
        md5(concat(cast(sk_id_curr as varchar), 'HC')) as loan_key,
        md5(cast(sk_id_curr as varchar)) as customer_key,
        'Home Credit' as source_system,
        
        -- Target de Morosidad (Para entrenamiento y validación final)
        is_default as target,
        
        -- Variables de Negocio (Monto y Crédito Buro)
        amt_goods_price,
        avg_bureau_debt,
        avg_bureau_credit_sum
        
    FROM {{ ref('int_home_credit_consolidated') }}
),

give_me_some_credit AS (
    SELECT
        md5(concat(cast("Unnamed: 0" as varchar), 'GMSC')) as loan_key,
        md5(cast("Unnamed: 0" as varchar)) as customer_key,
        'Give Me Some Credit' as source_system,
        
        -- Mapeo
        SeriousDlqin2yrs as target,
        cast(null as double) as amt_goods_price,
        DebtRatio as avg_bureau_debt, -- Proxy aproximado
        MonthlyIncome as avg_bureau_credit_sum -- Proxy aproximado
        
    -- FROM source('silver', 'cs_training')
    -- Usamos un dummy hasta que tu pipeline Silver esté listo
    FROM (SELECT 1 as "Unnamed: 0", 0 as SeriousDlqin2yrs, 0.5 as DebtRatio, 5000 as MonthlyIncome LIMIT 0) AS dummy
)

SELECT * FROM home_credit
UNION ALL
SELECT * FROM give_me_some_credit
