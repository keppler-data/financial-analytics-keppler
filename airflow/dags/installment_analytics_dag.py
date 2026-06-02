# airflow/dags/installment_analytics_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.tasks.installment_aggregations import compute_installment_aggregations, register_in_glue_catalog

default_args = {
    'owner': 'ELT_P2_Hugo_Perez',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_intermediate_job(**kwargs):
    # Definición de rutas del Data Lake S3
    silver_s3_uri = "s3a://kepler-silver/financial/tables/installment_history"
    intermediate_s3_uri = "s3a://kepler-intermediate/financial/aggregations/customer_installments"
    
    # Ejecutar la agregación pesada en PySpark
    compute_installment_aggregations(silver_s3_uri, intermediate_s3_uri)
    
    # Registrar la estructura en el catálogo corporativo de AWS Glue
    register_in_glue_catalog(
        database_name="kepler_intermediate_db",
        table_name="agg_customer_installment_history",
        s3_path=intermediate_s3_uri
    )

with DAG(
    'kepler_installment_history_intermediate_pipeline',
    default_args=default_args,
    description='Agregaciones temporales de cuotas por cliente en capa Intermediate',
    schedule_interval='@monthly', # Se ejecuta mensualmente para consolidar cierres de períodos
    catchup=False,
) as dag:

    task_compute_aggregations = PythonOperator(
        task_id='compute_and_catalog_installment_metrics',
        python_callable=run_intermediate_job
    )

    task_compute_aggregations