# airflow/dags/elt_pipeline_dag.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.tasks.elt_tasks import APIIngester, CSVIngester, LogIngester

default_args = {
    'owner': 'elt_analytics_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 20),
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def run_api_ingestion(endpoint, **kwargs):
    # Airflow inyecta la fecha lógica de ejecución automáticamente
    ds = kwargs['ds']
    ingester = APIIngester()
    ingester.fetch_and_upload(dataset_endpoint=endpoint, date=ds)

def run_csv_ingestion(filename, dataset_name, **kwargs):
    ds = kwargs['ds']
    # Apunta a la carpeta unificada 'seed' tal como lo pidió el nuevo esquema de trabajo
    source_path = f"/opt/airflow/data/seed/{filename}"
    ingester = CSVIngester()
    ingester.ingest_csv(file_path=source_path, dataset_name=dataset_name, date=ds)

def run_log_ingestion(**kwargs):
    ds = kwargs['ds']
    source_path = "/opt/airflow/data/seed/production_app.log"
    ingester = LogIngester()
    ingester.parse_and_upload_logs(log_file_path=source_path, date=ds)


with DAG(
    'kepler_elt_bronze_pipeline',
    default_args=default_args,
    description='Orquestador de Ingesta para Datasets de Riesgo Financiero - Capa Bronze',
    schedule_interval='@daily',  # Se ejecuta de manera continua/diaria
    catchup=False,
) as dag:

    # 1. Tareas de Ingesta API
    task_ingest_transactions = PythonOperator(
        task_id='ingest_api_transactions',
        python_callable=run_api_ingestion,
        op_kwargs={'endpoint': 'transactions'}
    )

    task_ingest_market_data = PythonOperator(
        task_id='ingest_api_market_data',
        python_callable=run_api_ingestion,
        op_kwargs={'endpoint': 'market_data'}
    )

    # 2. Tareas de Ingesta CSV
    task_ingest_accounts = PythonOperator(
        task_id='ingest_csv_accounts',
        python_callable=run_csv_ingestion,
        op_kwargs={'filename': 'accounts.csv', 'dataset_name': 'accounts'}
    )

    task_ingest_customers = PythonOperator(
        task_id='ingest_csv_customers',
        python_callable=run_csv_ingestion,
        op_kwargs={'filename': 'customers.csv', 'dataset_name': 'customers'}
    )

    # 3. Tarea de Ingesta de Logs
    task_ingest_logs = PythonOperator(
        task_id='ingest_app_logs',
        python_callable=run_log_ingestion
    )

    # Ejecución en paralelo dentro del Clúster de Celery Workers
    [task_ingest_transactions, task_ingest_market_data, task_ingest_accounts, task_ingest_customers, task_ingest_logs]