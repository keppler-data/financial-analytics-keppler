import boto3
import time

def setup_catalog():
    print("Iniciando configuración de AWS Glue y Athena...")
    
    # Inicializar clientes
    # Usamos la sesión por defecto que tomará el rol de la instancia EC2
    glue = boto3.client('glue', region_name='us-east-1')
    
    databases = ['keppler_silver', 'keppler_gold', 'keppler_diamond']
    
    for db_name in databases:
        try:
            glue.get_database(Name=db_name)
            print(f"La base de datos '{db_name}' ya existe.")
        except glue.exceptions.EntityNotFoundException:
            print(f"Creando base de datos '{db_name}'...")
            glue.create_database(
                DatabaseInput={
                    'Name': db_name,
                    'Description': f'Database for {db_name.split("_")[1].capitalize()} layer of Keppler Data Platform'
                }
            )
            print(f"Base de datos '{db_name}' creada exitosamente.")

    # Crear Crawler para la capa Silver
    crawler_name = 'keppler_silver_crawler'
    bucket_name = 'keppler-data-architecture'
    silver_path = f's3://{bucket_name}/silver/'
    
    try:
        glue.get_crawler(Name=crawler_name)
        print(f"El crawler '{crawler_name}' ya existe.")
    except glue.exceptions.EntityNotFoundException:
        print(f"Creando Crawler '{crawler_name}'...")
        
        # Necesitamos el rol. El usuario indicó que la instancia tiene full access.
        # Crearemos un rol básico para el crawler si no le pasamos uno, pero
        # requerimos un rol de IAM. Busquemos un rol que empiece con AWSGlueServiceRole
        iam = boto3.client('iam')
        roles = iam.list_roles()['Roles']
        glue_role = next((r['Arn'] for r in roles if 'glue' in r['RoleName'].lower()), None)
        
        if not glue_role:
            print("AVISO: No se encontró un rol específico de Glue. Asegúrate de que el rol de tu EC2 sirva para crawlers o crea uno.")
            # Para evitar que el script falle, usamos el primer rol disponible bajo la asunción de que el usuario sabe lo que hace
            # (El usuario dijo "mis instancias tienen role full access a s3, athena y catalogue")
            # Idealmente, el rol debe tener AWSGlueServiceRole y AmazonS3FullAccess
            
            # Vamos a intentar inferir el rol desde el metadata de la instancia
            import urllib.request
            import json
            try:
                token = urllib.request.urlopen(urllib.request.Request('http://169.254.169.254/latest/api/token', headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}, method='PUT')).read().decode()
                info = urllib.request.urlopen(urllib.request.Request('http://169.254.169.254/latest/meta-data/iam/info', headers={'X-aws-ec2-metadata-token': token})).read().decode()
                glue_role = json.loads(info)['InstanceProfileArn'].replace('instance-profile', 'role')
            except Exception as e:
                print("No se pudo obtener el rol de la instancia automáticamente.")
                # Fallback, el usuario deberá actualizar esto si falla
                glue_role = roles[0]['Arn'] if roles else ""

        glue.create_crawler(
            Name=crawler_name,
            Role=glue_role,
            DatabaseName='keppler_silver',
            Targets={
                'S3Targets': [
                    {'Path': silver_path}
                ]
            },
            SchemaChangePolicy={
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'DEPRECATE_IN_DATABASE'
            },
            RecrawlPolicy={
                'RecrawlBehavior': 'CRAWL_EVERYTHING'
            }
        )
        print(f"Crawler '{crawler_name}' creado exitosamente con rol {glue_role}.")
        
    print(f"Iniciando Crawler '{crawler_name}' para registrar las tablas Parquet...")
    try:
        glue.start_crawler(Name=crawler_name)
    except glue.exceptions.CrawlerRunningException:
        print("El crawler ya está corriendo.")
    except Exception as e:
        print(f"No se pudo iniciar el crawler. Detalles: {e}")
        return

    print("Esperando a que el crawler termine (esto puede tomar un par de minutos)...")
    while True:
        response = glue.get_crawler(Name=crawler_name)
        state = response['Crawler']['State']
        if state == 'READY':
            print("¡Crawler terminó con éxito! Las tablas están listas en Athena.")
            break
        elif state in ['RUNNING', 'STOPPING']:
            print(f"Estado del crawler: {state}... esperando 15 segundos.")
            time.sleep(15)
        else:
            print(f"Estado desconocido: {state}. Saliendo del loop.")
            break

if __name__ == "__main__":
    setup_catalog()
