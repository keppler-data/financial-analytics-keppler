# Arquitectura de la Plataforma de Riesgo Financiero — Caso 5

> **Autor:** Data Team — Keppler  
> **Versión:** 1.0  
> **Fecha:** Junio 2025  
> **Contexto:** Caso 5 — Descontrol Operacional y Riesgo Crediticio

---

## 1. Visión General — Medallion Architecture

La plataforma sigue el patrón **Medallion Architecture**, un marco de referencia ampliamente adoptado en plataformas de datos modernas (popularizado por Databricks). Este patrón organiza los datos en capas de madurez progresiva, donde cada capa añade valor a través de limpieza, enriquecimiento y agregación.

El objetivo central es transformar datos crudos provenientes de múltiples fuentes (en este caso, 7 tablas del dataset Home Credit Default Risk de Kaggle) en un activo de datos confiable y listo para consumo analítico y modelado predictivo.

```
                        ┌─────────────────────────────────────────────────┐
                        │         POWER BI (Visualización de Negocio)     │
                        └──────────────────────┬──────────────────────────┘
                                               │ CSV exportado
                        ┌──────────────────────┴──────────────────────────┐
                        │   GOLD — Customer 360 (Vista unificada x cliente)│
                        │   Segmentación de riesgo + scoring predictivo   │
                        └──────────────────────┬──────────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────────┐
                        │  QUALITY — Reporte HTML + JSON de Calidad        │
                        │  Métricas: completitud, unicidad, score 0-100   │
                        └──────────────────────┬──────────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────────┐
                        │  SCORING — Modelo Baseline (LR + Random Forest)  │
                        │  Predicción de probabilidad de default           │
                        └──────────────────────┬──────────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────────┐
                        │  INTERMEDIATE — 6 tablas de agregación           │
                        │  Comportamiento de pago, bureau, tarjeta, POS    │
                        └──────────────────────┬──────────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────────┐
                        │  SILVER — Datos limpios, tipados, deduplicados   │
                        │  Tipado explícito, corrección de anomalías      │
                        └──────────────────────┬──────────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────────┐
                        │  BRONZE — Datos crudos con metadata de auditoría│
                        │  Parquet + columnas técnicas (_row_hash, etc.)   │
                        └──────────────────────┬──────────────────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────────┐
                        │  SEED — CSVs originales de Home Credit (Kaggle)  │
                        │  7 archivos descargados manualmente             │
                        └─────────────────────────────────────────────────┘
```

### Principios de cada capa

| Capa | Propósito | Formato | Calidad esperada |
|------|-----------|---------|-------------------|
| **Seed** | Almacenamiento de datos crudos originales, sin modificación alguna | CSV (tal cual de Kaggle) | N/A (fuente) |
| **Bronze** | Captura fiel de los datos de origen con metadata de trazabilidad | Parquet (Snappy) | Baja — datos crudos con nulos y duplicados |
| **Silver** | Datos limpios, tipados y deduplicados, listos para análisis | Parquet (Snappy) | Media-Alta — se corrigen anomalías conocidas |
| **Intermediate** | Agregaciones de comportamiento financiero por cliente | Parquet (Snappy) | Alta — datos numéricos derivados y limpios |
| **Gold** | Vista consolidada de 360° del cliente para negocio y ML | Parquet (Snappy) | Alta — datos enriquecidos y segmentados |

---

## 2. Componentes de Infraestructura

La infraestructura se despliega en una instancia EC2 de AWS usando Docker Compose. Cada servicio se gestiona desde un repositorio independiente (`financial-risk-cluster`) con sus propios archivos de configuración.

### Servicios desplegados

