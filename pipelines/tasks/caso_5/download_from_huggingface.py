import os
import tempfile
import boto3
import logging
import zipfile
import requests
from airflow.models import Variable

# Configurar el logger de Airflow
logger = logging.getLogger(__name__)

def _base_download_upload_hf(repo_id: str, s3_prefix: str):
    """
    Descarga archivos de un dataset de HuggingFace usando la API REST (requests)
    y los sube a S3.
    """
    s3_client = boto3.client('s3')
    bronze_bucket = Variable.get("BUCKET_NAME", default_var="mi-bucket-bronze")

    # --- Verificación de Idempotencia (Evitar reprocesos) ---
    s3_prefix_path = f"bronze/{s3_prefix}/"
    response = s3_client.list_objects_v2(Bucket=bronze_bucket, Prefix=s3_prefix_path)
    
    if 'Contents' in response and len(response['Contents']) > 0:
        logger.info(f"¡Éxito! Los datos de {repo_id} ya existen en s3://{bronze_bucket}/{s3_prefix_path}. Saltando ingesta.")
        return
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.info(f"Obteniendo lista de archivos para el repositorio de HuggingFace '{repo_id}'...")
        
        # 1. Obtener la lista de archivos (asumiendo estructura plana en main)
        tree_url = f"https://huggingface.co/api/datasets/{repo_id}/tree/main"
        resp = requests.get(tree_url)
        resp.raise_for_status()
        
        files_data = resp.json()
        
        # 2. Descargar cada archivo
        for item in files_data:
            if item.get("type") == "file":
                file_path = item.get("path")
                # Ignorar archivos ocultos o de metadatos propios de git/HF si los hay
                if file_path.startswith("."):
                    continue
                    
                download_url = f"https://huggingface.co/datasets/{repo_id}/resolve/main/{file_path}"
                local_file_path = os.path.join(tmpdirname, file_path)
                
                logger.info(f"Descargando {file_path} desde {download_url}...")
                file_resp = requests.get(download_url, stream=True)
                file_resp.raise_for_status()
                
                with open(local_file_path, 'wb') as f:
                    for chunk in file_resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
        # 3. Extraer manualmente cualquier archivo .zip resultante por seguridad
        for item in os.listdir(tmpdirname):
            if item.endswith('.zip'):
                zip_path = os.path.join(tmpdirname, item)
                logger.info(f"Descomprimiendo {zip_path}...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdirname)
                os.remove(zip_path) # Limpiamos el .zip para no subirlo a S3
                
        # 4. Subimos TODOS los archivos extraídos a S3
        archivos_subidos = 0
        for root, dirs, files in os.walk(tmpdirname):
            for file in files:
                local_file_path = os.path.join(root, file)
                s3_path = f"bronze/{s3_prefix}/{file}"
                
                logger.info(f"Subiendo {file} a s3://{bronze_bucket}/{s3_path}...")
                s3_client.upload_file(local_file_path, bronze_bucket, s3_path)
                archivos_subidos += 1
                
        logger.info(f"Subida completada exitosamente para {repo_id}. Total archivos: {archivos_subidos}")

# ==========================================
# Funciones explícitas para cada Dataset
# ==========================================

def task_ingest_home_credit():
    _base_download_upload_hf(
        repo_id='algcache/HomeCreditDefaultRisk',
        s3_prefix='home_credit'
    )

def task_ingest_give_me_some_credit():
    _base_download_upload_hf(
        repo_id='algcache/GiveMeSomeCredit',
        s3_prefix='give_me_some_credit'
    )
