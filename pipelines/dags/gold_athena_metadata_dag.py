# pipelines/dags/gold_athena_metadata_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from pipelines.tasks.gold_athena_catalog import configure_glue_and_athena_gold

default_args = {
    'owner': 'ELT_P2_Hugo_Perez',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_metadata_sync():
    database_gold = "kepler_gold_db"
    s3_athena_results = "s3://kepler-athena-query-results/gold_queries/"
    
    configure_glue_and_athena_gold(
        database_name=database_gold,
        s3_output_athena=s3_athena_results
    )

with DAG(
    'kepler_gold_athena_catalog_pipeline',
    default_args=default_args,
    description='Sincronización automatizada de Glue Catalog y Athena sobre la capa Gold en S3',
    schedule_interval='@daily',
    catchup=False,
) as dag:

    task_sync_catalog = PythonOperator(
        task_id='sync_glue_athena_catalog_gold',
        python_callable=run_metadata_sync
    )

    task_sync_catalog