# Propuesta de Infraestructura — Data Platform Keppler
## CASO 5: Descontrol Operacional y Riesgo Crediticio

> **Versión:** 1.0 · **Fecha:** Junio 2026 · **Entorno:** AWS Free Tier  
> **Alcance:** Ingestión desde Kaggle → Bronze → Silver → Gold → Diamond

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Cluster Existente y Estrategia de Reutilización](#2-cluster-existente-y-estrategia-de-reutilización)
3. [Arquitectura de Red y VPC](#3-arquitectura-de-red-y-vpc)
4. [Flujo General End-to-End](#4-flujo-general-end-to-end)
5. [Fase 1 — Extracción y Carga Bronze (Python + Airflow)](#5-fase-1--extracción-y-carga-bronze-python--airflow)
6. [Fase 2 — ETL Distribuido Bronze → Silver (Spark)](#6-fase-2--etl-distribuido-bronze--silver-spark)
7. [Fase 3 — ELT Silver → Gold (dbt + Athena + Glue)](#7-fase-3--elt-silver--gold-dbt--athena--glue)
8. [Fase 4 — Capas Analíticas y ML (Diamond)](#8-fase-4--capas-analíticas-y-ml-diamond)
9. [Modelo Dimensional — Star Schema Financiero](#9-modelo-dimensional--star-schema-financiero)
10. [Stack Tecnológico por Capa](#10-stack-tecnológico-por-capa)
11. [Estructura S3 — Data Lake](#11-estructura-s3--data-lake)
12. [Configuración Spark en Free Tier](#12-configuración-spark-en-free-tier)
13. [Cronograma de 2 Semanas](#13-cronograma-de-2-semanas)

---

## 1. Resumen Ejecutivo

La plataforma resolverá los problemas de **descontrol operacional y riesgo crediticio** de la entidad financiera mediante una arquitectura **Medallion híbrida** (ETL + ELT), distribuida sobre un cluster AWS Free Tier existente con máximo 4 GB RAM por instancia.

### Decisiones Clave de Diseño

| Decisión | Elección | Razón |
|----------|----------|-------|
| Ingestión de datos | Python puro en workers Airflow | Aprovecha cluster existente, sin costos adicionales |
| Procesamiento masivo | Spark Standalone en cluster EC2 | Las mismas instancias Airflow + RabbitMQ + Postgres actúan como Spark workers |
| Formato intermedio | **Apache Iceberg sobre S3** | ACID, time travel, upserts nativos, perfecto para deduplicación |
| Transformaciones analíticas | dbt + Athena + Glue Catalog | ELT sin servidor, pago por query, ideal para Free Tier |
| Orquestación | Airflow con Celery + RabbitMQ | Ya instalado en el cluster |
| Warehouse | PostgreSQL RDS (instancia existente) | Para metadatos Airflow + tablas Gold pequeñas |

---

## 2. Cluster Existente y Estrategia de Reutilización

### 2.1 Inventario del Cluster Actual

```
┌────────────────────────────────────────────────────────────────────┐
│                        VPC PRIVADA AWS                              │
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐  │
│  │  EC2 — MASTER        │    │  EC2 — WORKER 1                  │  │
│  │  Airflow Scheduler   │    │  Airflow Celery Worker           │  │
│  │  Airflow Webserver   │    │  Max 4 GB RAM                    │  │
│  │  Max 4 GB RAM        │    └──────────────────────────────────┘  │
│  └──────────────────────┘                                           │
│                              ┌──────────────────────────────────┐  │
│  ┌──────────────────────┐    │  EC2 — WORKER 2                  │  │
│  │  EC2 — RABBITMQ      │    │  Airflow Celery Worker           │  │
│  │  Message Broker      │    │  Max 4 GB RAM                    │  │
│  │  Celery Backend      │    └──────────────────────────────────┘  │
│  │  Max 4 GB RAM        │                                           │
│  └──────────────────────┘    ┌──────────────────────────────────┐  │
│                              │  EC2 — WORKER 3                  │  │
│  ┌──────────────────────┐    │  Airflow Celery Worker           │  │
│  │  EC2 — POSTGRES      │    │  Max 4 GB RAM                    │  │
│  │  Metadata Airflow    │    └──────────────────────────────────┘  │
│  │  Max 4 GB RAM        │                                           │
│  └──────────────────────┘                                           │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘

     ┌──────────────────────┐
     │  EC2 — PROXY         │  ← Subnet Pública
     │  Nginx Proxy Manager │
     │  Acceso externo UI   │
     └──────────────────────┘
```

### 2.2 Estrategia de Doble Rol: Airflow + Spark

La clave de esta arquitectura es que **las mismas instancias sirven dos propósitos** en distintos momentos del pipeline:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MODO: INGESTIÓN (Python)                         │
│                      Horario: continuo                               │
│                                                                      │
│   Master EC2           Worker 1          Worker 2         Worker 3  │
│  ┌──────────┐         ┌──────────┐      ┌──────────┐    ┌────────┐ │
│  │ Airflow  │─tasks──▶│ Python   │      │ Python   │    │ Python │ │
│  │ Scheduler│         │ Kaggle   │      │ Kaggle   │    │ Kaggle │ │
│  │          │         │ → S3     │      │ → S3     │    │ → S3   │ │
│  └──────────┘         └──────────┘      └──────────┘    └────────┘ │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   MODO: ETL SPARK (Distribuido)                      │
│                    Horario: ventana nocturna                         │
│                                                                      │
│   Master EC2           Worker 1          Worker 2         Worker 3  │
│  ┌──────────┐         ┌──────────┐      ┌──────────┐    ┌────────┐ │
│  │  Spark   │◀───────▶│  Spark   │      │  Spark   │    │ Spark  │ │
│  │  Master  │         │  Worker  │      │  Worker  │    │ Worker │ │
│  │  Driver  │         │  1.5g RAM│      │  1.5g RAM│    │ 1.5g   │ │
│  └──────────┘         └──────────┘      └──────────┘    └────────┘ │
│                                                                      │
│   RabbitMQ EC2              Postgres EC2                            │
│  ┌──────────────┐          ┌───────────────┐                       │
│  │ Spark Worker │          │ Spark Worker  │  ← Se suman al ETL   │
│  │ Adhoc 1.5g   │          │ Adhoc 1.5g    │    cuando no hay      │
│  └──────────────┘          └───────────────┘    carga en Airflow   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Plan de Reconfiguración del Cluster

| Instancia | Rol Primario | Rol Secundario (ETL Spark) | Memoria Spark |
|-----------|-------------|---------------------------|---------------|
| EC2 Master | Airflow Scheduler + Spark Master | Spark Driver | 1.0 GB driver |
| EC2 Worker 1 | Airflow Celery + Spark Worker | Spark Executor | 1.5 GB exec |
| EC2 Worker 2 | Airflow Celery + Spark Worker | Spark Executor | 1.5 GB exec |
| EC2 Worker 3 | Airflow Celery + Spark Worker | Spark Executor | 1.5 GB exec |
| EC2 RabbitMQ | Celery Broker (siempre activo) + Spark Worker | Spark Executor adhoc | 1.5 GB exec |
| EC2 Postgres | Metadata DB (siempre activo) + Spark Worker | Spark Executor adhoc | 1.0 GB exec |

> **Resultado:** Spark cluster con 1 Master + hasta 5 Workers = ~7.5 GB RAM distribuida para ETL

---

## 3. Arquitectura de Red y VPC

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              AWS REGION                                       │
│                                                                               │
│  ┌─────────────────┐                                                          │
│  │  SUBNET PÚBLICA │                                                          │
│  │                 │    Internet Gateway                                       │
│  │  ┌───────────┐  │◀─────────────────── Users / Devs                        │
│  │  │ EC2 PROXY │  │                                                          │
│  │  │  Nginx PM │  │                                                          │
│  │  │  :80/:443 │  │                                                          │
│  │  └─────┬─────┘  │                                                          │
│  └────────┼────────┘                                                          │
│           │ (proxy_pass)                                                      │
│  ┌────────▼──────────────────────────────────────────────────────────────┐   │
│  │                         SUBNET PRIVADA                                 │   │
│  │                                                                        │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐    │   │
│  │  │EC2 MASTER  │  │EC2 WORKER1 │  │EC2 WORKER2 │  │ EC2 WORKER3  │    │   │
│  │  │:8080 AF UI │  │Celery/Spark│  │Celery/Spark│  │ Celery/Spark │    │   │
│  │  │:7077 Spark │  │            │  │            │  │              │    │   │
│  │  │:4040 Spark │  │            │  │            │  │              │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────────┘    │   │
│  │                                                                        │   │
│  │  ┌────────────┐  ┌──────────────┐                                     │   │
│  │  │EC2 RABBITMQ│  │ EC2 POSTGRES │                                     │   │
│  │  │:5672 AMQP  │  │ :5432 DB     │                                     │   │
│  │  │:15672 UI   │  │ Airflow Meta │                                     │   │
│  │  └────────────┘  └──────────────┘                                     │   │
│  │                                                                        │   │
│  │  Security Groups:                                                      │   │
│  │  • sg-airflow: :8080, :8793, :7077, :4040-4045                       │   │
│  │  • sg-spark:   :7077, :7078, :8080 (Spark UI)                        │   │
│  │  • sg-internal: All traffic within subnet                             │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                        AWS MANAGED SERVICES                            │   │
│  │                                                                        │   │
│  │   S3 Buckets             Athena            Glue Catalog               │   │
│  │  ┌───────────┐         ┌────────┐         ┌──────────┐               │   │
│  │  │keppler-   │         │Ad-hoc  │         │ Data     │               │   │
│  │  │data-lake  │◀───────▶│SQL     │◀───────▶│ Catalog  │               │   │
│  │  │/bronze    │         │Queries │         │ Tables   │               │   │
│  │  │/silver    │         └────────┘         └──────────┘               │   │
│  │  │/gold      │                                                        │   │
│  │  │/artifacts │         IAM · CloudWatch · CloudTrail                  │   │
│  │  └───────────┘                                                        │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Flujo General End-to-End

```mermaid
flowchart TD
    subgraph SRC["📦 Fuentes de Datos — CASO 5"]
        direction LR
        KG1["🏠 Home Credit\nDefault Risk\nKaggle API"]
        KG2["💳 Give Me Some\nCredit\nKaggle API"]
        KG3["🏦 Lending Club\nLoan Data\nKaggle API"]
        KG4["📊 Loan Prediction\nDataset\nKaggle API"]
    end

    subgraph AIRFLOW["⚙️ Apache Airflow — Orquestación Central"]
        direction LR
        DAG_B["bronze_pipeline_dag\n⏰ cada 6h"]
        DAG_ETL["etl_spark_dag\n⏰ diario 02:00"]
        DAG_ELT["elt_dbt_dag\n⏰ diario 05:00"]
        DAG_ML["ml_scoring_dag\n⏰ semanal"]
        DAG_MON["monitoring_dag\n⏰ cada 30min"]
    end

    subgraph WORKERS["🖥️ EC2 Workers — Python Tasks"]
        W1["Worker 1\nKaggle Download\nChunked Upload"]
        W2["Worker 2\nKaggle Download\nChunked Upload"]
        W3["Worker 3\nKaggle Download\nChunked Upload"]
    end

    subgraph BRONZE["🟫 BRONZE LAYER — S3 Raw"]
        B1["application_data/\nParquet raw"]
        B2["bureau_data/\nParquet raw"]
        B3["payment_history/\nParquet raw"]
        B4["credit_history/\nParquet raw"]
    end

    subgraph SPARK["⚡ Apache Spark Standalone — ETL Distribuido"]
        SM["Spark Master\n(EC2 Master)"]
        SE1["Executor 1\n(Worker 1)\n1.5g"]
        SE2["Executor 2\n(Worker 2)\n1.5g"]
        SE3["Executor 3\n(Worker 3)\n1.5g"]
        SE4["Executor 4\n(RabbitMQ EC2)\n1.5g — adhoc"]
        SE5["Executor 5\n(Postgres EC2)\n1.0g — adhoc"]
    end

    subgraph SILVER["🥈 SILVER LAYER — S3 Iceberg/Parquet"]
        SV1["customers/\nDeduplicado\nKYC validado"]
        SV2["loans/\nNormalizado\nEnriquecido"]
        SV3["payments/\nConciliado\nTimestamp correcto"]
        SV4["delinquencies/\nMora calculada"]
        SV5["bureau/\nHistorial externo"]
    end

    subgraph GLUE["📚 AWS Glue Catalog"]
        GC["Catálogo de Tablas\ndb: keppler_silver\ndb: keppler_gold"]
    end

    subgraph ELT["🔄 ELT — dbt + Amazon Athena"]
        DBT["dbt Models\nStaging → Intermediate\n→ Marts"]
        ATH["Amazon Athena\nSQL Engine\nsobre S3"]
    end

    subgraph GOLD["🥇 GOLD LAYER — Star Schema"]
        G1["fact_loans"]
        G2["fact_payments"]
        G3["fact_delinquencies"]
        G4["fact_collections"]
        G5["dim_customer"]
        G6["dim_product"]
        G7["dim_time"]
        G8["dim_risk"]
    end

    subgraph DIAMOND["💎 DIAMOND LAYER — ML & Analytics"]
        D1["Feature Store\n(variables riesgo)"]
        D2["Scoring Model\n(PD, LGD, EAD)"]
        D3["Fraud Detection\n(anomalías)"]
        D4["Analytical APIs\nFraude · Riesgo · KPIs"]
    end

    subgraph CONS["📊 Consumo"]
        C1["Power BI\nDashboards\nEjecutivos"]
        C2["Athena\nAd-hoc SQL\nData Science"]
        C3["APIs REST\nIntegración\nexterna"]
    end

    SRC --> DAG_B
    DAG_B --> WORKERS
    WORKERS --> BRONZE

    DAG_ETL --> SM
    SM --- SE1
    SM --- SE2
    SM --- SE3
    SM -.->|"ventana ETL"| SE4
    SM -.->|"ventana ETL"| SE5
    BRONZE --> SM
    SM --> SILVER

    SILVER --> GC
    GC --> ATH
    DAG_ELT --> DBT
    DBT --> ATH
    ATH --> GOLD

    GOLD --> D1
    D1 --> D2
    D1 --> D3
    D2 --> D4
    D3 --> D4

    GOLD --> C1
    GOLD --> C2
    D4 --> C3

    DAG_MON -.->|"alerta"| AIRFLOW
```

---

## 5. Fase 1 — Extracción y Carga Bronze (Python + Airflow)

### 5.1 Diagrama de Secuencia — Ingestión Kaggle → S3

```mermaid
sequenceDiagram
    autonumber
    participant SCH as Airflow Scheduler
    participant RMQ as RabbitMQ
    participant W1 as Worker 1
    participant W2 as Worker 2
    participant W3 as Worker 3
    participant KAG as Kaggle API
    participant S3B as S3 Bronze

    SCH->>RMQ: Encola tareas bronze_pipeline_dag
    Note over SCH: Trigger: cada 6h o manual

    par Descarga paralela por dataset
        RMQ->>W1: Task: download_home_credit()
        RMQ->>W2: Task: download_give_me_credit()
        RMQ->>W3: Task: download_lending_club()
    end

    W1->>KAG: GET /datasets/home-credit-default-risk
    KAG-->>W1: application_train.csv (307k filas)
    W1->>W1: Chunk CSV → Parquet (100k rows/chunk)
    W1->>S3B: PUT /bronze/home_credit/application/dt=2026-06-15/part-0.parquet
    W1->>S3B: PUT /bronze/home_credit/application/dt=2026-06-15/part-1.parquet
    W1->>S3B: PUT /bronze/home_credit/application/dt=2026-06-15/part-2.parquet
    W1-->>SCH: ✅ Task SUCCESS + metadata (rows, size, checksum)

    W2->>KAG: GET /datasets/give-me-some-credit
    KAG-->>W2: cs-training.csv (150k filas)
    W2->>W2: Chunk CSV → Parquet
    W2->>S3B: PUT /bronze/give_me_credit/training/dt=2026-06-15/*.parquet
    W2-->>SCH: ✅ Task SUCCESS

    W3->>KAG: GET /datasets/lending-club
    KAG-->>W3: loan.csv (2.2M filas — chunked)
    W3->>W3: Chunk CSV → Parquet (50k rows/chunk — conservador por RAM)
    W3->>S3B: PUT /bronze/lending_club/loans/dt=2026-06-15/*.parquet
    W3-->>SCH: ✅ Task SUCCESS

    SCH->>SCH: validate_bronze_task()
    SCH->>S3B: HEAD — verificar archivos
    SCH->>SCH: Log manifest: {files, rows, bytes, checksum}
    SCH-->>SCH: ✅ Bronze validation PASSED
```

### 5.2 Código de Referencia — Task de Ingestión

```python
# airflow/tasks/bronze/ingest_kaggle.py

def download_and_upload_to_bronze(dataset_name: str, table_name: str,
                                   chunk_size: int = 50_000, **kwargs):
    """
    Task Airflow: descarga dataset Kaggle en chunks y sube a S3 Bronze.
    Diseñado para workers con máx 4 GB RAM.
    """
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    import boto3
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    s3 = boto3.client('s3')
    bucket = 'keppler-data-lake'
    dt = kwargs['ds']  # 2026-06-15

    # Stream CSV → Parquet chunks → S3
    local_path = f'/tmp/{table_name}.csv'
    api.dataset_download_file(dataset_name, table_name, path='/tmp', unzip=True)

    schema = None
    part = 0
    for chunk in pd.read_csv(local_path, chunksize=chunk_size, low_memory=False):
        table = pa.Table.from_pandas(chunk)
        if schema is None:
            schema = table.schema

        buf = pa.BufferOutputStream()
        pq.write_table(table, buf, compression='snappy')

        s3_key = f'bronze/{dataset_name}/{table_name}/dt={dt}/part-{part:04d}.parquet'
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=buf.getvalue().to_pybytes(),
            Metadata={'source': 'kaggle', 'rows': str(len(chunk)), 'chunk': str(part)}
        )
        part += 1

    return {'status': 'ok', 'parts': part, 'dataset': dataset_name, 'table': table_name}
```

### 5.3 DAG de Bronze

```mermaid
flowchart LR
    ST([Start]) --> DL["download_datasets\n(grupo paralelo)"]

    subgraph DL["Descarga Paralela — Workers"]
        T1["download_home_credit\nWorker 1"]
        T2["download_give_me_credit\nWorker 2"]
        T3["download_lending_club\nWorker 3"]
        T4["download_loan_prediction\nWorker 1 ó 2"]
    end

    T1 & T2 & T3 & T4 --> VAL["validate_bronze\nchecksum + row count"]
    VAL --> META["write_manifest\nS3 metadata.json"]
    META --> ALT{¿Validación OK?}
    ALT -->|✅ OK| END([Bronze DONE])
    ALT -->|❌ Error| ALERT["alert_slack\n+ retry task"]
    ALERT --> DL
```

---

## 6. Fase 2 — ETL Distribuido Bronze → Silver (Spark)

### 6.1 Topología del Cluster Spark Standalone

```
┌──────────────────────────────────────────────────────────────────┐
│                   SPARK STANDALONE CLUSTER                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  EC2 MASTER — Spark Master + Driver                        │  │
│  │  spark://master:7077                                       │  │
│  │  Spark UI: :8080  |  Driver UI: :4040                      │  │
│  │  Memoria Driver: 1.0g  |  Cores: 1                         │  │
│  └────────────────┬───────────────────────────────────────────┘  │
│                   │                                               │
│       ┌───────────┼───────────┬──────────────┐                   │
│       ▼           ▼           ▼              ▼                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │Worker 1 │ │Worker 2 │ │Worker 3 │ │RabbitMQ │               │
│  │Executor │ │Executor │ │Executor │ │Executor │               │
│  │1.5g RAM │ │1.5g RAM │ │1.5g RAM │ │1.5g RAM │               │
│  │2 cores  │ │2 cores  │ │2 cores  │ │1 core   │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
│                                        ┌─────────┐               │
│                                        │Postgres │               │
│                                        │Executor │               │
│                                        │1.0g RAM │               │
│                                        │1 core   │               │
│                                        └─────────┘               │
│                                                                   │
│  Total disponible: ~7.5 GB RAM  |  ~9 cores                     │
│  Particiones recomendadas: 18-24 (2-3x cores)                    │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Diagrama de Secuencia — ETL Spark Bronze → Silver

```mermaid
sequenceDiagram
    autonumber
    participant AF as Airflow DAG
    participant SM as Spark Master
    participant EX as Spark Executors (x3-5)
    participant S3B as S3 Bronze
    participant GE as Great Expectations
    participant S3S as S3 Silver (Iceberg)
    participant GC as Glue Catalog

    AF->>SM: spark-submit etl_bronze_to_silver.py
    Note over SM: spark://ec2-master:7077

    SM->>EX: Distribuir tareas

    SM->>S3B: READ bronze/home_credit/application/*.parquet
    S3B-->>EX: DataFrames particionados (18 partitions)

    Note over EX: TRANSFORMACIONES DISTRIBUIDAS

    par Procesamiento paralelo por partición
        EX->>EX: 1. Deduplicar por SK_ID_CURR
        EX->>EX: 2. Normalizar tipos (int→string donde aplica)
        EX->>EX: 3. Imputar nulos (media/moda por grupo)
        EX->>EX: 4. Calcular income_credit_ratio
        EX->>EX: 5. Calcular debt_burden_ratio
        EX->>EX: 6. Validar rangos (age, income, credit)
        EX->>EX: 7. Enriquecer con bureau_score
    end

    EX-->>SM: DataFrames procesados
    SM->>GE: Ejecutar Expectation Suite "silver_customers"
    GE->>GE: expect_column_values_to_not_be_null(SK_ID_CURR)
    GE->>GE: expect_column_values_to_be_between(AGE, 18, 80)
    GE->>GE: expect_column_unique_value_count_to_be_between(TARGET, 0, 1)
    GE-->>SM: ✅ Validation Report (JSON)

    SM->>S3S: WRITE silver/customers/ (Iceberg format)
    Note over S3S: Particionado por: target / risk_segment
    S3S-->>SM: ✅ Commit Iceberg snapshot

    SM->>GC: Registrar tabla keppler_silver.customers
    GC-->>SM: ✅ Catalog updated

    SM-->>AF: ETL COMPLETED — stats: {rows_in, rows_out, nulls_fixed, dupes_removed}
```

### 6.3 Pipeline de Transformaciones por Tabla

```mermaid
flowchart TD
    subgraph BRONZE["🟫 Bronze — Datos Crudos"]
        B_APP["application_train\n307k filas\n122 columnas"]
        B_BUR["bureau\n1.7M filas"]
        B_BAL["bureau_balance\n27M filas"]
        B_PAY["previous_application\n1.7M filas"]
        B_POS["POS_CASH_balance\n10M filas"]
        B_INS["installments_payments\n13M filas"]
    end

    subgraph TRANS["⚡ Transformaciones Spark"]
        T1["🔍 Deduplicación\npor SK_ID_CURR"]
        T2["🧹 Limpieza\nnulos, outliers"]
        T3["📐 Normalización\ntypes, encoding"]
        T4["🔗 Joins\nbronze tables"]
        T5["📊 Enriquecimiento\nratios calculados"]
        T6["✅ Validación\nGreat Expectations"]
    end

    subgraph SILVER["🥈 Silver — Apache Iceberg"]
        S_CUST["customers\nPerfil limpio\n+ KYC score"]
        S_LOAN["loans\nSolicitudes\nnormalizadas"]
        S_PAY["payments\nPagos\nconciliados"]
        S_BUR["bureau_history\nHistorial externo\nconsolidado"]
        S_DEL["delinquencies\nMora calculada\npor bucket"]
    end

    B_APP --> T1 --> T2 --> T3 --> T5 --> T6 --> S_CUST
    B_BUR & B_BAL --> T4 --> T2 --> T3 --> T6 --> S_BUR
    B_PAY --> T2 --> T3 --> T5 --> T6 --> S_LOAN
    B_POS --> T1 --> T2 --> T5 --> T6 --> S_DEL
    B_INS --> T1 --> T2 --> T5 --> T6 --> S_PAY

    style BRONZE fill:#8B4513,color:#fff
    style SILVER fill:#708090,color:#fff
    style TRANS fill:#2F4F4F,color:#fff
```

---

## 7. Fase 3 — ELT Silver → Gold (dbt + Athena + Glue)

### 7.1 Arquitectura ELT Sin Servidor

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ELT PIPELINE                                     │
│                                                                          │
│  ┌──────────────┐         ┌────────────────────────────────────────┐   │
│  │  dbt Core    │         │         Amazon Athena                   │   │
│  │  (EC2 Master │────────▶│  Motor SQL sobre S3                    │   │
│  │  o Worker)   │ queries │  Presto Engine                         │   │
│  │              │◀────────│  Pago por TB escaneado                  │   │
│  └──────────────┘ results │  ~$5/TB — muy barato para Free Tier    │   │
│                           └────────────────┬───────────────────────┘   │
│                                            │ lee/escribe                │
│                           ┌────────────────▼───────────────────────┐   │
│                           │         S3 Data Lake                    │   │
│                           │  /silver/  (Iceberg — lee dbt)         │   │
│                           │  /gold/    (Parquet — escribe dbt)      │   │
│                           └────────────────────────────────────────┘   │
│                                            │                            │
│                           ┌────────────────▼───────────────────────┐   │
│                           │        AWS Glue Catalog                 │   │
│                           │  keppler_silver.customers               │   │
│                           │  keppler_silver.loans                   │   │
│                           │  keppler_gold.fact_loans                │   │
│                           │  keppler_gold.dim_customer              │   │
│                           └────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Flujo de Modelos dbt

```mermaid
flowchart TD
    subgraph STG["📂 dbt — Staging (1:1 Silver)"]
        STG1["stg_customers\nRenombrar + cast"]
        STG2["stg_loans\nRenombrar + cast"]
        STG3["stg_payments\nRenombrar + cast"]
        STG4["stg_bureau_history\nRenombrar + cast"]
        STG5["stg_delinquencies\nRenombrar + cast"]
    end

    subgraph INT["🔄 dbt — Intermediate (Business Logic)"]
        INT1["int_customer_risk_profile\nAgregar scores\ncalcular segmento"]
        INT2["int_loan_enriched\nJoin bureau\nagregar mora histórica"]
        INT3["int_payment_behavior\nPatrones pago\ncalcular DPD"]
        INT4["int_collection_funnel\nEstado cobranza\nbucket 30-60-90-120"]
    end

    subgraph MART["🥇 dbt — Marts (Star Schema Gold)"]
        DIM_C["dim_customer\nID único + atributos"]
        DIM_P["dim_product\nTipos crédito"]
        DIM_T["dim_time\nCalendario + festivos"]
        DIM_R["dim_risk_category\nSegmentos riesgo"]
        DIM_CH["dim_channel\nCanales digitales"]
        FACT_L["fact_loans\nGrano: 1 fila = 1 crédito"]
        FACT_P["fact_payments\nGrano: 1 fila = 1 pago"]
        FACT_D["fact_delinquencies\nGrano: 1 fila = 1 evento mora"]
        FACT_CO["fact_collections\nGrano: 1 fila = 1 acción cobranza"]
    end

    STG1 --> INT1 --> DIM_C
    STG2 --> INT2 --> FACT_L
    STG3 --> INT3 --> FACT_P
    STG4 --> INT2
    STG5 --> INT4 --> FACT_D & FACT_CO
    INT1 --> DIM_R
    FACT_L --> DIM_P
    FACT_L --> DIM_T
    FACT_L --> DIM_CH

    style STG fill:#1a3a4a,color:#fff
    style INT fill:#2d5a27,color:#fff
    style MART fill:#7a5c00,color:#fff
```

### 7.3 Secuencia dbt + Athena + Glue

```mermaid
sequenceDiagram
    autonumber
    participant AF as Airflow (elt_dbt_dag)
    participant DBT as dbt Core
    participant ATH as Amazon Athena
    participant GC as Glue Catalog
    participant S3S as S3 Silver
    participant S3G as S3 Gold

    AF->>DBT: dbt run --select staging.*
    DBT->>GC: Resolver keppler_silver.customers
    GC-->>DBT: s3://keppler-data-lake/silver/customers/
    DBT->>ATH: CREATE TABLE AS SELECT ... (staging models)
    ATH->>S3S: Scan Silver Parquet
    S3S-->>ATH: DataFrames
    ATH->>S3G: WRITE stg_customers.parquet
    DBT-->>AF: ✅ 5 staging models OK

    AF->>DBT: dbt run --select intermediate.*
    DBT->>ATH: Complex SQL (joins, window functions)
    Note over ATH: int_customer_risk_profile:\nROW_NUMBER() OVER(PARTITION BY customer_id)\nCASE WHEN overdue_30d > 2 THEN 'HIGH' ...
    ATH->>S3G: WRITE intermediate/*.parquet
    DBT-->>AF: ✅ 4 intermediate models OK

    AF->>DBT: dbt run --select marts.*
    DBT->>ATH: Dimensional model SQL
    Note over ATH: fact_loans JOIN dim_customer\nJOIN dim_product JOIN dim_time
    ATH->>S3G: WRITE gold/fact_loans/*.parquet
    ATH->>S3G: WRITE gold/dim_*.parquet
    DBT-->>AF: ✅ 9 mart models OK

    AF->>DBT: dbt test
    DBT->>ATH: Ejecutar tests SQL
    ATH-->>DBT: unique(loan_id): 0 duplicates ✅
    ATH-->>DBT: not_null(customer_id): 0 nulls ✅
    ATH-->>DBT: accepted_values(risk_segment): valid ✅
    DBT-->>AF: ✅ All tests passed

    AF->>GC: Crawler: actualizar Gold tables
    GC-->>AF: ✅ keppler_gold.* updated
```

---

## 8. Fase 4 — Capas Analíticas y ML (Diamond)

```mermaid
flowchart LR
    subgraph GOLD["🥇 Gold Layer"]
        FL[fact_loans]
        FP[fact_payments]
        FD[fact_delinquencies]
        DC[dim_customer]
        DR[dim_risk]
    end

    subgraph FS["💾 Feature Store — S3 + Glue"]
        F1["credit_history_features\n- max_overdue_30d\n- payment_ratio\n- revolving_utilization\n- income_stability_score"]
        F2["behavioral_features\n- channel_preference\n- login_frequency\n- payment_timing_pattern\n- device_consistency"]
        F3["risk_features\n- bureau_score_weighted\n- debt_service_ratio\n- loan_to_income\n- delinquency_trend_3m"]
    end

    subgraph ML["🤖 ML Models — Python/Scikit/XGBoost"]
        M1["🎯 PD Model\nProbability of Default\nXGBoost Classifier\nTarget: TARGET (0/1)"]
        M2["💡 LGD Model\nLoss Given Default\nGradient Boosting\nTarget: % pérdida real"]
        M3["🔍 Fraud Detector\nAnomaly Detection\nIsolation Forest\nTarget: comportamiento atípico"]
        M4["📈 Collection Score\nPropensión al pago\nLogistic Regression\nTarget: pago en cobranza"]
    end

    subgraph API["🌐 APIs de Integración"]
        A1["risk_api\nGET /score/{customer_id}\n→ {pd, lgd, ead, risk_label}"]
        A2["fraud_api\nPOST /evaluate\n→ {score, flags, action}"]
        A3["metrics_api\nGET /kpis\n→ {mora_rate, recovery_rate, ...}"]
    end

    FL & FP & FD --> F1 & F3
    DC & DR --> F2
    F1 & F2 & F3 --> M1 & M2 & M3 & M4
    M1 & M2 --> A1
    M3 --> A2
    M4 & M1 --> A3

    style GOLD fill:#7a5c00,color:#fff
    style FS fill:#1a3a6a,color:#fff
    style ML fill:#3a1a5a,color:#fff
    style API fill:#1a5a3a,color:#fff
```

---

## 9. Modelo Dimensional — Star Schema Financiero

```mermaid
erDiagram

    DIM_CUSTOMER {
        int      customer_id       PK "SK_ID_CURR"
        string   document_type        "CC, CE, NIT"
        string   risk_segment         "LOW/MEDIUM/HIGH/VERY_HIGH"
        string   kyc_status           "VERIFIED / PENDING / REJECTED"
        int      age_years
        string   gender
        string   education_type
        string   family_status
        float    income_total
        string   income_type          "Working, Pensioner..."
        string   organization_type
        int      days_employed
        float    credit_bureau_score
        date     onboarding_date
        string   channel_origin       "Mobile, Web, Partner"
        string   country_region
        string   housing_type
        int      children_count
        boolean  has_car
        boolean  has_realty
    }

    DIM_PRODUCT {
        int      product_id       PK
        string   product_type         "CASH_LOAN, REVOLVING"
        string   product_name
        float    max_amount
        int      max_term_days
        float    interest_rate_annual
        string   repayment_type       "MONTHLY, WEEKLY"
        string   collateral_type      "NONE, PROPERTY, VEHICLE"
    }

    DIM_TIME {
        int      date_id          PK  "YYYYMMDD"
        date     full_date
        int      year
        int      month
        int      week_of_year
        int      quarter
        string   month_name
        boolean  is_weekend
        boolean  is_holiday_co
        boolean  is_end_of_month
        string   fiscal_period
    }

    DIM_RISK_CATEGORY {
        int      risk_id          PK
        string   risk_label           "AAA, AA, A, BBB, BB, B, C, D"
        string   risk_level           "LOW / MEDIUM / HIGH / DEFAULT"
        float    pd_min               "Probabilidad Default mín"
        float    pd_max               "Probabilidad Default máx"
        float    lgd_estimate         "Loss Given Default estimado"
        string   collection_strategy
        int      days_to_action
    }

    DIM_CHANNEL {
        int      channel_id       PK
        string   channel_name         "Mobile App, Web Portal, API..."
        string   platform_type        "Digital, Physical, Hybrid"
        string   device_category      "Mobile, Desktop, Tablet"
        string   os_type
    }

    FACT_LOANS {
        int      loan_sk          PK
        int      loan_id              "SK_ID_CURR (business key)"
        int      customer_id      FK
        int      product_id       FK
        int      application_date_id FK
        int      disbursement_date_id FK
        int      risk_id          FK
        int      channel_id       FK
        float    amount_credit        "Monto aprobado"
        float    amount_annuity       "Cuota mensual"
        float    amount_goods_price   "Precio bien financiado"
        int      term_days
        float    interest_rate
        string   loan_status          "ACTIVE, PAID, DEFAULT, RESTRUCTURED"
        int      target               "0=No default, 1=Default (TARGET)"
        float    pd_score             "Probabilidad default al originar"
        float    income_credit_ratio
        float    debt_service_ratio
        int      prev_applications_count
        int      bureau_credits_active
        float    bureau_overdue_amount
        string   contract_type
    }

    FACT_PAYMENTS {
        int      payment_sk       PK
        int      loan_id          FK
        int      customer_id      FK
        int      payment_date_id  FK
        int      due_date_id      FK
        float    amount_due           "Cuota esperada"
        float    amount_paid          "Monto real pagado"
        float    amount_balance       "Saldo restante"
        int      days_past_due        "DPD — clave para mora"
        boolean  is_full_payment
        boolean  is_partial_payment
        boolean  is_overpayment
        string   payment_method       "PSE, Efectivo, Débito..."
        string   payment_channel
        string   payment_status       "ON_TIME, LATE, MISSED"
    }

    FACT_DELINQUENCIES {
        int      delinq_sk        PK
        int      loan_id          FK
        int      customer_id      FK
        int      report_date_id   FK
        int      risk_id          FK
        int      days_past_due
        string   delinq_bucket        "DPD_30, DPD_60, DPD_90, DPD_120+"
        float    overdue_amount
        float    overdue_pct_balance  "% del saldo total"
        boolean  first_delinquency
        boolean  repeated_delinquency
        string   delinq_cause         "NO_PAYMENT, PARTIAL, DISPUTED"
    }

    FACT_COLLECTIONS {
        int      collection_sk    PK
        int      loan_id          FK
        int      customer_id      FK
        int      action_date_id   FK
        int      risk_id          FK
        string   collection_stage     "PREVENTIVA, TEMPRANA, TARDÍA, JUDICIAL"
        string   action_type          "CALL, SMS, EMAIL, VISIT, LEGAL"
        float    amount_due_at_action
        float    amount_recovered
        float    recovery_rate
        string   action_result        "PAID, PROMISE, REFUSED, NO_CONTACT"
        int      days_to_recovery
        string   agent_id
    }

    DIM_CUSTOMER    ||--o{ FACT_LOANS         : "solicita"
    DIM_PRODUCT     ||--o{ FACT_LOANS         : "tipo producto"
    DIM_TIME        ||--o{ FACT_LOANS         : "fecha solicitud"
    DIM_RISK_CATEGORY ||--o{ FACT_LOANS       : "clasificado"
    DIM_CHANNEL     ||--o{ FACT_LOANS         : "canal origen"
    FACT_LOANS      ||--o{ FACT_PAYMENTS      : "genera pagos"
    FACT_LOANS      ||--o{ FACT_DELINQUENCIES : "puede moras"
    FACT_LOANS      ||--o{ FACT_COLLECTIONS   : "puede cobranza"
    DIM_CUSTOMER    ||--o{ FACT_PAYMENTS      : "realiza"
    DIM_TIME        ||--o{ FACT_PAYMENTS      : "fecha pago"
    DIM_RISK_CATEGORY ||--o{ FACT_DELINQUENCIES : "riesgo actual"
```

---

## 10. Stack Tecnológico por Capa

```mermaid
flowchart TD
    subgraph L0["📡 Fuentes"]
        K["Kaggle API\n(Python kaggle client)"]
    end

    subgraph L1["📥 Ingestión — Capa Bronze"]
        P["Python 3.11\nPandas + PyArrow\nBoto3"]
        AF["Apache Airflow 2.8\nCelery Executor\n4 DAGs producción"]
        RMQ["RabbitMQ 3.x\nCelery Message Broker\nTask Queue"]
    end

    subgraph L2["⚡ ETL — Capa Silver"]
        SP["Apache Spark 3.5\nStandalone Mode\nPySpark"]
        IC["Apache Iceberg 1.5\nTabla format ACID\nTime Travel"]
        GE["Great Expectations 0.18\nData Quality Checks\nExpectation Suites"]
        S3["Amazon S3\nData Lake Storage\nParquet / Iceberg"]
    end

    subgraph L3["🔄 ELT — Capa Gold"]
        DBT["dbt Core 1.8\nSQL Transformations\nLineage + Tests"]
        ATH["Amazon Athena\nPresto SQL Engine\nServerless"]
        GCT["AWS Glue Catalog\nMetastore centralizado\nCrawlers automáticos"]
        PG["PostgreSQL 15\n(RDS Free Tier)\nMetadatos + Gold small"]
    end

    subgraph L4["💎 Analítica y ML"]
        XGB["XGBoost / Scikit-learn\nModelos PD, LGD, LGD"]
        FST["Feature Store\nS3 + Glue\nVersioning de features"]
        API["FastAPI\nRisk API · Fraud API\nMetrics API"]
    end

    subgraph L5["📊 Consumo"]
        PBI["Power BI\nDashboards Ejecutivos"]
        ATH2["Amazon Athena\nAd-hoc SQL\nData Science"]
        EXP["Exports\nCSV · Parquet\nReportes regulatorios"]
    end

    subgraph CROSS["🔒 Transversal"]
        IAM["AWS IAM\nRoles y políticas"]
        CW["AWS CloudWatch\nMonitoreo + Alertas"]
        CT["AWS CloudTrail\nAuditoria completa"]
        GIT["Git + GitHub\nVersion Control\nCI/CD básico"]
    end

    K --> P --> AF
    RMQ --> AF
    AF --> S3
    S3 --> SP
    SP --> IC
    GE --> IC
    IC --> S3
    S3 --> ATH --> DBT --> S3
    GCT --> ATH
    DBT --> PG
    S3 --> FST --> XGB --> API
    S3 --> PBI
    ATH --> ATH2
    API --> EXP
```

---

## 11. Estructura S3 — Data Lake

```
keppler-data-lake/
│
├── bronze/                              ← Datos crudos, inmutables, por fecha
│   ├── home_credit/
│   │   ├── application/
│   │   │   └── dt=2026-06-15/
│   │   │       ├── part-0000.parquet
│   │   │       ├── part-0001.parquet
│   │   │       └── _metadata.json
│   │   ├── bureau/
│   │   │   └── dt=2026-06-15/*.parquet
│   │   ├── bureau_balance/
│   │   ├── previous_application/
│   │   ├── POS_CASH_balance/
│   │   └── installments_payments/
│   ├── give_me_credit/
│   │   └── training/dt=YYYY-MM-DD/*.parquet
│   ├── lending_club/
│   │   └── loans/dt=YYYY-MM-DD/*.parquet
│   └── loan_prediction/
│       └── train/dt=YYYY-MM-DD/*.parquet
│
├── silver/                              ← Datos limpios, Apache Iceberg
│   ├── customers/                       ← Tabla Iceberg
│   │   ├── data/*.parquet               ← Archivos de datos
│   │   └── metadata/                    ← Iceberg metadata
│   │       ├── snap-*.avro             ← Snapshots
│   │       └── *.json                  ← Manifests
│   ├── loans/
│   ├── payments/
│   ├── bureau_history/
│   └── delinquencies/
│
├── gold/                                ← Star Schema, Parquet optimizado
│   ├── fact_loans/
│   │   └── year=2026/month=06/*.parquet
│   ├── fact_payments/
│   ├── fact_delinquencies/
│   ├── fact_collections/
│   ├── dim_customer/
│   ├── dim_product/
│   ├── dim_time/
│   ├── dim_risk_category/
│   └── dim_channel/
│
├── diamond/                             ← Features y modelos ML
│   ├── feature_store/
│   │   ├── credit_history_features/
│   │   ├── behavioral_features/
│   │   └── risk_features/
│   ├── models/
│   │   ├── pd_model_v1/
│   │   └── fraud_detector_v1/
│   └── analytical_products/
│       └── risk_reports/
│
├── artifacts/                           ← Artefactos de calidad y documentación
│   ├── great_expectations/
│   │   ├── bronze_validation_results/
│   │   └── silver_validation_results/
│   ├── dbt_docs/
│   └── pipeline_logs/
│
└── _manifests/                          ← Manifiesto de ingestión por día
    └── dt=YYYY-MM-DD/
        └── manifest.json
```

---

## 12. Configuración Spark en Free Tier

### 12.1 Parámetros Recomendados (4 GB RAM max por instancia)

```bash
# spark-defaults.conf — Configuración conservadora para free tier

spark.master                     spark://ec2-master-private-ip:7077
spark.deploy.mode                client

# Driver (EC2 Master)
spark.driver.memory              1g
spark.driver.cores               1
spark.driver.maxResultSize       512m

# Executors (Workers)
spark.executor.memory            1500m      # 1.5g — deja 2.5g para OS y Airflow
spark.executor.cores             2
spark.executor.instances         3          # Base: 3 workers siempre disponibles

# Serialización y shuffle
spark.serializer                 org.apache.spark.serializer.KryoSerializer
spark.sql.shuffle.partitions     18         # 2x cores totales (3 workers x 2 cores x 3)
spark.default.parallelism        18

# Manejo de memoria
spark.memory.fraction            0.6        # 60% para ejecución, 40% para storage
spark.memory.storageFraction     0.5
spark.sql.adaptive.enabled       true       # AQE — adaptar particiones automáticamente
spark.sql.adaptive.coalescePartitions.enabled true

# S3 — acceso optimizado
spark.hadoop.fs.s3a.impl                org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.fast.upload         true
spark.hadoop.fs.s3a.multipart.size      64m
spark.jars.packages                     org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,\
                                        org.apache.hadoop:hadoop-aws:3.3.4

# Iceberg
spark.sql.catalog.keppler               org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.keppler.type          glue
spark.sql.catalog.keppler.warehouse     s3://keppler-data-lake/silver/
```

### 12.2 Script de Arranque del Cluster Spark

```bash
#!/bin/bash
# scripts/start_spark_cluster.sh
# Ejecutar en EC2 Master antes del ETL window

MASTER_IP=$(hostname -I | awk '{print $1}')
SPARK_HOME=/opt/spark

# Iniciar Master
$SPARK_HOME/sbin/start-master.sh --host $MASTER_IP --port 7077

# Iniciar Worker en Master también (si hay RAM disponible)
$SPARK_HOME/sbin/start-worker.sh spark://$MASTER_IP:7077 \
  --memory 1g --cores 1

echo "Spark Master iniciado en spark://$MASTER_IP:7077"
echo "UI disponible en http://$MASTER_IP:8080"

# Notificar a workers vía Airflow Variable
python3 -c "
from airflow.models import Variable
Variable.set('spark_master_url', 'spark://$MASTER_IP:7077')
"
```

```bash
#!/bin/bash
# scripts/join_spark_worker.sh
# Ejecutar en Workers, RabbitMQ y Postgres durante ventana ETL

MASTER_IP=$1  # Recibe IP del master como argumento
SPARK_HOME=/opt/spark

$SPARK_HOME/sbin/start-worker.sh spark://$MASTER_IP:7077 \
  --memory 1500m --cores 2

echo "Worker iniciado. Conectado a spark://$MASTER_IP:7077"
```

---

## 13. Cronograma de 2 Semanas

```mermaid
gantt
    title Sprint 2 Semanas — Keppler Data Platform CASO 5
    dateFormat  YYYY-MM-DD
    axisFormat  %d/%m

    section 🏗️ Semana 1 — Infraestructura & Bronze
    Configurar S3 buckets + IAM roles           :s1t1,  2026-06-16, 1d
    Instalar Spark Standalone en cluster        :s1t2,  2026-06-16, 2d
    Configurar Security Groups (Spark ports)    :s1t3,  2026-06-16, 1d
    Setup AWS Glue Catalog + Crawlers           :s1t4,  2026-06-17, 1d
    Configurar Athena + workgroup + S3 results  :s1t5,  2026-06-17, 1d
    DAG: bronze_pipeline_dag (Python Kaggle→S3) :s1t6,  2026-06-18, 2d
    Descarga y validación dataset Home Credit   :s1t7,  2026-06-19, 1d
    Descarga Give Me Some Credit + Lending Club :s1t8,  2026-06-19, 1d
    Great Expectations — Suite Bronze           :s1t9,  2026-06-20, 1d
    Test end-to-end Bronze pipeline completo    :s1t10, 2026-06-20, 1d
    Documentar Bronze schema + manifest         :s1t11, 2026-06-21, 1d
    Revisión Semana 1 + ajustes                 :crit, s1rev, 2026-06-21, 1d

    section ⚡ Semana 1-2 — ETL Spark (Bronze→Silver)
    Desarrollar transformaciones Spark (PySpark) :s2t1, 2026-06-22, 2d
    Integración Apache Iceberg                   :s2t2, 2026-06-22, 1d
    ETL customers: dedup + normalización         :s2t3, 2026-06-23, 1d
    ETL loans: joins bureau + enrichment         :s2t4, 2026-06-24, 1d
    ETL payments + delinquencies                 :s2t5, 2026-06-24, 1d
    Great Expectations — Suite Silver            :s2t6, 2026-06-25, 1d
    DAG: etl_spark_dag (Airflow orquesta Spark)  :s2t7, 2026-06-25, 1d
    Test Spark cluster con 3-5 workers           :s2t8, 2026-06-25, 1d

    section 🔄 Semana 2 — ELT dbt + Gold
    Instalar dbt Core + configurar profiles      :s3t1, 2026-06-23, 1d
    Modelos dbt: staging layer (5 modelos)       :s3t2, 2026-06-24, 1d
    Modelos dbt: intermediate layer (4 modelos)  :s3t3, 2026-06-25, 1d
    Modelos dbt: marts Star Schema (9 modelos)   :s3t4, 2026-06-26, 2d
    dbt tests (unique, not_null, relationships)  :s3t5, 2026-06-27, 1d
    DAG: elt_dbt_dag (dbt + Athena + Glue)       :s3t6, 2026-06-27, 1d

    section 💎 Semana 2 — Diamond + Entrega
    Feature engineering (variables riesgo)       :s4t1, 2026-06-26, 1d
    Modelo PD (XGBoost sobre home_credit)        :s4t2, 2026-06-27, 1d
    API risk_api (FastAPI básico)                :s4t3, 2026-06-28, 1d
    DAG: monitoring_dag (alertas + SLAs)         :s4t4, 2026-06-28, 1d
    Power BI conexión a Gold (Athena connector)  :s4t5, 2026-06-28, 1d
    Dashboard: KPIs mora + cartera + riesgo      :s4t6, 2026-06-29, 1d
    Pruebas end-to-end pipeline completo         :crit, s4t7, 2026-06-29, 1d
    Documentación final + walkthrough            :s4t8, 2026-06-29, 1d
    Entrega CASO 5                               :milestone, crit, 2026-06-30, 0d
```

### Tareas Detalladas por Día

| Día | Foco | Entregables |
|-----|------|-------------|
| **Lun 16** | Setup AWS: S3, IAM, Glue, Athena, Spark install | Cluster funcional, buckets creados |
| **Mar 17** | Security Groups, Kaggle API setup, DAG Bronze inicio | Kaggle descarga manual OK |
| **Mié 18** | bronze_pipeline_dag completo (4 datasets) | Bronze con Home Credit completo |
| **Jue 19** | Descarga todos los datasets, GE Bronze Suite | Bronze 100% validado |
| **Vie 20** | Test completo Bronze, ajustes, documentación | Bronze pipeline production-ready |
| **Sáb 21** | Revisión Semana 1, planificación Semana 2 | Review + backlog priorizado |
| **Dom 22** | Descanso / contingencia | — |
| **Lun 23** | dbt install/config + Spark ETL customers/loans | stg_customers, stg_loans OK |
| **Mar 24** | Spark ETL payments + delinq + GE Silver Suite | Silver 80% completo |
| **Mié 25** | Silver completo, intermediate dbt (4 modelos) | int_customer_risk_profile OK |
| **Jue 26** | Marts dbt Star Schema (9 modelos) | fact_loans, dim_customer OK |
| **Vie 27** | dbt tests completos, monitoring_dag, Feature Store | All tests green |
| **Sáb 28** | Modelo PD, risk_api FastAPI, Power BI conexión | API /score/{id} funcionando |
| **Dom 29** | Dashboard final, pruebas E2E, documentación | Entregable completo |
| **Lun 30** | Buffer contingencias + entrega final | ✅ CASO 5 DONE |

---

## Apéndice — KPIs del Dashboard Final

| KPI | Fuente | Frecuencia |
|-----|--------|------------|
| Tasa de Mora 30/60/90 días | fact_delinquencies | Diaria |
| Cartera Vencida (%) | fact_loans + fact_delinquencies | Diaria |
| Probabilidad de Default media por segmento | fact_loans.pd_score | Diaria |
| Tasa de Recuperación en Cobranza | fact_collections | Semanal |
| Ingreso vs Cuota (Debt Service Ratio) | fact_loans | Por origination |
| Aprobaciones vs Rechazos por canal | fact_loans + dim_channel | Diaria |
| Clientes en mora repetida (%) | dim_customer + fact_delinquencies | Semanal |
| Score de Riesgo por segmento | dim_risk_category | Mensual |
| Fraud flags por día | ML Fraud Detector | Tiempo real (via API) |

---

*Propuesta generada para la plataforma Keppler Data Platform*  
*CASO 5 — Descontrol Operacional y Riesgo Crediticio*  
*Junio 2026 — Entorno AWS Free Tier*
