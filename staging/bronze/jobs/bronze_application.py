# -*- coding: utf-8 -*-
"""
Bronze Layer: Application Dataset
Lee de S3 (elt_pipeline_dag output), aplica esquema explícito, escribe particionado.
"""

import sys
import os
from datetime import datetime
import uuid

# Agregar repo2 al path para importar desde common
sys.path.insert(0, "/opt/keppler/data-platform")

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, lit, current_timestamp, monotonically_increasing_id, md5, concat_ws
)
from common.utils.spark_session import get_spark_session
from staging.bronze.schemas.application_schema import APPLICATION_SCHEMA

def generate_unique_id(df: DataFrame, source_cols: list) -> DataFrame:
    """
    Genera ID único nuevo basado en hash de columnas clave + UUID
    Mantiene id_original intacto
    """
    return df.withColumn(
        "id_unico_nuevo",
        concat_ws("-", 
            lit("APP"),
            lit(datetime.now().strftime("%Y%m%d")),
            md5(concat_ws("|", *[col(c) for c in source_cols])),
            monotonically_increasing_id()
        )
    )

def add_bronze_metadata(df: DataFrame, source: str, dataset: str) -> DataFrame:
    """
    Agrega columnas de trazabilidad para auditoría
    """
    return df.withColumn(
        "id_original", col("SK_ID_CURR")  # En Home Credit, es el ID principal
    ).withColumn(
        "fuente", lit(source)
    ).withColumn(
        "dataset_nombre", lit(dataset)
    ).withColumn(
        "ingestion_timestamp", current_timestamp()
    ).withColumn(
        "batch_id", lit(datetime.now().strftime("%Y%m%d_%H%M%S"))
    )

def main():
    print("=" * 80)
    print("BRONZE LAYER: APPLICATION DATASET")
    print("=" * 80)
    
    try:
        # 1. Obtener Spark Session
        spark = get_spark_session(app_name="bronze-application-job")
        print("✅ Spark session creada")
        
        # 2. Leer desde S3 (output de elt_pipeline_dag)
        # Asume que elt_pipeline_dag escribió a:
        # s3a://kepler-bronze/financial/application/year=YYYY/month=MM/day=DD/application_YYYY-MM-DD.parquet
        
        s3_path = "s3a://kepler-bronze/financial/application/"
        print(f"📥 Leyendo desde: {s3_path}")
        
        df = spark.read \
            .parquet(s3_path) \
            .limit(10000)  # Limit para demo
        
        print(f"   Registros cargados: {df.count()}")
        
        # 3. Aplicar esquema explícito (validación)
        # Los datos ya tienen columnas, solo validamos que sean correctas
        # En producción, forzaríamos el schema con:
        # df = spark.read.schema(APPLICATION_SCHEMA).parquet(s3_path)
        
        # 4. Generar IDs únicos
        df = generate_unique_id(df, ["SK_ID_CURR"])
        print("✅ IDs únicos generados")
        
        # 5. Agregar metadata de trazabilidad
        df = add_bronze_metadata(
            df, 
            source="kepler-finance-s3", 
            dataset="application"
        )
        print("✅ Metadata agregada")
        
        # 6. Validaciones básicas de Bronze
        null_counts = df.select([
            (col(c).isNull().cast("int").sum()).alias(c) 
            for c in df.columns
        ])
        print("📊 Nulos por columna:")
        null_counts.show()
        
        # 7. Escribir a Bronze (particionado por fecha de ingestión + fuente)
        output_path = "s3a://kepler-bronze-curated/bronze/application/"
        print(f"📤 Escribiendo a: {output_path}")
        
        df.coalesce(1) \
            .write \
            .mode("overwrite") \
            .partitionBy("batch_id") \
            .parquet(output_path)
        
        print("✅ Datos escritos exitosamente")
        
        # 8. Logging de éxito
        print("\n" + "=" * 80)
        print("✅ BRONZE APPLICATION JOB COMPLETADO")
        print(f"   Total registros procesados: {df.count()}")
        print(f"   Ubicación: {output_path}")
        print("=" * 80)
        
        spark.stop()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
