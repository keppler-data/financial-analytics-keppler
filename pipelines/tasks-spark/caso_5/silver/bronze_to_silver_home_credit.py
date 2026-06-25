import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, abs, round
from pyspark.sql.types import StringType
import re

def clean_column_name(name: str) -> str:
    """Convierte a minúsculas y reemplaza espacios/caracteres por guiones bajos."""
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def standardize_column_names(df):
    """Estandariza los nombres de todas las columnas en el DataFrame."""
    print("Limpiando nombres de columnas...")
    for old_col in df.columns:
        new_col = clean_column_name(old_col)
        if old_col != new_col:
            df = df.withColumnRenamed(old_col, new_col)
    return df

def trim_string_columns(df):
    """Elimina espacios en blanco al inicio y final de columnas tipo texto."""
    print("Aplicando trim() a columnas de texto...")
    string_columns = [f.name for f in df.schema.fields if isinstance(f.dataType, StringType)]
    for c in string_columns:
        df = df.withColumn(c, trim(col(c)))
    return df

def drop_high_null_columns(df, threshold=0.8):
    """
    Elimina columnas que superen el porcentaje de nulos indicado.
    Imprime el conteo y la lista de columnas eliminadas.
    """
    print(f"Calculando nulos para eliminar columnas con más del {threshold*100}% de vacíos...")
    total_rows = df.count()

    if total_rows == 0:
        return df

    # Optimizamos contando los valores no nulos con summary("count")
    counts_row = df.summary("count").first().asDict()
    
    columns_to_drop = []
    for c in df.columns:
        # 'summary' retorna string, hay que parsear
        non_null_count = int(counts_row.get(c, 0))
        null_count = total_rows - non_null_count
        null_ratio = null_count / total_rows
        
        if null_ratio > threshold:
            columns_to_drop.append(c)
            
    if columns_to_drop:
        print(f"Se eliminarán {len(columns_to_drop)} columnas que superan el {threshold*100}% de nulos:")
        print(columns_to_drop)
        df = df.drop(*columns_to_drop)
    else:
        print("Ninguna columna superó el umbral de nulos. No se eliminó nada.")
        
    return df

def convert_days_to_years(df):
    """
    Convierte las columnas de formato DAYS_* (días negativos) a años positivos.
    Ejemplo: days_birth = -15000 -> years_birth = 41.1
    """
    days_cols = [c for c in df.columns if c.startswith('days_')]
    if days_cols:
        print(f"Convirtiendo columnas DAYS a formato AÑOS: {days_cols}")
        for c in days_cols:
            new_col_name = c.replace('days_', 'years_')
            # Matemática: Valor absoluto dividido entre 365.25 (años bisiestos) a 1 decimal
            df = df.withColumn(new_col_name, round(abs(col(c)) / 365.25, 1))
            df = df.drop(c) # Eliminamos la original en días
    return df

def main():
    parser = argparse.ArgumentParser(description="Bronze to Silver: Home Credit")
    parser.add_argument("--bronze-bucket", required=True, help="Bucket de origen (Bronze)")
    parser.add_argument("--silver-bucket", required=True, help="Bucket de destino (Silver)")
    parser.add_argument("--table-name", required=True, help="Nombre del archivo a procesar (ej. application_train)")
    args = parser.parse_args()

    print(f"Iniciando procesamiento de tabla: {args.table_name}")

    # 1. Inicializar SparkSession
    spark = SparkSession.builder \
        .appName(f"BronzeToSilver_HomeCredit_{args.table_name}") \
        .getOrCreate()

    # 2. Configuración S3 IAM Roles
    spark.sparkContext._jsc.hadoopConfiguration().set(
        "fs.s3a.aws.credentials.provider", 
        "com.amazonaws.auth.DefaultAWSCredentialsProviderChain"
    )
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "s3.amazonaws.com")

    # Definir rutas
    bronze_path = f"s3a://{args.bronze_bucket}/bronze/home_credit/{args.table_name}.csv"
    silver_path = f"s3a://{args.silver_bucket}/silver/home_credit/{args.table_name}"

    # 3. Lectura
    print(f"Leyendo datos desde Bronze: {bronze_path}")
    df = spark.read.csv(bronze_path, header=True, inferSchema=True)
    print(f"Esquema original: {len(df.columns)} columnas. Total registros: {df.count()}")

    # 4. Pipeline de Transformaciones Silver
    df = standardize_column_names(df)
    df = trim_string_columns(df)
    df = convert_days_to_years(df)
    df = drop_high_null_columns(df, threshold=0.8)

    # 5. Escritura a Silver en Parquet
    print(f"Escribiendo datos a Silver: {silver_path}")
    df.write.mode("overwrite").parquet(silver_path)
    
    print(f"¡Proceso completado exitosamente para {args.table_name}! Columnas finales: {len(df.columns)}")
    spark.stop()

if __name__ == "__main__":
    main()
