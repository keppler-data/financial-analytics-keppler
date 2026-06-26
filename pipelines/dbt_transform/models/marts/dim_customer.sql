{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/gold/dim_customer/',
    s3_data_dir='s3://keppler-data-architecture/gold/dim_customer/',
    format='parquet'
) }}

WITH home_credit AS (
    SELECT 
        to_hex(md5(to_utf8(cast(sk_id_curr as varchar)))) as customer_key,
        cast(sk_id_curr as varchar) as customer_id,
        'Home Credit' as source_system,
        try_cast(years_birth as integer) as age_years,
        try_cast(years_employed as integer) as employment_years,
        cast(code_gender as varchar) as gender
    FROM {{ ref('int_home_credit_consolidated') }}
),

lending_club AS (
    SELECT 
        to_hex(md5(to_utf8(cast(emp_title as varchar)))) as customer_key,
        cast(emp_title as varchar) as customer_id,
        'Lending Club' as source_system,
        cast(null as integer) as age_years,
        cast(emp_length as varchar) as employment_years_str, -- LC has string e.g. "10+ years"
        cast(null as varchar) as gender
    FROM {{ ref('int_lending_club_consolidated') }}
),

give_me_some_credit AS (
    SELECT
        to_hex(md5(to_utf8(cast(c0 as varchar)))) as customer_key,
        cast(c0 as varchar) as customer_id,
        'Give Me Some Credit' as source_system,
        try_cast(age as integer) as age_years,
        cast(null as integer) as employment_years,
        cast(null as varchar) as gender
    FROM {{ ref('int_give_me_some_credit_consolidated') }}
),

loan_prediction AS (
    SELECT
        to_hex(md5(to_utf8(cast(loan_id as varchar)))) as customer_key,
        cast(loan_id as varchar) as customer_id,
        'Loan Prediction' as source_system,
        cast(null as integer) as age_years,
        cast(null as integer) as employment_years,
        cast(gender as varchar) as gender
    FROM {{ ref('int_loan_prediction_consolidated') }}
)

SELECT customer_key, customer_id, source_system, age_years, cast(employment_years as varchar) as employment_years, gender FROM home_credit
UNION ALL
SELECT customer_key, customer_id, source_system, age_years, employment_years_str as employment_years, gender FROM lending_club
UNION ALL
SELECT customer_key, customer_id, source_system, age_years, cast(employment_years as varchar) as employment_years, gender FROM give_me_some_credit
UNION ALL
SELECT customer_key, customer_id, source_system, age_years, cast(employment_years as varchar) as employment_years, gender FROM loan_prediction
