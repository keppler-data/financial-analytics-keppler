# Raw Ingestion DAG

## Overview

La DAG `raw_ingestion` es responsable de orquestar la carga de datos desde fuentes externas hacia la capa Bronze del Data Lake.

Esta capa representa el punto de entrada de los datos dentro de la plataforma analítica.

La DAG coordina la ejecución de los pipelines de ingesta y garantiza que cada dataset complete su ciclo de procesamiento antes de ser utilizado por capas posteriores.

---

# DAG Information

```text
DAG ID:
raw_ingestion
```

Objetivo:

```text
Ingestar datasets financieros desde Kaggle
y almacenarlos en Amazon S3 Bronze.
```

Frecuencia actual:

```text
Manual Trigger
(schedule=None)
```

---

# Datasets Managed

Actualmente la DAG administra las siguientes fuentes:

```text
- Home Credit Default Risk

- Lending Club Accepted Loans

- Lending Club Rejected Loans
```

---

# High-Level Flow

```text
                     RAW INGESTION DAG

                           START
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼

     Home Credit      Lending Accepted    Lending Rejected

          │                   │                   │
          ▼                   ▼                   ▼

      Download           Download          Download

          │                   │                   │
          ▼                   ▼                   ▼

       Extract           CSV.GZ Read        CSV.GZ Read

          │                   │                   │
          ▼                   ▼                   ▼

       Parquet            Parquet            Parquet

          │                   │                   │
          ▼                   ▼                   ▼

      Upload S3         Upload S3          Upload S3

          │                   │                   │
          ▼                   ▼                   ▼

      Validation       Validation         Validation

          │                   │                   │
          ▼                   ▼                   ▼

       Cleanup           Cleanup            Cleanup

          └───────────────────┼───────────────────┘
                              │
                              ▼
                             END
```

---

# Airflow Components

La arquitectura utiliza Apache Airflow como motor principal de orquestación.

Responsabilidades:

* Programación de tareas.
* Monitoreo de ejecuciones.
* Gestión de dependencias.
* Registro de eventos.
* Reintentos automáticos.

---

# Celery Executor

La plataforma utiliza:

```text
CeleryExecutor
```

como estrategia de ejecución distribuida.

Beneficios:

* Escalabilidad horizontal.
* Ejecución paralela.
* Distribución automática de carga.
* Separación entre orquestación y ejecución.

---

# RabbitMQ

RabbitMQ actúa como Message Broker.

Responsabilidades:

```text
Airflow Scheduler
        ↓
RabbitMQ Queue
        ↓
Airflow Workers
```

Funciones:

* Distribución de tareas.
* Balanceo de carga.
* Comunicación entre Scheduler y Workers.

---

# Worker Execution

Cuando la DAG es ejecutada:

```text
Scheduler
    ↓
RabbitMQ
    ↓
Worker
    ↓
Task Execution
```

Cada Worker recibe una tarea específica y ejecuta el pipeline completo asociado al dataset.

---

# Parallel Processing Strategy

Las fuentes de datos son completamente independientes.

Por esta razón no existen dependencias entre tareas.

Ejemplo:

```text
Home Credit
```

no depende de:

```text
Lending Accepted
```

ni de:

```text
Lending Rejected
```

Esto permite que Airflow distribuya la carga entre múltiples Workers.

---

# Expected Execution

```text
Worker 1
└── Home Credit

Worker 2
└── Lending Accepted

Worker 3
└── Lending Rejected
```

Esta estrategia reduce significativamente el tiempo total de ingesta.

---

# Failure Handling

Cada pipeline implementa:

* Validación de archivos.
* Verificación de carga en S3.
* Manejo de excepciones.
* Limpieza de archivos temporales.

Si una fuente falla:

```text
Home Credit
    ❌

Lending Accepted
    ✅

Lending Rejected
    ✅
```

las demás pueden continuar ejecutándose sin interrupción.

---

# Integration with Bronze Layer

Destino final:

```text
layer-keppler/

└── bronze/

    ├── home_credit/

    ├── lending_accepted/

    └── lending_rejected/
```

Todos los datasets son almacenados en formato Parquet.

---

# Future Improvements

## Dynamic Task Mapping

Permitir que nuevas fuentes puedan ser registradas sin modificar la DAG principal.

---

## Dataset Registry

Crear un catálogo centralizado de datasets para automatizar la creación de tareas.

---

## Event-Based Triggers

Ejecutar pipelines en respuesta a eventos en lugar de ejecuciones manuales.

---

# Current Status

* [x] DAG Definition
* [x] Celery Integration
* [x] RabbitMQ Integration
* [x] Parallel Execution Design
* [x] Amazon S3 Integration
* [ ] Dynamic Task Mapping
* [ ] Automated Dataset Registry