| Servicio | Puerto | Rol en la plataforma | Contenedor |
|----------|--------|---------------------|------------|
| **PostgreSQL 15** | 5432 | Base de datos de metadatos de Airflow (DAG runs, task instances, logs). Almacena el estado completo del orquestador. | `db/` |
| **RabbitMQ 3.13** | 5672 (AMQP) / 15672 (Management) | Broker de mensajes para el executor Celery. Gestiona colas de tareas entre el Airflow Master y los Workers. | `rabbitMQ/` |
| **Airflow Master — Scheduler** | — | Componente que determina cuándo y qué tareas deben ejecutarse. Analiza el DAG y programa las tareas según sus dependencias. | `master/` |
| **Airflow Master — API Server** | 8080 | Expone la API REST y la interfaz web de Airflow. Permite gestionar DAGs, trigger ejecuciones y revisar logs. | `master/` |
| **Airflow Master — DAG Processor** | — | Procesa y parsea los archivos DAG de forma asíncrona para no bloquear el scheduler. Disponible en Airflow 3.x. | `master/` |
| **Airflow Master — Triggerer** | — | Gestiona los triggers de tipo deferrable (tareas que esperan eventos externos sin consumir un slot de worker). | `master/` |
| **Airflow Master — Flower** | 5555 | Interfaz de monitoreo para Celery. Muestra workers activos, tareas en ejecución, éxito/fallo en tiempo real. | `master/` |
| **Airflow Worker (Celery)** | — | Ejecuta las tareas reales del pipeline (ingesta, transformación, modelado). Se comunica con el Master vía RabbitMQ. | `worker/` |
| **Spark Master + Worker** | 8081 (Master UI) / 4040 (App UI) | Clúster Spark en modo standalone. Disponible para transformaciones pesadas (PySpark), aunque actualmente el pipeline usa Pandas. | `spark/` |
| **Nginx Proxy Manager** | 80 / 443 | Proxy inverso que expone Airflow (8080), Grafana (3000) y Spark UI (8081) bajo un único dominio con certificados SSL/TLS. | `proxy/` |
| **Prometheus** | 9090 | Sistema de monitoreo y alertas. Scrapea métricas de Airflow (tiempos de tarea, DAG runs, tamaño de cola Celery) y las almacena en series temporales. | `monitoring/` |
| **Grafana** | 3000 | Plataforma de visualización de métricas. Conecta con Prometheus para mostrar dashboards del estado del pipeline y la infraestructura. | `monitoring/` |

### Diagrama de comunicación entre servicios

```
                    ┌──────────────┐
                    │  Nginx Proxy │ :80 / :443
                    │   Manager    │
                    └──┬───┬───┬───┘
                       │   │   │
            ┌──────────┘   │   └──────────┐
            ▼              ▼              ▼
     ┌────────────┐ ┌───────────┐  ┌──────────┐
     │  Airflow   │ │  Grafana  │  │  Spark   │
     │  Master    │ │   :3000   │  │  UI:8081 │
     │  :8080     │ └─────┬─────┘  └──────────┘
     └──┬────┬────┘           │
        │    │                │ scrape
  Scheduler│  │API Server     │
        │  DAG Processor     ▼
        │  Triggerer    ┌───────────┐
        │  Flower       │ Prometheus│
        │               │   :9090   │
        ▼               └───────────┘
  ┌───────────┐
  │  RabbitMQ │ :5672
  │  Broker   │ :15672 (mgmt)
  └─────┬─────┘
        │ AMQP / RPC
        ▼
  ┌───────────┐
  │  Airflow  │
  │  Worker   │
  │  (Celery) │
  └─────┬─────┘
        │
        ▼
  ┌───────────┐
  │ PostgreSQL│ :5432
  │  (Metadata)│
  └───────────┘
```

---

## 3. Flujo de Datos End-to-End

A continuación se describe el recorrido completo de un dato desde su origen en Kaggle hasta su consumo en Power BI:

### Paso 1: Descarga de datos (manual)

El usuario descarga los 7 archivos CSV del dataset [Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk) desde Kaggle y los deposita en el directorio `data/seed/`. No hay ingesta automatizada desde APIs.

**Tecnologías:** Kaggle → descarga manual → sistema de archivos local (EC2).

### Paso 2: Ingesta Bronze (automatizada)

El DAG de Airflow `case_5_financial_risk_pipeline` dispara la tarea `ingest_bronze`, que ejecuta `ingest_all_bronze()`. Esta función lee cada CSV, detecta automáticamente la codificación (utf-8, latin-1, cp1252), enriquece con columnas técnicas de auditoría (`_ingestion_date`, `_source_file`, `_dataset_name`, `_row_hash`) y escribe como Parquet con compresión Snappy en `data/bronze/<dataset>/`.

**Tecnologías:** Python + Pandas + PyArrow (lector/escritor Parquet).

### Paso 3: Transformación Silver (automatizada)

La tarea `transform_silver` ejecuta `transform_all_silver()`. Lee los Parquet de Bronze, aplica tipado explícito por dataset (enteros nullable `Int64`, cadenas `string`, flotantes `float64`), elimina duplicados por clave primaria, corrige la anomalía de `DAYS_EMPLOYED=365243` (valor centinela que indica desempleo) y reemplaza nulos críticos con valores por defecto. El resultado se escribe en `data/silver/<dataset>/`.

