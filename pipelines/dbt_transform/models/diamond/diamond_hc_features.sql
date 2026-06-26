{{ config(
    materialized='table',
    table_type='hive',
    external_location='s3://keppler-data-architecture/diamond/diamond_hc_features/',
    s3_data_dir='s3://keppler-data-architecture/diamond/diamond_hc_features/',
    format='parquet'
) }}

SELECT
    sk_id_curr as id,
    is_default,
    
    {% set features = var('home_credit_features', []) %}
    
    {% if features | length > 0 %}
        {% for feature in features %}
            {{ feature }}{% if not loop.last %},{% endif %}
        {% endfor %}
    {% else %}
        -- Fallback de seguridad si falla ML
        cast(null as double) as dummy_feature
    {% endif %}

FROM {{ ref('int_home_credit_consolidated') }}
