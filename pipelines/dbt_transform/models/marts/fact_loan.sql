{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/fact_loan/',
    s3_data_dir='s3://keppler-data-architecture/gold/fact_loan/',
    format='parquet'
) }}

WITH home_credit AS (
    SELECT 
        to_hex(md5(to_utf8(concat(cast(sk_id_curr as varchar), 'HC')))) as loan_key,
        to_hex(md5(to_utf8(cast(sk_id_curr as varchar)))) as customer_key,
        'Home Credit' as source_system,
        is_default as target,
        cast(amt_credit as double) as loan_amount,
        cast(amt_income_total as double) as annual_income
    FROM {{ ref('int_home_credit_consolidated') }}
),

lending_club AS (
    SELECT 
        to_hex(md5(to_utf8(concat(cast(id as varchar), 'LC')))) as loan_key,
        to_hex(md5(to_utf8(cast(emp_title as varchar)))) as customer_key,
        'Lending Club' as source_system,
        is_default as target,
        cast(loan_amnt as double) as loan_amount,
        cast(annual_inc as double) as annual_income
    FROM {{ ref('int_lending_club_consolidated') }}
),

give_me_some_credit AS (
    SELECT
        to_hex(md5(to_utf8(concat(cast(c0 as varchar), 'GMSC')))) as loan_key,
        to_hex(md5(to_utf8(cast(c0 as varchar)))) as customer_key,
        'Give Me Some Credit' as source_system,
        is_default as target,
        cast(null as double) as loan_amount,
        cast(cast(monthlyincome as double) * 12 as double) as annual_income
    FROM {{ ref('int_give_me_some_credit_consolidated') }}
),

loan_prediction AS (
    SELECT
        to_hex(md5(to_utf8(concat(cast(loan_id as varchar), 'LP')))) as loan_key,
        to_hex(md5(to_utf8(cast(loan_id as varchar)))) as customer_key,
        'Loan Prediction' as source_system,
        is_default as target,
        cast(cast(loanamount as double) * 1000 as double) as loan_amount,
        cast(cast(applicantincome as double) * 12 as double) as annual_income
    FROM {{ ref('int_loan_prediction_consolidated') }}
)

SELECT * FROM home_credit
UNION ALL
SELECT * FROM lending_club
UNION ALL
SELECT * FROM give_me_some_credit
UNION ALL
SELECT * FROM loan_prediction
