from pathlib import Path
import tempfile
import shutil
import zipfile
import pandas as pd
import logging

from pipelines.utils.kaggle.client import get_kaggle_client
from pipelines.utils.s3.upload import upload_to_s3
from pipelines.utils.s3.validate import validate_s3_upload

logger = logging.getLogger(__name__)

HOME_CREDITS_DATASETS = {
    "application_train.csv",
    "bureau.csv",
    "bureau_balance.csv",
    "previous_application.csv",
    "POS_CASH_balance.csv", 
    "installments_payments.csv", 
    "credit_card_balance.csv"
}

def ingest_home_credit() -> list[tuple[str, str]]:
    """
    Ejecuta el flujo completo de Home Credit:
    Descarga de Kaggle -> Extrae -> Convierte a Parquet -> Sube a S3 -> Limpia.
    """
    logger.info("Iniciando ingesta Home Credit")
    
    # 1. Preparar directorio temporal
    base_dir = Path(tempfile.gettempdir()) / "home_credit"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 2. Descargar de Kaggle
        api = get_kaggle_client()
        api.competition_download_files(competition="home-credit-default-risk", path=str(base_dir))
        
        zip_files = list(base_dir.glob("*.zip"))
        if not zip_files:
            raise FileNotFoundError(f"No se encontró ningún ZIP en: {base_dir}")
        zip_path = zip_files[0]
        logger.info(f"ZIP descargado: {zip_path}")
        
        # 3. Extraer ZIP
        extract_path = base_dir / "extracted"
        extract_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        logger.info(f"Archivos extraídos en: {extract_path}")
        
        # 4. Convertir CSV a Parquet
        parquet_path = base_dir / "parquet"
        parquet_path.mkdir(parents=True, exist_ok=True)
        
        for csv_file in extract_path.glob("*.csv"):
            if csv_file.name not in HOME_CREDITS_DATASETS:
                continue
                
            logger.info(f"Procesando a parquet: {csv_file.name}")
            df = pd.read_csv(csv_file)
            parquet_file = parquet_path / f"{csv_file.stem}.parquet"
            df.to_parquet(parquet_file, engine="pyarrow", index=False)
            del df # Liberar memoria
        
        # 5. Subir a S3
        uploaded_files = upload_to_s3(
            local_path=str(parquet_path),
            bucket_name="layer-keppler",
            s3_prefix="bronze/home_credit"
        )
        
        # 6. Validar subida
        for bucket, s3_key in uploaded_files:
            validate_s3_upload(bucket, s3_key)
            
        logger.info("Ingesta Home Credit finalizada con éxito")
        return uploaded_files
        
    finally:
        # 7. Limpieza local (se ejecuta sin importar si hubo error o no)
        if base_dir.exists():
            shutil.rmtree(base_dir)
            logger.info(f"Directorio temporal eliminado: {base_dir}")

if __name__ == "__main__":
    result = ingest_home_credit()
    logger.info(f"Result: {result}")