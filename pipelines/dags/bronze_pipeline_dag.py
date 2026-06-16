# -*- coding: utf-8 -*-
"""
Airflow DAG: Bronze Layer - Data Structuring
Lee datos de elt_pipeline_dag output (S3), estructura con Spark, escribe a Bronze curated
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup

# ====== Configuración Default ======
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 15),
    'email_on_failure': True,
    'email': ['data-team@keppler.local'],
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

# ====== DAG Definition ======
dag = DAG(
    'bronze_pipeline_dag',
    default_args=default_args,
    description='Bronze Layer: Structuring raw data with Spark',
    schedule_interval='0 2 * * *',  # Daily at 2 AM (después de elt_pipeline)
    catchup=False,
    tags=['bronze', 'spark', 'production'],
)

# ====== Variables Airflow (configurables desde UI) ======
# Varias desde UI: Admin → Variables
spark_master = Variable.get("SPARK_MASTER_URL", "spark://financial-risk-spark-master:7077")
spark_apps_jar = Variable.get("SPARK_JARS", "s3a://kepler-bronze/jars/hadoop-aws-3.3.4.jar,s3a://kepler-bronze/jars/aws-java-sdk-bundle-1.12.261.jar")

# ====== Bronze Structuring Jobs ======

task_bronze_application = SparkSubmitOperator(
    task_id='bronze_application',
    application='/opt/keppler/data-platform/staging/bronze/jobs/bronze_application.py',
    conf={
        'spark.master': spark_master,
        'spark.submit.deployMode': 'cluster',
        'spark.executor.memory': '2g',
        'spark.executor.cores': '2',
        'spark.driver.memory': '2g',
        'spark.jars.packages': 'org.apache.hadoop:hadoop-aws:3.3.4',
    },
    env_vars={
        'AWS_ACCESS_KEY_ID': Variable.get("AWS_ACCESS_KEY_ID"),
        'AWS_SECRET_ACCESS_KEY': Variable.get("AWS_SECRET_ACCESS_KEY"),
        'S3_ENDPOINT': Variable.get("S3_ENDPOINT", "s3.amazonaws.com"),
    },
    dag=dag,
)

task_bronze_bureau = SparkSubmitOperator(
    task_id='bronze_bureau',
    application='/opt/keppler/data-platform/staging/bronze/jobs/bronze_bureau.py',
    conf={
        'spark.master': spark_master,
        'spark.submit.deployMode': 'cluster',
        'spark.executor.memory': '2g',
        'spark.executor.cores': '2',
        'spark.driver.memory': '2g',
        'spark.jars.packages': 'org.apache.hadoop:hadoop-aws:3.3.4',
    },
    env_vars={
        'AWS_ACCESS_KEY_ID': Variable.get("AWS_ACCESS_KEY_ID"),
        'AWS_SECRET_ACCESS_KEY': Variable.get("AWS_SECRET_ACCESS_KEY"),
        'S3_ENDPOINT': Variable.get("S3_ENDPOINT", "s3.amazonaws.com"),
    },
    dag=dag,
)

# ====== Ejecución en paralelo ======
# Ambos jobs corren en paralelo (no hay dependencias entre ellos)
[task_bronze_application, task_bronze_bureau]
