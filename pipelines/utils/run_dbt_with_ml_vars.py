import boto3
import json
import subprocess
import os

def get_ml_features_from_s3(bucket_name, datasets):
    s3 = boto3.client('s3', region_name='us-east-1')
    dbt_vars = {}
    
    for dataset in datasets:
        key = f"reports/ml/{dataset}_ml_features.json"
        try:
            print(f"Descargando {key} desde S3...")
            response = s3.get_object(Bucket=bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)
            
            # Extraer las top features
            features = data.get("top_features", [])
            var_name = f"{dataset}_features"
            dbt_vars[var_name] = features
            print(f" -> Encontradas {len(features)} variables para {dataset}.")
            
        except Exception as e:
            print(f"ERROR: No se pudo obtener o procesar el JSON para {dataset}: {e}")
            # Retornar vacío para que dbt no falle por sintaxis, pero deje un registro
            dbt_vars[f"{dataset}_features"] = []
            
    return dbt_vars

def main():
    # Obtener el bucket desde variables de entorno (Airflow settea AWS variables o las inyectaremos)
    # Por defecto usamos el nombre establecido
    bucket_name = os.environ.get("DIAMOND_BUCKET_NAME", "keppler-data-architecture")
    
    datasets = [
        "home_credit",
        "lending_club",
        "give_me_some_credit",
        "loan_prediction"
    ]
    
    # 1. Armar el diccionario de variables de ML
    dbt_vars = get_ml_features_from_s3(bucket_name, datasets)
    
    # 2. Convertir a string JSON para pasarlo a dbt
    dbt_vars_json = json.dumps(dbt_vars)
    print(f"Variables generadas para dbt: {dbt_vars_json}")
    
    # 3. Ejecutar dbt run
    # Nos movemos al directorio de dbt y ejecutamos
    dbt_dir = "/opt/airflow/pipelines/dbt_transform"
    
    command = [
        "dbt", "run", 
        "--select", "marts", "diamond", 
        "--profiles-dir", ".",
        "--vars", dbt_vars_json
    ]
    
    print(f"Ejecutando: {' '.join(command)}")
    
    try:
        # Popen permite ver el output en tiempo real en Airflow
        process = subprocess.Popen(
            command,
            cwd=dbt_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        for line in process.stdout:
            print(line, end="")
            
        process.wait()
        
        if process.returncode != 0:
            print(f"ERROR: dbt run falló con código {process.returncode}")
            import sys
            sys.exit(process.returncode)
            
        print("¡dbt run finalizado con éxito!")
        
    except Exception as e:
        print(f"Error al ejecutar dbt: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
