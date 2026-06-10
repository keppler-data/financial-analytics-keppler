# airflow/dags/bureau_governance_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.tasks.bureau_aggregations import compute_bureau_aggregations
from airflow.tasks.installment_aggregations import register_in_glue_catalog

default_args = {
    'owner': 'ELT_P2_Hugo_Perez',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_bureau_intermediate_job(**kwargs):
    silver_bureau_uri = "s3a://kepler-silver/financial/tables/bureau_history"
    intermediate_bureau_uri = "s3a://kepler-intermediate/financial/aggregations/bureau_summary"
    
    # Procesar agregados masivos externos
    compute_bureau_aggregations(silver_bureau_uri, intermediate_bureau_uri)
    
    # Registrar en el catálogo Glue
    register_in_glue_catalog(
        database_name="kepler_intermediate_db",
        table_name="agg_customer_bureau_history",
        s3_path=intermediate_bureau_uri
    )

with DAG(
    'kepler_bureau_history_intermediate_pipeline',
    default_args=default_args,
    description='Agregaciones y tendencias de comportamiento del Buró Externo en Capa Intermediate',
    schedule_interval='@monthly',
    catchup=False,
) as dag:

    task_bureau_analytics = PythonOperator(
        task_id='compute_and_catalog_bureau_trends',
        python_callable=run_bureau_intermediate_job
    )

    task_bureau_analytics