**Tecnologías:** Python + Pandas (casteo de tipos, drop_duplicates, replace).

### Paso 4: Agregación Intermediate (automatizada)

La tarea `build_intermediate` ejecuta `build_all_intermediate()`. Lee las tablas Silver y genera 6 tablas de agregación con métricas de comportamiento financiero por cliente: historial de cuotas, comportamiento de pago temporal, historial en buró de crédito, solicitudes previas, comportamiento de tarjeta de crédito y comportamiento POS CASH. Cada tabla se guarda como Parquet en `data/intermediate/<dataset>/`.

**Tecnologías:** Python + Pandas (groupby, agg, funciones lambda).

### Paso 5: Consolidación Gold (automatizada)

La tarea `build_gold` ejecuta `build_gold_customer_360()`. Toma la tabla `application_train` de Silver como base y realiza left joins con las 6 tablas Intermediate por `SK_ID_CURR`. Calcula columnas derivadas (edad, años empleados, ratio crédito/ingreso, ratio anualidad/ingreso) y segmenta los clientes en `LOW_RISK`, `MEDIUM_RISK` o `HIGH_RISK` según el score de consistencia de pago y días de atraso. El resultado se guarda en `data/gold/gold_customer_360/`.

**Tecnologías:** Python + Pandas (merge, np.select).

### Paso 6: Calidad de Datos (automatizada)

La tarea `quality_report` ejecuta `run_quality_checks()`. Perfila cada dataset de cada capa calculando: conteo de filas, columnas, nulos totales, duplicados, porcentaje de nulos por columna, cardinalidad y un score de calidad 0-100. Genera un reporte HTML autocontenido (dashboard visual con colores por umbral) y un reporte JSON para consumo programático.

**Tecnologías:** Python + Pandas + HTML/CSS embebido.

### Paso 7: Scoring Crediticio (automatizada)

La tarea `ml_scoring` ejecuta `train_scoring_baseline()`. Carga la Gold Customer 360, selecciona 29 features numéricas, divide en train/test (80/20 con estratificación), entrena Logistic Regression y Random Forest con `class_weight="balanced"`, selecciona el mejor modelo por AUC-ROC, genera predicciones sobre todo el dataset, segmenta en riesgo bajo/medio/alto y exporta: scores por cliente (Parquet), métricas (JSON), importancia de features (CSV) y un CSV listo para Power BI.

**Tecnologías:** Python + Scikit-Learn (LogisticRegression, RandomForestClassifier, train_test_split, métricas).

### Paso 8: Consumo en Power BI

El archivo `reports/gold_customer_360_for_powerbi.csv` contiene las columnas clave para análisis visual: `SK_ID_CURR`, `TARGET`, segmentos de riesgo, probabilidad de default, ingresos, crédito, score de consistencia, edad, ratio crédito/ingreso. Este archivo se conecta directamente a Power BI Desktop o Power BI Service mediante el conector de archivos CSV/ carpeta local o SharePoint.

**Tecnologías:** CSV → Power BI (connector de archivo).

---

## 4. Arquitectura de Red

La infraestructura se despliega dentro de una **VPC (Virtual Private Cloud)** de AWS con las siguientes características:

### Topología de red

