{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/intermediate/int_lending_club_consolidated/',
    s3_data_dir='s3://keppler-data-architecture/intermediate/int_lending_club_consolidated/',
    format='parquet'
) }}

-- Modelo base temporal. 
SELECT 
    CASE 
        WHEN loan_status IN ('Charged Off', 'Default', 'Does not meet the credit policy. Status:Charged Off') THEN 1
        WHEN loan_status IN ('Fully Paid', 'Does not meet the credit policy. Status:Fully Paid') THEN 0
        ELSE NULL
    END as is_default,
    * 
FROM {{ source('silver', 'accepted_2007_to_2018q4') }}
WHERE loan_status IN ('Charged Off', 'Default', 'Fully Paid', 'Does not meet the credit policy. Status:Charged Off', 'Does not meet the credit policy. Status:Fully Paid')
