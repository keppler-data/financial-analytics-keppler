from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.models import Variable

# Argumentos por defecto del DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

silver_bucket = Variable.get("SILVER_BUCKET_NAME", default_var="keppler-data-architecture")
diamond_bucket = Variable.get("DIAMOND_BUCKET_NAME", default_var=silver_bucket)

with DAG(
    'caso5_dbt_spark_ml_pipeline',
    default_args=default_args,
    description='Orquesta la transformación con dbt (Athena) y el Feature Selection con Spark (MLlib)',
    schedule=None,
    catchup=False,
    max_active_tasks=1,
    tags=['dbt', 'athena', 'spark', 'machine_learning', 'caso_5'],
) as dag:

    # 0. Tarea de AWS Glue: Actualizar catálogo en Athena
    run_glue_crawler = BashOperator(
        task_id='run_glue_crawler',
        bash_command='python /opt/airflow/pipelines/utils/setup_glue_catalog.py',
    )

    # 1. Tarea de dbt: Ejecutar el modelo fct_home_credit_consolidated
    # Usamos --profiles-dir para indicarle a dbt dónde encontrar profiles.yml
    dbt_run_gold = BashOperator(
        task_id='dbt_run_gold_table',
        bash_command='cd /opt/airflow/pipelines/dbt_transform && dbt run --select fct_home_credit_consolidated --profiles-dir .',
    )

    # 2. Tarea de Spark ML: Calcular Feature Importance usando la Tabla Gorda
    spark_ml_command = f"""
    docker exec core-spark-master /opt/spark/bin/spark-submit \\
        --packages org.apache.hadoop:hadoop-aws:3.4.0,com.amazonaws:aws-java-sdk-bundle:1.12.367 \\
        --conf spark.driver.port=7078 \\
        --conf spark.driver.blockManager.port=7079 \\
        --conf spark.blockManager.port=37000 \\
        --total-executor-cores 10 \\
        --executor-memory 1500M \\
        --master spark://21.0.2.203:7077 \\
        /opt/spark/pipelines/tasks-spark/caso_5/diamond/gold_to_diamond_ml.py \\
        --gold-path s3a://{silver_bucket}/gold/fct_home_credit_consolidated/ \\
        --diamond-path s3a://{diamond_bucket}/diamond/home_credit_refined/ \\
        --report-path s3a://{diamond_bucket}/reports/diamond/home_credit_ml_report.md \\
        --target-col is_default
    """

    spark_ml_feature_selection = SSHOperator(
        task_id='spark_ml_feature_selection',
        ssh_conn_id='spark_master_ssh',
        command=spark_ml_command,
        cmd_timeout=3600
    )

    # Dependencia: Primero Glue, luego dbt (Athena), luego Spark (ML)
    run_glue_crawler >> dbt_run_gold >> spark_ml_feature_selection
