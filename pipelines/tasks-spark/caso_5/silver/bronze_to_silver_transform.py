import argparse
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, abs, round, count, when
from pyspark.sql.types import StringType
import re

def clean_column_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def standardize_column_names(df):
    for old_col in df.columns:
        new_col = clean_column_name(old_col)
        if old_col != new_col:
            df = df.withColumnRenamed(old_col, new_col)
    return df

def standardize_target(df):
    """
    Standardize the default indicator across different datasets into a single 'is_default' column.
    """
    cols = df.columns
    
    if 'target' in cols:
        df = df.withColumn('is_default', col('target').cast('integer'))
        df = df.drop('target')
    elif 'loan_status' in cols:
        df = df.withColumn('is_default', 
            when(col('loan_status') == 'Charged Off', 1)
            .when(col('loan_status') == 'Fully Paid', 0)
            .when(col('loan_status') == 'N', 1)
            .when(col('loan_status') == 'Y', 0)
            .otherwise(None)
        )
        df = df.drop('loan_status')
    elif 'seriousdlqin2yrs' in cols:
        df = df.withColumn('is_default', col('seriousdlqin2yrs').cast('integer'))
        df = df.drop('seriousdlqin2yrs')
        
    return df

def trim_string_columns(df):
    string_columns = [f.name for f in df.schema.fields if isinstance(f.dataType, StringType)]
    for c in string_columns:
        df = df.withColumn(c, trim(col(c)))
    return df

def drop_high_null_columns(df, total_rows, threshold=0.8):
    if total_rows == 0:
        return df, []
        
    exprs = [count(when(col(c).isNull(), c)).alias(c) for c in df.columns]
    null_counts_row = df.select(*exprs).first().asDict()
    
    columns_to_drop = []
    for c in df.columns:
        null_count = int(null_counts_row.get(c, 0))
        null_ratio = null_count / total_rows
        if null_ratio > threshold:
            columns_to_drop.append(c)
            
    if columns_to_drop:
        df = df.drop(*columns_to_drop)
        
    return df, columns_to_drop

def convert_days_to_years(df):
    days_cols = [c for c in df.columns if c.startswith('days_')]
    if days_cols:
        for c in days_cols:
            new_col_name = c.replace('days_', 'years_')
            df = df.withColumn(new_col_name, round(abs(col(c)) / 365.25, 1))
            df = df.drop(c)
    return df

def save_report_to_s3(spark, report_path, report_content):
    """Guarda un string directamente en S3 usando Py4J y la API de Hadoop"""
    sc = spark.sparkContext
    URI = sc._gateway.jvm.java.net.URI
    Path = sc._gateway.jvm.org.apache.hadoop.fs.Path
    FileSystem = sc._gateway.jvm.org.apache.hadoop.fs.FileSystem
    
    fs = FileSystem.get(URI(report_path), sc._jsc.hadoopConfiguration())
    out = fs.create(Path(report_path), True) # True for overwrite
    out.write(bytearray(report_content, "utf-8"))
    out.close()

def main():
    parser = argparse.ArgumentParser(description="Generic Bronze to Silver Transform")
    parser.add_argument("--bronze-bucket", required=True)
    parser.add_argument("--silver-bucket", required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--file-name", required=True)
    args = parser.parse_args()

    table_name = args.file_name.split('.')[0]
    
    spark = SparkSession.builder \
        .appName(f"BronzeToSilver_{args.dataset_name}_{table_name}") \
        .getOrCreate()

    # AWS Credentials y Configuración S3
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "s3.amazonaws.com")

    bronze_path = f"s3a://{args.bronze_bucket}/bronze/{args.dataset_name}/{args.file_name}"
    silver_path = f"s3a://{args.silver_bucket}/silver/{args.dataset_name}/{table_name}"
    report_path = f"s3a://{args.silver_bucket}/reports/silver/{args.dataset_name}/{table_name}_report.md"

    # HDFS FileSystem API para comprobaciones
    sc = spark.sparkContext
    URI = sc._gateway.jvm.java.net.URI
    Path = sc._gateway.jvm.org.apache.hadoop.fs.Path
    FileSystem = sc._gateway.jvm.org.apache.hadoop.fs.FileSystem
    fs = FileSystem.get(URI(bronze_path), sc._jsc.hadoopConfiguration())

    # 1. Comprobar Idempotencia (Si ya existe en Silver, saltar)
    # NOTA: Comentamos este bloque para lograr IDEMPOTENCIA REAL. 
    # Ahora siempre procesará y sobreescribirá (.mode("overwrite")), aplicando los cambios nuevos.
    # if fs.exists(Path(silver_path)):
    #     file_statuses = fs.listStatus(Path(silver_path))
    #     if len(file_statuses) > 0:
    #         print(f"La tabla {table_name} ya fue procesada en Silver ({silver_path}). Saltando ejecución para ahorrar recursos.")
    #         spark.stop()
    #         return

    # 2. Comprobar si Bronze existe (Falta de datos)
    if not fs.exists(Path(bronze_path)):
        print(f"ALERTA: El archivo origen no existe en Bronze: {bronze_path}. Saltando.")
        spark.stop()
        return

    start_time = time.time()
    
    # 3. Lectura Genérica
    print(f"Leyendo desde Bronze: {bronze_path}")
    df = spark.read.csv(bronze_path, header=True, inferSchema=True)
    
    original_rows = df.count()
    original_cols = len(df.columns)

    # 4. Transformaciones
    df = df.dropDuplicates()
    dedup_rows = df.count()
    duplicates_dropped = original_rows - dedup_rows

    df = standardize_column_names(df)
    df = standardize_target(df)
    df = trim_string_columns(df)
    df = convert_days_to_years(df)
    df, dropped_cols = drop_high_null_columns(df, original_rows, threshold=0.8)

    # 5. Escritura a Silver
    print(f"Escribiendo a Silver: {silver_path}")
    df.write.mode("overwrite").parquet(silver_path)
    
    duration_sec = int(time.time() - start_time)
    
    # 6. Generación del Reporte MD
    report = f"# Reporte de Transformación: {table_name}\n\n"
    report += f"- **Dataset:** `{args.dataset_name}`\n"
    report += f"- **Archivo Origen:** `{args.file_name}`\n"
    report += f"- **Tiempo de Ejecución:** {duration_sec} segundos\n\n"
    
    report += "## Métricas de Volumen\n"
    report += f"- **Filas Originales:** {original_rows:,}\n"
    report += f"- **Duplicados Eliminados:** {duplicates_dropped:,}\n"
    report += f"- **Filas Finales (Sin duplicados):** {dedup_rows:,}\n"
    report += f"- **Columnas Originales:** {original_cols}\n"
    report += f"- **Columnas Finales:** {len(df.columns)}\n\n"
    
    report += "## Columnas Eliminadas (>80% nulos)\n"
    if dropped_cols:
        for c in dropped_cols:
            report += f"- `{c}`\n"
    else:
        report += "Ninguna columna fue eliminada.\n"

    # Guardar reporte en S3
    print(f"Guardando reporte en: {report_path}")
    save_report_to_s3(spark, report_path, report)
    
    print(f"Proceso completado exitosamente para {table_name}.")
    spark.stop()

if __name__ == "__main__":
    main()
