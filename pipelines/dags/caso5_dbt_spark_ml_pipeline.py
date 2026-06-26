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

def build_spark_command(dataset_name, intermediate_folder):
    return f"""
    docker exec -e AWS_DEFAULT_REGION=us-east-1 core-spark-master /opt/spark/bin/spark-submit \\
        --packages org.apache.hadoop:hadoop-aws:3.4.0,com.amazonaws:aws-java-sdk-bundle:1.12.367 \\
        --conf spark.jars.ivy=/opt/spark/work/.ivy \\
        --conf "spark.driver.host=21.0.2.203" \\
        --total-executor-cores 10 \\
        --executor-memory 1500M \\
        --master spark://21.0.2.203:7077 \\
        /opt/spark/pipelines/tasks-spark/caso_5/ml/feature_discovery.py \\
        --intermediate-path s3a://{silver_bucket}/intermediate/{intermediate_folder}/ \\
        --report-path s3a://{diamond_bucket}/reports/ml/{dataset_name}_ml_report.md \\
        --json-path s3a://{diamond_bucket}/reports/ml/{dataset_name}_ml_features.json \\
        --target-col is_default
    """

with DAG(
    'caso5_dbt_spark_ml_pipeline',
    default_args=default_args,
    description='Orquesta la transformación con dbt (Athena) y el Feature Selection con Spark (MLlib) Multi-Modelo',
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

    # 1. Tarea de dbt (PARALELO NATIVO): Ejecuta todos los modelos de intermediate a la vez
    dbt_run_intermediate = BashOperator(
        task_id='dbt_run_intermediate_layer',
        bash_command='cd /opt/airflow/pipelines/dbt_transform && dbt run --select intermediate --profiles-dir .',
    )

    # 2. Tareas de Spark ML: Calcular Feature Importance para cada dataset
    spark_ml_hc = SSHOperator(
        task_id='spark_ml_home_credit',
        ssh_conn_id='spark_master_ssh',
        command=build_spark_command('home_credit', 'int_home_credit_consolidated'),
        cmd_timeout=3600
    )

    spark_ml_lc = SSHOperator(
        task_id='spark_ml_lending_club',
        ssh_conn_id='spark_master_ssh',
        command=build_spark_command('lending_club', 'int_lending_club_consolidated'),
        cmd_timeout=3600
    )

    spark_ml_gmsc = SSHOperator(
        task_id='spark_ml_give_me_some_credit',
        ssh_conn_id='spark_master_ssh',
        command=build_spark_command('give_me_some_credit', 'int_give_me_some_credit_consolidated'),
        cmd_timeout=3600
    )

    spark_ml_lp = SSHOperator(
        task_id='spark_ml_loan_prediction',
        ssh_conn_id='spark_master_ssh',
        command=build_spark_command('loan_prediction', 'int_loan_prediction_consolidated'),
        cmd_timeout=3600
    )

    # 3. Tarea final de orquestación: Cargar JSONs de S3 y compilar dbt Gold y Diamond
    dbt_run_gold_diamond = BashOperator(
        task_id='dbt_run_gold_diamond',
        bash_command='python /opt/airflow/pipelines/utils/run_dbt_with_ml_vars.py',
    )

    # Dependencia: Primero Glue, luego dbt (Athena), luego Spark ML (Secuencial 1 a 1 para no ahogar memoria), luego orquestador de ML a dbt
    run_glue_crawler >> dbt_run_intermediate >> spark_ml_hc >> spark_ml_lc >> spark_ml_gmsc >> spark_ml_lp >> dbt_run_gold_diamond
