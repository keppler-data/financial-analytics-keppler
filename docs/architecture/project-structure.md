# Project Structure

## Overview

La plataforma sigue una arquitectura modular orientada a la separación de responsabilidades.

Cada componente del sistema tiene una función específica dentro del ciclo de vida de los datos, facilitando:

* Mantenimiento.
* Escalabilidad.
* Reutilización de código.
* Desarrollo colaborativo.
* Pruebas independientes.

---

# High-Level Structure

```text
financial-analytics-keppler/

├── dags/
├── pipelines/
├── docs/
├── tests/
├── storage/
└── pyproject.toml
```

---

# Dags

```text
dags/
```

Contiene los flujos de orquestación de Airflow.

Responsabilidades:

* Definir dependencias.
* Programar ejecuciones.
* Coordinar pipelines.
* Gestionar la ejecución distribuida.

Ejemplos:

```text
raw_ingestion_dag.py
silver_etl_dag.py
gold_convergence_dag.py
```

---

# Pipelines

```text
pipelines/
```

Contiene toda la lógica de procesamiento de datos.

La carpeta se divide en componentes especializados.

---

# Tasks

```text
pipelines/tasks/
```

Contiene las operaciones específicas ejecutadas durante la ingesta y transformación de datos.

Cada tarea tiene una única responsabilidad.

Ejemplo:

```text
homeCredit/

├── download_task.py
├── extract_task.py
├── parquet_task.py
├── cleanup_task.py
└── ingestion_task.py
```

---

## Download Task

Responsabilidad:

```text
Descargar datasets desde la fuente de origen.
```

Ejemplos:

* Kaggle API
* APIs externas
* Sistemas de terceros

---

## Extract Task

Responsabilidad:

```text
Descomprimir archivos y preparar
los datos para procesamiento.
```

Aplica únicamente a datasets comprimidos.

---

## Parquet Task

Responsabilidad:

```text
Convertir archivos CSV
a formato Parquet.
```

Beneficios:

* Mejor compresión.
* Lectura más rápida.
* Compatibilidad con Spark.
* Compatibilidad con Athena.

---

## Upload Task

Responsabilidad:

```text
Transferir archivos procesados
a Amazon S3.
```

---

## Validation Task

Responsabilidad:

```text
Verificar que los archivos
fueron almacenados correctamente.
```

---

## Cleanup Task

Responsabilidad:

```text
Eliminar archivos temporales
generados durante la ejecución.
```

---

## Ingestion Task

Responsabilidad:

```text
Orquestar todas las tareas
de un dataset específico.
```

Ejemplo:

```text
Download
    ↓
Extract
    ↓
Parquet
    ↓
Upload
    ↓
Validate
    ↓
Cleanup
```

---

# Utils

```text
pipelines/utils/
```

Contiene funcionalidades reutilizables compartidas entre múltiples pipelines.

Objetivo:

```text
Evitar duplicación de código.
```

---

## S3 Utilities

```text
pipelines/utils/s3/
```

Componentes:

```text
upload.py
validate.py
```

Responsabilidades:

* Carga de archivos.
* Validación de objetos.
* Integración con Amazon S3.

Beneficio:

Una única implementación puede ser utilizada por todos los datasets.

---

# Documentation

```text
docs/
```

Contiene documentación técnica y funcional del proyecto.

Objetivos:

* Transferencia de conocimiento.
* Onboarding de nuevos integrantes.
* Registro de decisiones arquitectónicas.
* Fuente de verdad del proyecto.

---

# Tests

```text
tests/
```

Espacio destinado para pruebas unitarias e integración.

Tipos de pruebas previstas:

* Unit Tests
* Integration Tests
* Data Quality Tests

---

# Storage

```text
storage/
```

Utilizado durante el desarrollo local para simulaciones y pruebas.

En producción la persistencia principal se realiza en Amazon S3.

---

# Architectural Principles

## Single Responsibility Principle

Cada módulo tiene una única responsabilidad claramente definida.

Ejemplo:

```text
download_task.py
```

solo descarga datos.

---

## Reusability

Las funcionalidades comunes se centralizan en utilidades compartidas.

Ejemplo:

```text
upload_to_s3()
validate_s3_upload()
```

---

## Separation of Concerns

La lógica de negocio, la orquestación y la infraestructura permanecen desacopladas.

```text
Airflow
    ↓
Tasks
    ↓
Utilities
    ↓
AWS Services
```

---

## Scalability

La arquitectura permite:

* Agregar nuevos datasets.
* Agregar nuevas capas.
* Incorporar nuevos servicios.
* Escalar horizontalmente mediante Celery Workers.

---

# Current Status

* [x] Modular Task Design
* [x] Shared S3 Utilities
* [x] Airflow Integration
* [x] Documentation Structure
* [ ] Automated Testing Suite
* [ ] CI/CD Integration
