import sys
sys.path.append("/opt/airflow")

from airflow import DAG
from airflow.decorators import task
from datetime import datetime

# Importamos las funciones modularizadas para el dataset de Home Credit
from pipelines.tasks.caso_5.eda.homeCredit.eda_task import list_homecredit_files, generate_single_eda

with DAG(
    dag_id="eda_home_credit_s3",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    schedule="@daily",
    tags=["eda", "s3", "analytics", "homecredit", "dynamic-mapping"]
) as dag:

    @task
    def get_files_task():
        """Obtiene la lista de archivos CSV desde S3."""
        return list_homecredit_files()

    @task
    def process_file_task(s3_key: str):
        """Genera el EDA para un archivo específico (se ejecutará en paralelo por los workers)."""
        generate_single_eda(s3_key)

    # 1. Obtenemos la lista de llaves de los archivos
    files_to_process = get_files_task()
    
    # 2. Dynamic Task Mapping: Expande la tarea process_file_task. 
    # Airflow creará una instancia separada de esta tarea para cada CSV encontrado,
    # permitiendo que distintos workers procesen los datasets en paralelo.
    process_file_task.expand(s3_key=files_to_process)