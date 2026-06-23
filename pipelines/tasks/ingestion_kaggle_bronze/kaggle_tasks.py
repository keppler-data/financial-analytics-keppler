import os
import tempfile
import boto3
import logging
import zipfile
from airflow.models import Variable

# Configurar el logger de Airflow
logger = logging.getLogger(__name__)

def _base_download_upload(dataset_id: str, s3_prefix: str):
    """
    Lógica base interna para descargar todos los archivos de un dataset y subirlos a S3.
    """
    os.environ['KAGGLE_USERNAME'] = Variable.get("KAGGLE_USERNAME", default_var="")
    os.environ['KAGGLE_KEY'] = Variable.get("KAGGLE_KEY", default_var="")

    from kaggle.api.kaggle_api_extended import KaggleApi
    
    api = KaggleApi()
    api.authenticate()

    s3_client = boto3.client('s3')
    # Actualizado al nombre de variable correcto configurado en Airflow
    bronze_bucket = Variable.get("BUCKET_NAME", default_var="mi-bucket-bronze")

    # --- Verificación de Idempotencia (Evitar reprocesos) ---
    s3_prefix_path = f"bronze/{s3_prefix}/"
    response = s3_client.list_objects_v2(Bucket=bronze_bucket, Prefix=s3_prefix_path)
    
    if 'Contents' in response and len(response['Contents']) > 0:
        logger.info(f"¡Éxito! Los datos de {dataset_id} ya existen en s3://{bronze_bucket}/{s3_prefix_path}. Saltando ingesta para ahorrar tiempo y red.")
        return
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.info(f"Descargando dataset '{dataset_id}' en '{tmpdirname}'...")
        
        # Diferenciamos entre competencias (c/) y datasets normales
        if dataset_id.startswith('c/'):
            comp_name = dataset_id.split('/')[-1]
            # competition_download_files no siempre soporta unzip=True correctamente
            api.competition_download_files(comp_name, path=tmpdirname)
        else:
            api.dataset_download_files(dataset_id, path=tmpdirname, unzip=True)
            
        # Extraer manualmente cualquier archivo .zip resultante por seguridad
        for item in os.listdir(tmpdirname):
            if item.endswith('.zip'):
                zip_path = os.path.join(tmpdirname, item)
                logger.info(f"Descomprimiendo {zip_path}...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdirname)
                os.remove(zip_path) # Limpiamos el .zip para no subirlo a S3
        
        # Subimos TODOS los archivos extraídos a S3
        archivos_subidos = 0
        for root, dirs, files in os.walk(tmpdirname):
            for file in files:
                local_file_path = os.path.join(root, file)
                s3_path = f"bronze/{s3_prefix}/{file}"
                
                logger.info(f"Subiendo {file} a s3://{bronze_bucket}/{s3_path}...")
                s3_client.upload_file(local_file_path, bronze_bucket, s3_path)
                archivos_subidos += 1
                
        logger.info(f"Subida completada exitosamente para {dataset_id}. Total archivos: {archivos_subidos}")

# ==========================================
# Funciones explícitas para cada Dataset
# ==========================================

def task_ingest_lending_club():
    _base_download_upload(
        dataset_id='wordsforthewise/lending-club',
        s3_prefix='lending_club'
    )

def task_ingest_home_credit():
    _base_download_upload(
        dataset_id='c/home-credit-default-risk',
        s3_prefix='home_credit'
    )

def task_ingest_give_me_some_credit():
    _base_download_upload(
        dataset_id='c/GiveMeSomeCredit',
        s3_prefix='give_me_some_credit'
    )

def task_ingest_loan_prediction():
    _base_download_upload(
        dataset_id='altruistdelhite04/loan-prediction-problem-dataset',
        s3_prefix='loan_prediction'
    )
