{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/diamond/diamond_gmsc_features/',
    s3_data_dir='s3://keppler-data-architecture/diamond/diamond_gmsc_features/',
    format='parquet'
) }}

SELECT
    "Unnamed: 0" as id,
    is_default,
    
    {% set features = var('give_me_some_credit_features', []) %}
    
    {% if features | length > 0 %}
        {% for feature in features %}
            "{{ feature }}"{% if not loop.last %},{% endif %}
        {% endfor %}
    {% else %}
        cast(null as double) as dummy_feature
    {% endif %}

FROM {{ ref('int_give_me_some_credit_consolidated') }}
