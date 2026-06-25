import boto3
import os
import tempfile
import pyarrow.parquet as pq

def map_type(pa_type_str):
    pa_type_str = pa_type_str.lower()
    if 'int8' in pa_type_str: return 'tinyint'
    if 'int16' in pa_type_str: return 'smallint'
    if 'int32' in pa_type_str: return 'int'
    if 'int64' in pa_type_str: return 'bigint'
    if 'float16' in pa_type_str or 'float32' in pa_type_str: return 'float'
    if 'float64' in pa_type_str or 'double' in pa_type_str: return 'double'
    if 'bool' in pa_type_str: return 'boolean'
    if 'timestamp' in pa_type_str: return 'timestamp'
    if 'date' in pa_type_str: return 'date'
    return 'string'

def setup_catalog():
    print("Iniciando registro de esquema (PyArrow) en AWS Glue...")
    glue = boto3.client('glue', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    
    databases = ['keppler_silver', 'keppler_intermediate', 'keppler_gold', 'keppler_diamond']
    
    for db_name in databases:
        try:
            glue.get_database(Name=db_name)
            print(f"Base de datos '{db_name}' ya existe.")
        except glue.exceptions.EntityNotFoundException:
            print(f"Creando base de datos '{db_name}'...")
            glue.create_database(
                DatabaseInput={'Name': db_name, 'Description': f'Capa {db_name}'}
            )

    bucket = 'keppler-data-architecture'
    
    print("Buscando datasets en la capa Silver...")
    resp_ds = s3.list_objects_v2(Bucket=bucket, Prefix='silver/', Delimiter='/')
    if 'CommonPrefixes' not in resp_ds:
        print("No se encontraron datasets.")
        return
        
    for ds_prefix in resp_ds['CommonPrefixes']:
        dataset_path = ds_prefix['Prefix']
        
        resp_tb = s3.list_objects_v2(Bucket=bucket, Prefix=dataset_path, Delimiter='/')
        if 'CommonPrefixes' not in resp_tb:
            continue
            
        for tb_prefix in resp_tb['CommonPrefixes']:
            table_path = tb_prefix['Prefix']
            table_name = table_path.strip('/').split('/')[-1]
            
            try:
                glue.get_table(DatabaseName='keppler_silver', Name=table_name)
                print(f"-> Tabla '{table_name}' ya existe en Glue. Saltando.")
                continue
            except glue.exceptions.EntityNotFoundException:
                pass
                
            print(f"-> Descubriendo esquema para '{table_name}'...")
            objects = s3.list_objects_v2(Bucket=bucket, Prefix=table_path, MaxKeys=5)
            parquet_key = None
            for obj in objects.get('Contents', []):
                if obj['Key'].endswith('.parquet'):
                    parquet_key = obj['Key']
                    break
                    
            if not parquet_key:
                print(f"   [!] No se encontraron archivos parquet para {table_name}.")
                continue
                
            tmp_file = os.path.join(tempfile.gettempdir(), f"{table_name}_tmp.parquet")
            s3.download_file(bucket, parquet_key, tmp_file)
            
            try:
                schema = pq.read_schema(tmp_file)
            except Exception as e:
                print(f"   [!] Error leyendo el parquet: {e}")
                os.remove(tmp_file)
                continue
            os.remove(tmp_file)
            
            columns = []
            for name in schema.names:
                athena_type = map_type(str(schema.field(name).type))
                columns.append({'Name': name, 'Type': athena_type})
                
            s3_location = f"s3://{bucket}/{table_path}"
            
            table_input = {
                'Name': table_name,
                'TableType': 'EXTERNAL_TABLE',
                'Parameters': {'classification': 'parquet'},
                'StorageDescriptor': {
                    'Columns': columns,
                    'Location': s3_location,
                    'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
                        'Parameters': {'serialization.format': '1'}
                    }
                }
            }
            
            glue.create_table(DatabaseName='keppler_silver', TableInput=table_input)
            print(f"   [+] ¡Tabla '{table_name}' registrada en Glue con éxito! ({len(columns)} columnas)")

    print("Proceso de Catálogo completado con éxito.")

if __name__ == "__main__":
    setup_catalog()
