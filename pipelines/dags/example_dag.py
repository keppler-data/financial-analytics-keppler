from airflow.decorators import dag, task
from datetime import datetime
import time
import random


@dag(
    dag_id="test_medium_workload",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "medium"],
)
def test_medium_workload():

    @task
    def cpu_task():
        print("🔥 Iniciando tarea CPU...")
        total = 0
        for i in range(5_000_000):
            total += i
        print(f"✅ Resultado cálculo: {total}")

    @task
    def data_task():
        print("🧠 Procesando datos...")
        data = [random.randint(1, 1000) for _ in range(1000000)]
        data_sorted = sorted(data)
        print(f"✅ Datos procesados. Min: {data_sorted[0]}, Max: {data_sorted[-1]}")

    @task
    def sleep_task():
        print("⏳ Simulando proceso largo...")
        for i in range(5):
            print(f"Paso {i+1}/5")
            time.sleep(3)
        print("✅ Proceso completado")

    # Definir dependencias
    cpu = cpu_task()
    data = data_task()
    sleep = sleep_task()

    cpu >> data >> sleep


dag = test_medium_workload()
