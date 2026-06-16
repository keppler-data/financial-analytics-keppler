# -*- coding: utf-8 -*-
"""
Main Pipeline DAG: Orquestra ingesta (ELT) → Structuring (Bronze)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.dummy import DummyOperator

default_args = {
    'owner': 'data-engineering',
    'start_date': datetime(2026, 6, 15),
    'retries': 2,
}

dag = DAG(
    'main_data_pipeline',
    default_args=default_args,
    description='Master: ELT → Bronze structuring',
    schedule_interval='0 0 * * *',  # Daily midnight
    catchup=False,
    tags=['main', 'production'],
)

# Esperar a que elt_pipeline_dag complete
wait_for_elt = ExternalTaskSensor(
    task_id='wait_for_elt_pipeline',
    external_dag_id='kepler_elt_bronze_pipeline',
    external_task_id=None,  # Espera que TODO el DAG complete
    timeout=3600,  # 1 hora timeout
    dag=dag,
)

# Trigger bronze_pipeline_dag
start_bronze = DummyOperator(
    task_id='start_bronze_pipeline',
    dag=dag,
)

wait_for_elt >> start_bronze
