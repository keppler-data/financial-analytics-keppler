from datetime import datetime, timedelta

from pipelines.tasks.ingestion_kaggle_bronze.kaggle_tasks import (
    task_ingest_lending_club,
    task_ingest_home_credit,
    task_ingest_give_me_some_credit,
    task_ingest_loan_prediction
)
from airflow import DAG
from airflow.operators.python import PythonOperator

# Argumentos por defecto del DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1), # Ajustar a la fecha de despliegue real
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'ingesta_kaggle_bronze_dag',
    default_args=default_args,
    description='Extrae los 4 datasets masivos de Kaggle y los almacena crudos en S3 (Capa Bronze)',
    schedule_interval='@daily',
    catchup=False,
    tags=['ingestion', 'bronze', 'kaggle', 's3'],
) as dag:

    # ==========================================
    # Definición explícita de las tareas
    # ==========================================

    ingest_lending_club = PythonOperator(
        task_id='extract_and_load_lending_club',
        python_callable=task_ingest_lending_club
    )

    ingest_home_credit = PythonOperator(
        task_id='extract_and_load_home_credit_default_risk',
        python_callable=task_ingest_home_credit
    )

    ingest_give_me_some_credit = PythonOperator(
        task_id='extract_and_load_give_me_some_credit',
        python_callable=task_ingest_give_me_some_credit
    )

    ingest_loan_prediction = PythonOperator(
        task_id='extract_and_load_loan_prediction',
        python_callable=task_ingest_loan_prediction
    )

    # Orden de ejecución (Dependencies)
    # Dejamos las tareas en paralelo ya que los datasets son independientes
    [ingest_lending_club, ingest_home_credit, ingest_give_me_some_credit, ingest_loan_prediction]
