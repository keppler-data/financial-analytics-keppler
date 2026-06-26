{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/diamond/diamond_lp_features/',
    s3_data_dir='s3://keppler-data-architecture/diamond/diamond_lp_features/',
    format='parquet'
) }}

SELECT
    Loan_ID as id,
    is_default,
    
    {% set features = var('loan_prediction_features', []) %}
    
    {% if features | length > 0 %}
        {% for feature in features %}
            "{{ feature }}"{% if not loop.last %},{% endif %}
        {% endfor %}
    {% else %}
        cast(null as double) as dummy_feature
    {% endif %}

FROM {{ ref('int_loan_prediction_consolidated') }}
