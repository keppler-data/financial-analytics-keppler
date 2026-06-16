# -*- coding: utf-8 -*-
"""
Spark Session Manager
Crea y gestiona la sesión de Spark con configuración óptima para data lakehouse
"""

from pyspark.sql import SparkSession
import os

def get_spark_session(app_name: str = "kepler-data-platform") -> SparkSession:
    """
    Crea una sesión de Spark preconfigurada para el data lakehouse.
    
    Args:
        app_name: Nombre de la aplicación Spark
        
    Returns:
        SparkSession configurada y lista para usar
    """
    
    spark = (
        SparkSession
        .builder
        .appName(app_name)
        .master("spark://financial-risk-spark-master:7077")  # Conecta al cluster Spark de repo1
        .config("spark.executor.memory", "2g")
        .config("spark.executor.cores", "2")
        .config("spark.driver.memory", "2g")
        # === Configuración S3 ===
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID", ""))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
        .config("spark.hadoop.fs.s3a.endpoint", os.getenv("S3_ENDPOINT", "s3.amazonaws.com"))
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        # === Configuración Delta (opcional pero recomendado) ===
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        # === Configuración Logging ===
        .config("spark.driver.log.level", "INFO")
        # === Evitar warnings de deprecated APIs ===
        .config("spark.sql.legacy.timeParser.enabled", "true")
        .getOrCreate()
    )
    
    spark.sparkContext.setLogLevel("INFO")
    
    return spark
