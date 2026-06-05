from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime

# ===============================
# Funcion de toda la vida
# ===============================
def greet(worker_name):
    print(f'Hola desde {worker_name}')

# ===============================
# Definicion de un DAG
# ===============================

with DAG(
    dag_id = 'Hellow_workers',
    start_date = datetime(2026, 4, 7),
    schedule = None,
    catchup = False,
    tags = ['tutorial', 'mi primer DAG']
) as dag:
    # Task 1
    worker_1 = PythonOperator(
        task_id = 'Saludo_Worker_1', # identificador de la tarea
        python_callable = greet, # no se pone parentesis porque estamos diciendo que vamos a usar esa funcion, si le ponemos parentesis, lo estariamos ejecutando de una vez, y no es lo que queremos
        op_kwargs = {'worker_name': 'worker-1'} # estos son los argumentos que va a la funcion greet
    )

    # Task 2
    worker_2 = PythonOperator(
        task_id = 'Saludo_Worker_2',
        python_callable = greet,
        op_kwargs = {'worker_name': 'worker-2'}
    )

    # Task 3
    worker_3 = PythonOperator(
        task_id = 'Saludo_Worker_3',
        python_callable = greet,
        op_kwargs = {'worker_name': 'worker-3'}
    )

    # Task 4
    worker_4 = PythonOperator(
        task_id = 'Saludo_Worker_4',
        python_callable = greet,
        op_kwargs = {'worker_name': 'worker-4'}
    )

    # DEPENDENCIAS
    [
        worker_1,
        worker_2,
        worker_3,
        worker_4
    ] # referecia las tareas en paralelo porque no hay flechas, si dijera worker_1 >> worker_2 >> worker_3 >> worker_4, las tareas se ejecutarian en secuencia