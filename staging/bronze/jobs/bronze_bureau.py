# -*- coding: utf-8 -*-
"""
Bronze Layer: Bureau Dataset
Similar a bronze_application.py pero para bureau (histórico de créditos)
"""

import sys
import os
from datetime import datetime
import uuid

sys.path.insert(0, "/opt/keppler/data-platform")

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, lit, current_timestamp, monotonically_increasing_id, md5, concat_ws
)
from common.utils.spark_session import get_spark_session
from staging.bronze.schemas.application_schema import BUREAU_SCHEMA

def generate_unique_id(df: DataFrame, source_cols: list) -> DataFrame:
    return df.withColumn(
        "id_unico_nuevo",
        concat_ws("-", 
            lit("BUR"),
            lit(datetime.now().strftime("%Y%m%d")),
            md5(concat_ws("|", *[col(c) for c in source_cols])),
            monotonically_increasing_id()
        )
    )

def add_bronze_metadata(df: DataFrame, source: str, dataset: str) -> DataFrame:
    return df.withColumn(
        "id_original", col("SK_ID_BUREAU")
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
    print("BRONZE LAYER: BUREAU DATASET")
    print("=" * 80)
    
    try:
        spark = get_spark_session(app_name="bronze-bureau-job")
        print("✅ Spark session creada")
        
        s3_path = "s3a://kepler-bronze/financial/bureau/"
        print(f"📥 Leyendo desde: {s3_path}")
        
        df = spark.read \
            .parquet(s3_path) \
            .limit(100000)
        
        print(f"   Registros cargados: {df.count()}")
        
        df = generate_unique_id(df, ["SK_ID_BUREAU"])
        print("✅ IDs únicos generados")
        
        df = add_bronze_metadata(
            df, 
            source="kepler-finance-s3", 
            dataset="bureau"
        )
        print("✅ Metadata agregada")
        
        null_counts = df.select([
            (col(c).isNull().cast("int").sum()).alias(c) 
            for c in df.columns
        ])
        print("📊 Nulos por columna:")
        null_counts.show()
        
        output_path = "s3a://kepler-bronze-curated/bronze/bureau/"
        print(f"📤 Escribiendo a: {output_path}")
        
        df.coalesce(1) \
            .write \
            .mode("overwrite") \
            .partitionBy("batch_id") \
            .parquet(output_path)
        
        print("✅ Datos escritos exitosamente")
        
        print("\n" + "=" * 80)
        print("✅ BRONZE BUREAU JOB COMPLETADO")
        print(f"   Total registros procesados: {df.count()}")
        print(f"   Ubicación: {output_path}")
        print("=" * 80)
        
        spark.stop()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
