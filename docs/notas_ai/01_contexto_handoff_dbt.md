# Contexto de Proyecto: Buró de Crédito Central (CASO 5)
> **Nota para el Asistente AI:** Este documento es un resumen de contexto (Handoff) generado para continuar el desarrollo en una nueva sesión o chat. Lee este documento cuidadosamente para entender el estado de la arquitectura y los próximos pasos.

## 1. Visión General
Estamos resolviendo el **Caso 5: Descontrol Operacional y Riesgo Crediticio**. El objetivo es construir un Data Warehouse centralizado (Buró de Crédito) integrando 4 fuentes de Kaggle: *Home Credit*, *Lending Club*, *Give Me Some Credit* y *Loan Prediction*.

La arquitectura base es una **Lambda Híbrida** desplegada en AWS EC2 (con contenedores Docker):
- **Capa Speed/ODS:** PostgreSQL para eventos en tiempo real.
- **Capa Batch:** S3 (Bronze/Silver/Gold), Spark (Procesamiento masivo), dbt (Transformación) y Athena (Motor de consultas).
- **Orquestador:** Apache Airflow.

---

## 2. Lo que hemos logrado hasta ahora (Capa Bronze -> Silver)
Hemos construido exitosamente el pipeline de limpieza técnica masiva:
1. **PySpark Genérico y Optimizado (`bronze_to_silver_transform.py`):**
   - Lee archivos pesados de S3 (soporta `.csv` y `.csv.gz` nativamente).
   - Estandariza nombres de columnas (snake_case, sin espacios).
   - Convierte variables como `days_` a `years_`.
   - Elimina columnas con más del 80% de nulos usando lógicas eficientes de PySpark.
   - Es **idempotente** (verifica a través de Hadoop FS API si la ruta Silver ya existe para ahorrar costos y saltar el procesamiento).
   - Escribe de regreso a S3 en formato **Parquet**.
   - Genera reportes Markdown (Métricas de volumen, columnas eliminadas) y los sube nativamente a S3 usando Py4J.
2. **Orquestador Airflow (`spark_silver_all_datasets_dag.py`):**
   - Construimos un "Súper DAG" iterativo que pasa dinámicamente argumentos por CLI (`--dataset-name`, `--file-name`) al script de Spark a través del `SSHOperator`.
   - Tiene `max_active_tasks=1` para asegurar la carga secuencial y no ahogar el clúster.

*El código actual se encuentra integrado en la rama `dev2`.*

---

## 3. Estado Actual y Próximos Pasos (Rama actual: `dbt/v1`)

De acuerdo con el blueprint (`ARCHITECTURE_BLUEPRINT_FINAL.md`), el ciclo natural ahora es conectar la capa analítica de negocio.

### Paso 1: Configurar dbt con AWS Athena (Capa Gold - V1)
Necesitamos configurar un proyecto de `dbt-core` (usando el adaptador `dbt-athena-community`).
1. **Fuentes (Sources):** Apuntar dbt a las tablas Parquet de la capa Silver mapeadas en el Glue Data Catalog.
2. **Staging:** Crear modelos SQL para homogeneizar los datos de los 4 bancos (ej. renombrar columnas para que hablen el mismo idioma).
3. **Marts (Tabla Gorda):** Crear una tabla unificada con todas las 122+ variables de Home Credit y los demás. Aquí NO filtramos columnas aún, se las pasamos todas al modelo.

### Paso 2: Feature Selection (Machine Learning - Random Forest)
Con la "Tabla Gorda" en Athena, el científico de datos entra en acción.
1. Leeremos la tabla generada por dbt usando `pandas` o `awswrangler`.
2. Entrenaremos un **Random Forest Classifier** (o XGBoost). 
   - *¿Por qué Random Forest?* Los árboles de decisión y los ensambles tienen una propiedad matemática maravillosa: al realizar los cortes (splits) en los nodos basándose en la entropía o la impureza de Gini, pueden calcular exactamente qué variables separan mejor a los "Buenos pagadores" de los "Malos pagadores".
3. Extraeremos el gráfico de **Feature Importance**. Esto nos dirá, por ejemplo, que solo 20 columnas importan y las otras 100 son puro ruido.
4. **Data Leakage (Fuga de Datos):** En este paso inspeccionaremos si el modelo está usando variables "trampa" (como *collection_recovery_fee* en Lending Club, que solo existe DESPUÉS de que el cliente incumplió).

### Paso 3: Refinar dbt (Capa Gold - V2)
Sabiendo exactamente cuáles son las 20 columnas útiles y cuáles son "trampa" (Leakage), regresaremos a nuestro proyecto de dbt, editaremos los archivos `.sql` para desechar la basura, y volveremos a correr dbt. Esto optimizará el pipeline permanentemente, haciendo que Athena procese muchos menos datos.
