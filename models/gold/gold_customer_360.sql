-- models/gold/gold_customer_360.sql

{{ config(
    materialized='table',
    schema='gold',
    unique_key='customer_id',
    alias='gold_customer_360'
) }}

WITH dim_customers AS (
    SELECT 
        customer_id,
        first_name,
        last_name,
        email,
        created_at AS customer_onboarding_date
    FROM {{ ref('dim_customers') }} -- Origen: ETL Core / Modelos base de SCRUM-84
),

fct_loan_balances AS (
    SELECT 
        customer_id,
        COUNT(loan_id) AS total_active_loans,
        SUM(current_balance) AS total_outstanding_balance,
        SUM(original_amount) AS total_allocated_credit
    FROM {{ ref('fct_loans') }} -- Origen: ETL Core / Modelos de balances de SCRUM-84
    WHERE is_active = 1
    GROUP BY customer_id
),

agg_installment_history AS (
    SELECT 
        customer_id,
        SUM(total_installments_scheduled) AS historical_installments_count,
        SUM(total_amount_due) AS total_amount_due_historic,
        SUM(total_amount_paid) AS total_amount_paid_historic,
        MAX(max_days_overdue) AS historical_max_days_mora
    FROM {{ ref('agg_customer_installment_history') }} -- Origen: ELT Intermediate / SCRUM-73
    GROUP BY customer_id
),

behavior_features AS (
    SELECT 
        customer_id,
        avg_payment_delay_3m,
        avg_payment_delay_6m,
        avg_payment_delay_12m,
        missed_payment_count_90d,
        payment_consistency_score
    FROM {{ ref('fct_customer_payment_behavior_features') }} -- Origen: ELT Intermediate / SCRUM-75
    -- Filtramos por el último mes de procesamiento activo disponible para la foto 360
    WHERE period_month = TO_CHAR(CURRENT_DATE - INTERVAL '1 month', 'YYYY-MM')
),

bureau_signals AS (
    SELECT 
        customer_id,
        bureau_score AS current_bureau_score,
        bureau_score_trend_3m,
        bureau_score_trend_12m,
        inquiry_count AS bureau_inquiries_last_period
    FROM {{ ref('agg_customer_bureau_history') }} -- Origen: ELT Intermediate / SCRUM-76
    QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY bureau_date DESC) = 1
)

SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.customer_onboarding_date,
    
    -- Métricas Operacionales de Préstamos (Manejo seguro de nulos mediante COALESCE)
    COALESCE(l.total_active_loans, 0) AS total_active_loans,
    COALESCE(l.total_outstanding_balance, 0.00) AS total_outstanding_balance,
    COALESCE(l.total_allocated_credit, 0.00) AS total_allocated_credit,
    
    -- Métricas Históricas Internas de Pago
    COALESCE(i.historical_installments_count, 0) AS historical_installments_count,
    COALESCE(i.total_amount_due_historic, 0.00) AS total_amount_due_historic,
    COALESCE(i.total_amount_paid_historic, 0.00) AS total_amount_paid_historic,
    COALESCE(i.historical_max_days_mora, 0) AS historical_max_days_mora,
    
    -- Señales de Comportamiento e Inteligencia de Riesgo (ELT Features)
    COALESCE(b.avg_payment_delay_3m, 0.00) AS avg_payment_delay_3m,
    COALESCE(b.avg_payment_delay_6m, 0.00) AS avg_payment_delay_6m,
    COALESCE(b.avg_payment_delay_12m, 0.00) AS avg_payment_delay_12m,
    COALESCE(b.missed_payment_count_90d, 0) AS missed_payment_count_90d,
    COALESCE(b.payment_consistency_score, 100.00) AS payment_consistency_score,
    
    -- Señales Externas del Buró de Crédito
    COALESCE(bu.current_bureau_score, 0) AS current_bureau_score,
    COALESCE(bu.bureau_score_trend_3m, 0) AS bureau_score_trend_3m,
    COALESCE(bu.bureau_score_trend_12m, 0) AS bureau_score_trend_12m,
    COALESCE(bu.bureau_inquiries_last_period, 0) AS bureau_inquiries_last_period,
    
    -- Timestamp de Auditoría dbt
    CURRENT_TIMESTAMP AS dbt_updated_at

FROM dim_customers c
LEFT JOIN fct_loan_balances l     ON c.customer_id = l.customer_id
LEFT JOIN agg_installment_history i ON c.customer_id = i.customer_id
LEFT JOIN behavior_features b     ON c.customer_id = b.customer_id
LEFT JOIN bureau_signals bu       ON c.customer_id = bu.customer_id