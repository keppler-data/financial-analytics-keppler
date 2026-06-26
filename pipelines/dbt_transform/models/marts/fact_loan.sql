{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/fact_loan/',
    s3_data_dir='s3://keppler-data-architecture/gold/fact_loan/',
    format='parquet'
) }}

WITH home_credit AS (
    SELECT 
        md5(concat(cast(sk_id_curr as varchar), 'HC')) as loan_key,
        md5(cast(sk_id_curr as varchar)) as customer_key,
        'Home Credit' as source_system,
        is_default as target,
        
        -- Business Mappings
        cast(AMT_CREDIT as double) as loan_amount,
        cast(AMT_INCOME_TOTAL as double) as annual_income,
        cast(DAYS_BIRTH / -365.0 as integer) as age_years
        
    FROM {{ ref('int_home_credit_consolidated') }}
),

lending_club AS (
    SELECT 
        md5(concat(cast(id as varchar), 'LC')) as loan_key,
        md5(cast(emp_title as varchar)) as customer_key, -- Proxy since there is no customer id
        'Lending Club' as source_system,
        is_default as target,
        
        cast(loan_amnt as double) as loan_amount,
        cast(annual_inc as double) as annual_income,
        cast(null as integer) as age_years
        
    FROM {{ ref('int_lending_club_consolidated') }}
),

give_me_some_credit AS (
    SELECT
        md5(concat(cast("Unnamed: 0" as varchar), 'GMSC')) as loan_key,
        md5(cast("Unnamed: 0" as varchar)) as customer_key,
        'Give Me Some Credit' as source_system,
        is_default as target,
        
        cast(null as double) as loan_amount,
        cast(MonthlyIncome * 12 as double) as annual_income,
        cast(age as integer) as age_years
        
    FROM {{ ref('int_give_me_some_credit_consolidated') }}
),

loan_prediction AS (
    SELECT
        md5(concat(cast(Loan_ID as varchar), 'LP')) as loan_key,
        md5(cast(Loan_ID as varchar)) as customer_key,
        'Loan Prediction' as source_system,
        is_default as target,
        
        cast(LoanAmount * 1000 as double) as loan_amount,
        cast(ApplicantIncome * 12 as double) as annual_income,
        cast(null as integer) as age_years
        
    FROM {{ ref('int_loan_prediction_consolidated') }}
)

SELECT * FROM home_credit
UNION ALL
SELECT * FROM lending_club
UNION ALL
SELECT * FROM give_me_some_credit
UNION ALL
SELECT * FROM loan_prediction
