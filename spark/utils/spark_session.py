# -*- coding: utf-8 -*-
"""
Common Spark utilities and session management
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import *
import logging

logger = logging.getLogger(__name__)

def get_spark_session(app_name="financial-risk-lakehouse"):
    """
    Create or retrieve Spark session with optimized configurations
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.adaptive.skewJoin.enabled", "true") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.default.parallelism", "200") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.executor.cores", "4") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("INFO")
    logger.info(f"Spark session created: {app_name}")
    
    return spark

def read_parquet(spark, path):
    """Read Parquet file with error handling"""
    try:
        df = spark.read.parquet(path)
        logger.info(f"Successfully read Parquet from {path}")
        return df
    except Exception as e:
        logger.error(f"Error reading Parquet from {path}: {str(e)}")
        raise

def write_parquet(df, path, mode="overwrite", partition_cols=None):
    """Write DataFrame to Parquet with partitioning support"""
    try:
        write_df = df.write.mode(mode).format("parquet")
        if partition_cols:
            write_df = write_df.partitionBy(*partition_cols)
        write_df.save(path)
        logger.info(f"Successfully wrote Parquet to {path}")
    except Exception as e:
        logger.error(f"Error writing Parquet to {path}: {str(e)}")
        raise
