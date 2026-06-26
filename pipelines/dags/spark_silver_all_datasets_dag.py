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

bronze_bucket = Variable.get("BUCKET_NAME", default_var="keppler-data-architecture")
silver_bucket = Variable.get("SILVER_BUCKET_NAME", default_var=bronze_bucket)

# Definimos los 4 datasets y sus archivos correspondientes en S3 (capa bronze)
DATASETS = {
    'home_credit': [
        'application_test.csv', 
        'application_train.csv', 
        'bureau.csv', 
        'bureau_balance.csv', 
        'credit_card_balance.csv', 
        'installments_payments.csv', 
        'POS_CASH_balance.csv', 
        'previous_application.csv', 
        'sample_submission.csv'
    ],
    'lending_club': [
        'accepted_2007_to_2018Q4.csv.gz', 
        'rejected_2007_to_2018Q4.csv.gz'
    ],
    'give_me_some_credit': [
        'cs-test.csv', 
        'cs-training.csv', 
        'sampleEntry.csv'
    ],
    'loan_prediction': [
        'test_Y3wMUE5_7gLdaTN.csv', 
        'train_u6lujuX_CVtuZ9i.csv'
    ]
}

with DAG(
    'spark_silver_all_datasets_dag',
    default_args=default_args,
    description='Transforma todos los CSV/GZ de Bronze a Parquet (Silver) usando Spark (Idempotente)',
    schedule=None,
    catchup=False,
    # max_active_tasks=1 crea nuestro "Súper DAG" secuencial para no ahogar el clúster
    max_active_tasks=1,
    tags=['transformation', 'silver', 'spark', 'all_datasets', 'ssh'],
) as dag:

    for dataset_name, files in DATASETS.items():
        for file_name in files:
            # Reemplazamos puntos por guiones bajos para el task_id de Airflow
            clean_file_name = file_name.replace('.', '_')
            
            # Comando que ejecuta spark-submit dentro del contenedor core-spark-master
            spark_command = f"""
            docker exec -e AWS_DEFAULT_REGION=us-east-1 core-spark-master /opt/spark/bin/spark-submit \\
                --packages org.apache.hadoop:hadoop-aws:3.4.0,com.amazonaws:aws-java-sdk-bundle:1.12.367 \\
                --conf spark.jars.ivy=/opt/spark/work/.ivy \\
                --conf "spark.driver.host=21.0.2.203" \\
                --total-executor-cores 10 \\
                --executor-memory 1500M \\
                --master spark://21.0.2.203:7077 \\
                /opt/spark/pipelines/tasks-spark/caso_5/silver/bronze_to_silver_transform.py \\
                --bronze-bucket {bronze_bucket} \\
                --silver-bucket {silver_bucket} \\
                --dataset-name {dataset_name} \\
                --file-name {file_name}
            """

            task = SSHOperator(
                task_id=f'silver_{dataset_name}_{clean_file_name}',
                ssh_conn_id='spark_master_ssh',
                command=spark_command,
                cmd_timeout=3600  # 1 hora por archivo
            )