```
┌──────────────────────────────────────────────────────────┐
│                    VPC AWS (10.0.0.0/16)                  │
│                                                           │
│  ┌─────────────────── Subred Pública ──────────────────┐  │
│  │                                                     │  │
│  │  ┌─────────────┐     ┌──────────────────────────┐  │  │
│  │  │ EC2 Instance│     │  Internet Gateway (IGW)  │  │  │
│  │  │ (t3.medium) │────▶│  IP Elástica asociada   │  │  │
│  │  │             │     └──────────────────────────┘  │  │
│  │  │  Docker     │                                  │  │
│  │  │  Compose    │     Puertos abiertos en SG:      │  │
│  │  │             │     :80   → Nginx Proxy (HTTP)   │  │
│  │  │  ┌───────┐  │     :443  → Nginx Proxy (HTTPS)  │  │
│  │  │  │ All   │  │     :22   → SSH (admin only)      │  │
│  │  │  │Services│  │                                  │  │
│  │  │  └───────┘  │                                  │  │
│  │  └─────────────┘                                  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌──────────────── Subred Privada (futuro) ────────────┐  │
│  │  RDS PostgreSQL, S3 private, Lambda functions       │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Grupos de Seguridad (Security Groups)

| Regla | Puerto | Origen | Propósito |
|-------|--------|--------|-----------|
| Inbound TCP | 22 | IP del administrador | Acceso SSH para gestión |
| Inbound TCP | 80 | 0.0.0.0/0 | Acceso HTTP al Nginx Proxy |
| Inbound TCP | 443 | 0.0.0.0/0 | Acceso HTTPS al Nginx Proxy |
| Outbound TCP | 5432 | Localhost | PostgreSQL (solo interno) |
| Outbound TCP | 5672 | Localhost | RabbitMQ (solo interno) |
| Outbound TCP | 9090 | Localhost | Prometheus (solo interno) |

### Nginx Proxy Manager como puerta de entrada

Nginx Proxy Manager actúa como **proxy inverso** unificado, exponiendo múltiples servicios internos bajo un solo punto de entrada con las siguientes ventajas:

- **SSL/TLS:** Genera y renueva certificados SSL automáticamente (Let's Encrypt).
- **Enrutamiento:** Cada servicio tiene su propio subdominio (ej. `airflow.midominio.com`, `grafana.midominio.com`).
- **Seguridad:** Los puertos internos (8080, 3000, 9090) no se exponen directamente a Internet.
- **Autenticación básica:** Capa adicional de protección antes de llegar a los servicios.

---

## 5. Monitoreo

El sistema de monitoreo se compone de dos herramientas complementarias: **Prometheus** para recolección de métricas y **Grafana** para visualización.

### Prometheus — Recolección de métricas

Prometheus opera en modo **pull**: se conecta periódicamente a los endpoints de métricas de los servicios y almacena los datos como series temporales.

**Métricas scrapeadas de Airflow:**

| Métrica | Descripción |
|---------|-------------|
| `airflow_dag_run_duration` | Duración de cada ejecución del DAG |
| `airflow_task_instance_duration` | Duración de cada tarea individual |
| `airflow_dag_run_status` | Estado de cada DAG run (success/failed/running) |
| `airflow_task_status` | Estado de cada tarea por ejecución |
| `airflow_task_heartbeat` | Latido del scheduler (indica que está vivo) |
| `celery_worker_tasks` | Tareas en ejecución por worker |
| `celery_queue_length` | Tamaño de la cola de tareas pendientes |

**Configuración de scrape en `prometheus.yml`:**

```yaml
scrape_configs:
  - job_name: 'airflow'
    scrape_interval: 15s
    static_configs:
      - targets: ['airflow-master:8080']
    metrics_path: '/admin/metrics'
```

### Grafana — Dashboards de visualización

Grafana consume las métricas almacenadas en Prometheus y las presenta en dashboards interactivos. El acceso es a través de `http://IP_SERVIDOR:3000` (o vía Nginx Proxy con SSL).

**Dashboard implementado — "Pipeline Health":**

| Panel | Tipo | Contenido |
|-------|------|-----------|
| Estado del DAG | Stat | Último estado del DAG (success/failed/running) |
| Duración por tarea | Bar chart | Tiempo de ejecución de cada tarea del pipeline |
| Tareas exitosas vs fallidas | Pie chart | Distribución de estados de tareas |
| Latencia del scheduler | Gauge | Tiempo desde el último heartbeat del scheduler |
| Cola Celery | Time series | Evolución del tamaño de la cola de tareas pendientes |
| DAG Runs por día | Bar chart over time | Cantidad de ejecuciones diarias del pipeline |

**Integración con alertas (futuro):** Grafana puede configurarse para enviar alertas por correo electrónico, Slack o PagerDuty cuando una métrica supere un umbral (ej. AUC-ROC del modelo < 0.65, tasa de fallos > 10%).

---

## 6. Decisiones de Diseño

Esta sección documenta las decisiones técnicas más relevantes y su justificación, siguiendo un formato de ADR (Architecture Decision Record) simplificado.

### 6.1 ¿Por qué Pandas en lugar de Spark para las transformaciones?

**Decisión:** Las transformaciones de Bronze, Silver, Intermediate y Gold se implementan con Pandas (`pd.read_csv`, `pd.to_parquet`, `groupby/agg`) en lugar de PySpark.

**Justificación:**

