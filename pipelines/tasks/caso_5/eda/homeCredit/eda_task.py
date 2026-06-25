import boto3
import pandas as pd
import os
import logging
from ydata_profiling import ProfileReport

logger = logging.getLogger(__name__)

BUCKET_NAME = "keppler-data-architecture"
PREFIX_BRONZE = "bronze/home_credit/"
PREFIX_REPORT = "reports/home_credit/"

def list_homecredit_files() -> list[str]:
    """
    Lista todos los archivos CSV en el bucket de S3 para Home Credit.
    Retorna una lista de las llaves (keys) de S3.
    """
    s3 = boto3.client("s3")
    logger.info(f"Buscando archivos en s3://{BUCKET_NAME}/{PREFIX_BRONZE}")
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX_BRONZE)
    
    if "Contents" not in response:
        logger.warning("No se encontraron archivos.")
        return []
        
    keys = [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".csv")]
    logger.info(f"Se encontraron {len(keys)} archivos CSV.")
    return keys

def generate_single_eda(s3_key: str):
    """
    Descarga un solo archivo CSV desde S3, genera el reporte EDA con ydata-profiling
    y lo sube de regreso a S3. Diseñado para ejecutarse como una tarea mapeada dinámicamente.
    """
    s3 = boto3.client("s3")
    
    filename = s3_key.split("/")[-1]
    dataset_name = filename.replace(".csv", "")
    
    local_csv_path = f"/tmp/{filename}"
    local_html_path = f"/tmp/{dataset_name}_eda.html"
    
    logger.info(f"Descargando {s3_key}...")
    s3.download_file(BUCKET_NAME, s3_key, local_csv_path)
    
    logger.info(f"Generando reporte EDA con ydata-profiling para {dataset_name}...")
    try:
        # low_memory=False ayuda con las columnas de tipos mixtos en la lectura inicial
        df = pd.read_csv(local_csv_path, low_memory=False)
        
        # Configuramos minimal=True si el dataset es muy grande (> 100k filas) 
        # para no agotar los 3GB de memoria de los workers del cluster
        is_huge = len(df) > 100000
        
        profile = ProfileReport(
            df, 
            title=f"EDA Report - {dataset_name}",
            minimal=is_huge,
            explorative=True
        )
        profile.to_file(local_html_path)
            
        report_key = f"{PREFIX_REPORT}{dataset_name}_eda.html"
        logger.info(f"Subiendo reporte a s3://{BUCKET_NAME}/{report_key}...")
        s3.upload_file(local_html_path, BUCKET_NAME, report_key)
        
    except Exception as e:
        logger.error(f"Error procesando {filename}: {e}")
        # Relanzamos la excepción para que el Worker de Airflow marque esta tarea en específico como Fallida
        raise e
        
    finally:
        # Limpieza local para liberar espacio del worker
        if os.path.exists(local_csv_path):
            os.remove(local_csv_path)
        if os.path.exists(local_html_path):
            os.remove(local_html_path)
            
    logger.info(f"EDA de {dataset_name} completado exitosamente con ydata-profiling.")

