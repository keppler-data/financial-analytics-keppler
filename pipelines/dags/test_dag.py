from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="test_decorators_dag",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["test", "decorators"],
)
def test_decorators_dag():

    @task
    def extract():
        print("Extrayendo datos...")
        return "Hola desde Airflow"

    @task
    def transform(data):
        result = data.upper()
        print(f"Transformando: {result}")
        return result

    @task
    def load(data):
        print(f"Cargando: {data}")

    load(transform(extract()))


test_decorators_dag()