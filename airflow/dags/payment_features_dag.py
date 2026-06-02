# airflow/dags/payment_features_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.tasks.payment_behavior_features import compute_payment_behavior_features
from airflow.tasks.installment_aggregations import register_in_glue_catalog

default_args = {
    'owner': 'ELT_P2_Hugo_Perez',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_feature_engineering_job(**kwargs):
    source_uri = "s3a://kepler-intermediate/financial/aggregations/customer_installments"
    target_uri = "s3a://kepler-intermediate/financial/features/payment_behavior"
    
    # Calcular variables móviles de riesgo
    compute_payment_behavior_features(source_uri, target_uri)
    
    # Registro formal en el catálogo
    register_in_glue_catalog(
        database_name="kepler_intermediate_db",
        table_name="fct_customer_payment_behavior_features",
        s3_path=target_uri
    )

with DAG(
    'kepler_payment_behavior_features_pipeline',
    default_args=default_args,
    description='Feature Engineering de comportamiento y retrasos de pago para modelos de riesgo',
    schedule_interval='@monthly',
    catchup=False,
) as dag:

    task_generate_features = PythonOperator(
        task_id='compute_and_catalog_behavior_features',
        python_callable=run_feature_engineering_job
    )

    task_generate_features