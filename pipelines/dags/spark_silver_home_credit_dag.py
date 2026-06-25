from datetime import datetime, timedelta
from airflow import DAG
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

# Obtener nombre del bucket desde Variables de Airflow
bronze_bucket = Variable.get("BUCKET_NAME", default_var="keppler-data-architecture")
silver_bucket = Variable.get("SILVER_BUCKET_NAME", default_var=bronze_bucket)

# Lista de archivos a procesar dinámicamente
HOME_CREDIT_TABLES = [
    'application_test', 
    'application_train', 
    'bureau', 
    'bureau_balance', 
    'credit_card_balance', 
    'installments_payments', 
    'POS_CASH_balance', 
    'previous_application', 
    'sample_submission'
]

with DAG(
    'spark_silver_home_credit_dag',
    default_args=default_args,
    description='Transforma todos los CSV de Home Credit (Bronze) a Parquet (Silver) usando Spark',
    schedule=None,
    catchup=False,
    # Procesamiento secuencial: 1 archivo a la vez para darle TODO el clúster
    max_active_tasks=1,
    tags=['transformation', 'silver', 'spark', 'home_credit', 'ssh'],
) as dag:

    for table_name in HOME_CREDIT_TABLES:
        # Comando que ejecuta spark-submit dentro del contenedor core-spark-master
        spark_command = f"""
        docker exec core-spark-master /opt/spark/bin/spark-submit \\
            --packages org.apache.hadoop:hadoop-aws:3.4.0,com.amazonaws:aws-java-sdk-bundle:1.12.367 \\
            --conf spark.driver.port=7078 \\
            --conf spark.driver.blockManager.port=7079 \\
            --conf spark.blockManager.port=37000 \\
            --total-executor-cores 10 \\
            --executor-memory 1500M \\
            --master spark://21.0.2.203:7077 \\
            /opt/spark/pipelines/tasks-spark/caso_5/silver/bronze_to_silver_home_credit.py \\
            --bronze-bucket {bronze_bucket} \\
            --silver-bucket {silver_bucket} \\
            --table-name {table_name}
        """

        task = SSHOperator(
            task_id=f'run_spark_silver_{table_name}',
            ssh_conn_id='spark_master_ssh',
            command=spark_command,
            cmd_timeout=3600  # 1 hora por archivo, por si son muy grandes
        )