- **Volumen de datos:** El dataset de Home Credit tiene ~307K filas en `application_train` y ~13.6M en `installments_payments`. Pandas maneja estos volúmenes sin problema en una máquina con 8GB+ de RAM. Spark añade complejidad innecesaria (JVM overhead, serialización) para este tamaño.
- **Velocidad de desarrollo:** Pandas permite iteraciones rápidas durante el desarrollo. El código es más legible y fácil de depurar para un equipo de analistas de datos.
- **Integración con Airflow:** Los `PythonOperator` de Airflow ejecutan funciones Python directamente. Con Pandas, no se necesita un `SparkSubmitOperator` ni un clúster Spark activo para el pipeline principal.
- **Ruta de migración:** La arquitectura está diseñada para que la migración a PySpark sea incremental. Las funciones de transformación reciben y devuelven DataFrames, lo que permite reemplazar Pandas por PySpark con cambios mínimos cuando el volumen lo requiera.

**Trade-off:** Para volúmenes de producción (100M+ filas) o ingesta en tiempo real, Spark sería la opción correcta.

### 6.2 ¿Por qué Parquet como formato de almacenamiento?

**Decisión:** Todas las capas (Bronze, Silver, Intermediate, Gold) almacenan datos en formato Parquet con compresión Snappy.

**Justificación:**

- **Columnar y eficiente:** Parquet almacena datos por columna, permitiendo lectura selectiva de solo las columnas necesarias (column pruning). Esto es especialmente útil en Silver y Gold donde no siempre se necesitan todas las columnas.
- **Compresión Snappy:** Ofrece una excelente relación compresión/velocidad. Los archivos Parquet con Snappy son 3-5x más pequeños que los CSV originales y se leen significativamente más rápido.
- **Preservación de tipos:** A diferencia de CSV, Parquet preserva los tipos de datos (Int64, float64, string, timestamp). Un entero se lee como entero, no como cadena que necesita conversión.
- **Compatibilidad:** Parquet es soportado por Pandas, PySpark, AWS Athena, Power BI, dbt y prácticamente cualquier herramienta moderna de datos.
- **Metadata embebida:** Permite almacenar esquemas y estadísticas de columna dentro del archivo, facilitando la optimización de consultas.

### 6.3 ¿Por qué Airflow 3.x?

**Decisión:** Utilizar Apache Airflow 3.2 como orquestador del pipeline.

**Justificación:**

- **DAG Processor independiente:** Airflow 3.x separa el parseo de DAGs del scheduler en un proceso dedicado (`dag-processor`). Esto mejora la estabilidad del scheduler y permite manejar más DAGs sin degradación.
- **Triggerer para tareas deferrable:** El componente `triggerer` permite que las tareas esperen eventos externos (como la finalización de un trabajo en Spark) sin ocupar un slot de worker, mejorando la eficiencia del clúster.
- **UI mejorada:** La interfaz web de Airflow 3.x incluye mejoras en la visualización de DAGs, métricas de rendimiento y gestión de conexiones.
- **Ecosistema maduro:** Amplia disponibilidad de providers (PostgresOperator, S3Hook, SlackOperator) y documentación exhaustiva.
- **Estándar de la industria:** Airflow es el orquestador más utilizado en proyectos de data engineering, lo que facilita la contratación y la adopción por parte del equipo.

### 6.4 ¿Por qué Celery + RabbitMQ como executor?

**Decisión:** Configurar Airflow con el executor `CeleryExecutor` y RabbitMQ como broker de mensajes.

**Justificación:**

- **Escalabilidad horizontal:** Celery permite agregar workers adicionales sin modificar la configuración del master. Si el pipeline necesita más capacidad, basta con levantar otro contenedor de worker.
- **Desacoplamiento:** El master (scheduler + web) no ejecuta tareas directamente. Se enfoca únicamente en la planificación y exposición de la UI, delegando la ejecución a los workers.
- **RabbitMQ como broker confiable:** RabbitMQ es un broker de mensajes AMQP maduro con persistencia en disco, confirmaciones de entrega y manejo de reconexiones. A diferencia de Redis (que puede usarse como broker), RabbitMQ no pierde mensajes si se reinicia.
- **Colas y enrutamiento:** RabbitMQ soporta colas nombradas, routing keys y exchanges, lo que permite priorizar tareas o separar cargas de trabajo en el futuro.
- **Flower para monitoreo:** Celery se integra nativamente con Flower, que proporciona una interfaz web para inspeccionar workers, tareas exitosas/fallidas y tiempos de ejecución en tiempo real.

**Trade-off:** Para un entorno con un solo worker, el `LocalExecutor` sería más simple. Sin embargo, `CeleryExecutor` se eligió desde el inicio para que la plataforma esté lista para escalar sin cambios de configuración.
