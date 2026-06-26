{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/intermediate/int_home_credit_consolidated/',
    s3_data_dir='s3://keppler-data-architecture/intermediate/int_home_credit_consolidated/',
    format='parquet'
) }}

WITH app AS (
    SELECT *
    FROM {{ source('silver', 'application_train') }}
),

bureau_agg AS (
    SELECT 
        sk_id_curr,
        COUNT(sk_id_bureau) as total_bureau_loans,
        AVG(amt_credit_sum) as avg_bureau_credit_sum,
        AVG(amt_credit_sum_debt) as avg_bureau_debt
    FROM {{ source('silver', 'bureau') }}
    GROUP BY sk_id_curr
),

prev_app_agg AS (
    SELECT 
        sk_id_curr,
        COUNT(sk_id_prev) as total_previous_apps,
        AVG(amt_credit) as avg_prev_credit,
        -- Podríamos agregar más variables numéricas
        MAX(amt_credit) as max_prev_credit
    FROM {{ source('silver', 'previous_application') }}
    GROUP BY sk_id_curr
)

SELECT 
    a.*,
    
    -- Variables agregadas de Bureau
    COALESCE(b.total_bureau_loans, 0) as total_bureau_loans,
    b.avg_bureau_credit_sum,
    b.avg_bureau_debt,
    
    -- Variables agregadas de Previous Applications
    COALESCE(p.total_previous_apps, 0) as total_previous_apps,
    p.avg_prev_credit,
    p.max_prev_credit

FROM app a
LEFT JOIN bureau_agg b ON a.sk_id_curr = b.sk_id_curr
LEFT JOIN prev_app_agg p ON a.sk_id_curr = p.sk_id_curr
