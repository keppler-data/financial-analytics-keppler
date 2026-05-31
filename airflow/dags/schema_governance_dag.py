# airflow/dags/schema_governance_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.tasks.schema_manager import load_pyspark_schema, apply_schema_evolution

default_args = {
    'owner': 'elt_analytics_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 20),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def execute_governed_ingestion(dataset_name, version, **kwargs):
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName(f"Governance_{dataset_name}").getOrCreate()
    
    # 1. Cargar el esquema oficial del Registro Centralizado
    expected_schema = load_pyspark_schema(dataset_name, version)
    
    # Rutas para simulación en el Data Lake
    source_csv_path = f"/opt/airflow/data/seed/{dataset_name}.csv"
    target_delta_path = f"s3a://kepler-bronze/financial/tables/{dataset_name}"
    
    try:
        # Leer aplicando el esquema del Registry para forzar tipos y formatos correctos
        new_df = spark.read.format("csv") \
            .option("header", "true") \
            .schema(expected_schema) \
            .load(source_csv_path)
            
        # Evaluar compatibilidad y escribir de forma segura en Delta Lake
        apply_schema_evolution(target_delta_path, new_df, dataset_name, version)
    except Exception as e:
        print(f"⚠️ Pipeline controlado. Ejecución omitida/manejada para {dataset_name}: {e}")

with DAG(
    'kepler_schema_governance_pipeline',
    default_args=default_args,
    description='Gobernanza de Datos y Monitoreo de Schema Evolution en Delta Lake',
    schedule_interval='@daily',
    catchup=False,
) as dag:

    task_transactions = PythonOperator(
        task_id='validate_and_ingest_transactions',
        python_callable=execute_governed_ingestion,
        op_kwargs={'dataset_name': 'transactions', 'version': 'v1'}
    )

    task_customers = PythonOperator(
        task_id='validate_and_ingest_customers',
        python_callable=execute_governed_ingestion,
        op_kwargs={'dataset_name': 'customers', 'version': 'v1'}
    )

    task_accounts = PythonOperator(
        task_id='validate_and_ingest_accounts',
        python_callable=execute_governed_ingestion,
        op_kwargs={'dataset_name': 'accounts', 'version': 'v1'}
    )

    [task_transactions, task_customers, task_accounts]