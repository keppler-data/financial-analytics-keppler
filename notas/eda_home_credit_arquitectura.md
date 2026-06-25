# Refactorización del Flujo EDA - Home Credit

Este documento describe la arquitectura y las decisiones técnicas tomadas para refactorizar la generación de reportes EDA (Exploratory Data Analysis) del dataset de Home Credit. El objetivo principal fue optimizar el proceso para un clúster distribuido de Airflow (v3.2) ejecutado sobre AWS (workers en instancias EC2 con memoria limitada, ~3GB RAM).

## 1. Mapeo Dinámico de Tareas (Dynamic Task Mapping)

En lugar de procesar todos los archivos CSV en un ciclo `for` secuencial dentro de un mismo Worker (lo que genera cuellos de botella y altísimos riesgos de OOM - Out Of Memory), se implementó el **Dynamic Task Mapping** nativo de Airflow (`.expand()`).

### ¿Cómo funciona?
1. **Tarea 1 (`get_files_task`)**: Es una tarea rápida y de muy bajo consumo de memoria que simplemente hace un escaneo (`list_objects`) en el bucket de S3 (`bronze/home_credit/`) y retorna una lista con las rutas exactas (`keys`) de los archivos CSV.
2. **Tarea 2 (`process_file_task`)**: Usando la TaskFlow API de Airflow (`@task`), expandimos esta tarea pasándole la lista del paso anterior (`process_file_task.expand(s3_key=files_to_process)`).

### Beneficios
- **Distribución Paralela:** Airflow crea dinámicamente una instancia de esta tarea por cada archivo CSV. Si hay 7 archivos, se enviarán 7 tareas a la cola de Celery, permitiendo que varios workers disponibles procesen los datasets de manera 100% concurrente.
- **Tolerancia a fallos:** Si la generación del EDA de un CSV particular falla (por corrupción de datos o formato erróneo), esto solo marca como fallida su respectiva sub-tarea. No colapsa ni frena el pipeline para el resto de los archivos.

## 2. Implementación de `ydata-profiling` y Protección de Memoria

Abandonamos la generación estática y básica manual de HTML mediante pandas a favor de `ydata-profiling`, el cual genera reportes HTML exhaustivos, interactivos y sumamente visuales (detección de valores nulos, distribución de variables, matrices de correlación y alertas).

Dado que `ydata-profiling` puede llegar a calcular matrices de interacciones muy costosas, se implementó un **seguro contra colapsos de RAM en los workers**:
```python
is_huge = len(df) > 100000
profile = ProfileReport(df, minimal=is_huge, explorative=True)
```
- **Si el dataset es masivo (> 100k filas)** (ej. `application_train.csv` de Home Credit, que supera las 300k): Se activa automáticamente `minimal=True`. Esto desactiva temporalmente los cálculos más demorados y demandantes de memoria (interacciones cruzadas complejas) pero sigue generando un reporte muy sólido, asegurando que el worker de 3GB sobreviva la ejecución.
- **Si el dataset es normal**: Se procesa de forma exhaustiva (`minimal=False`), aprovechando todas las bondades analíticas de la librería.

## 3. Manejo de Logs (Estándares para Airflow Remoto en S3)

Para garantizar que todos los mensajes y trazas de error queden correctamente centralizados y legibles desde la UI de Airflow, se eliminaron los viejos comandos `print()` y se sustituyeron por el módulo estándar `logging` de Python:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("...")
logger.error("...")
```
Esto es indispensable porque Airflow intercepta estos logs y, mediante la configuración definida en el sistema (`AIRFLOW__LOGGING__REMOTE_LOGGING`), inyecta directamente estas líneas en el bucket remoto en AWS (`logs-s3`). Los `print()` convencionales tienden a perderse al correr bajo CeleryExecutor en clusters paralelos.

## 4. Consolidación de Tareas ELT

Como parte extra de la optimización del caso, el código original de ingesta (descarga de Kaggle -> descompresión de ZIP -> conversión a Parquet -> subida a S3) que estaba innecesariamente fragmentado en 5 módulos (aumentando la fragilidad de importaciones y dificultad de soporte), fue **unificado en un único script** (`ingestion_task.py`).
Se aseguró además la limpieza temporal y persistente de carpetas usando bloques `try / finally` para evitar discos llenos en los nodos.

## 5. Prevención de Crash en el DAG-Processor (Imports Diferidos)

Durante el despliegue a producción, nos enfrentamos a dos errores críticos que hacían colapsar todos los DAGs y que se resolvieron de la siguiente forma:

1. **Error de `pkg_resources` en Python 3.12:**
   La imagen de Airflow 3.2 utiliza Python 3.12, versión en la cual se removió la librería base `setuptools` (que provee `pkg_resources`). Como `ydata-profiling` la necesita, Python arrojaba un error mortal. **Solución:** Se añadió explícitamente `setuptools` en el `.env` (`EXTRA_REQUIREMENTS`) para que la imagen de Docker la instale durante el _build_.

2. **Técnica de *Deferred Imports* (Imports Diferidos):**
   Airflow escanea los archivos en la carpeta de DAGs constantemente. Si tenemos un `import` muy pesado (como `ydata-profiling`) en las primeras líneas de un script, Airflow intentará cargarlo solo para leer la estructura, lo que tumba el proceso si hay algún conflicto de librerías.
   **Solución experta:** Se movió el `import` de la librería pesada **hacia adentro de la función de ejecución**:
   ```python
   def generate_single_eda(s3_key: str):
       from ydata_profiling import ProfileReport # Import diferido
       ...
   ```
   Esto "engaña" a Airflow: el procesador central ignora la librería pesada, y solo el Worker que ejecute la tarea se encargará de importarla. Es una regla de oro para el código en entornos distribuidos.

## Archivos Clave Modificados:
- **`pipelines/dags/eda_s3_report.py`**: El DAG base reescrito bajo arquitectura moderna TaskFlow para aprovechar el `.expand()`.
- **`pipelines/tasks/caso_5/eda/homeCredit/eda_task.py`**: Módulo con la lógica modularizada para extraer CSV, procesar ProfileReport y cargar la capa de reports a S3.
- **`pipelines/tasks/caso_5/eda/homeCredit/ingestion_task.py`**: Pipeline ELT simplificado y consolidado.
- **`cluster-config/master/.env`**: Adición de dependencias analíticas visuales a la capa `EXTRA_REQUIREMENTS` (`ydata-profiling`, `numpy`, `matplotlib`, `scipy`, `seaborn`, `openpyxl`) esenciales para reconstruir la imagen de los Workers y Master Dockerizados.
