# Bronze Layer Ingestion Architecture

## Overview

La capa Bronze representa el punto de entrada de los datos al Data Lake.

Su objetivo es centralizar la información proveniente de distintas fuentes externas, conservando la mayor fidelidad posible respecto a los datos originales mientras se optimiza el almacenamiento mediante el formato Parquet.

Actualmente la capa Bronze almacena datasets financieros obtenidos desde Kaggle para análisis de riesgo crediticio y evaluación de clientes.

---

# Objectives

* Centralizar fuentes de datos externas.
* Reducir costos de almacenamiento mediante Parquet.
* Facilitar futuras transformaciones hacia Silver.
* Garantizar trazabilidad de la información desde su origen.
* Validar la correcta carga de los archivos en Amazon S3.

---

# Current Data Sources

## Home Credit Default Risk

Fuente:

```text
Kaggle Competition
home-credit-default-risk
```

Destino:

```text
s3://layer-keppler/bronze/home_credit/
```

---

## Lending Club Accepted Loans

Fuente:

```text
Kaggle Dataset
wordsforthewise/lending-club
```

Destino:

```text
s3://layer-keppler/bronze/lending_accepted/
```

---

## Lending Club Rejected Loans

Fuente:

```text
Kaggle Dataset
wordsforthewise/lending-club
```

Destino:

```text
s3://layer-keppler/bronze/lending_rejected/
```

---

# Ingestion Workflow

Cada dataset sigue el mismo flujo de procesamiento.

```text
Kaggle
    ↓
Download
    ↓
Extract
    ↓
CSV / CSV.GZ
    ↓
Parquet Conversion
    ↓
Amazon S3 Bronze
    ↓
Validation
    ↓
Cleanup
```

---

# Processing Steps

## 1. Download

Los datasets son descargados utilizando la API oficial de Kaggle.

Responsabilidades:

* Autenticación.
* Descarga del dataset.
* Gestión de archivos temporales.

---

## 2. Extraction

Aplica únicamente para datasets distribuidos en formato ZIP.

Responsabilidades:

* Descompresión.
* Organización de archivos temporales.

---

## 3. Parquet Conversion

Los archivos CSV son transformados a formato Parquet.

Beneficios:

* Menor tamaño de almacenamiento.
* Lectura optimizada.
* Compatibilidad con Spark.
* Compatibilidad con Athena.
* Compatibilidad con DBT.

---

## 4. Upload to Amazon S3

Los archivos Parquet son cargados a la capa Bronze del Data Lake.

Estructura actual:

```text
layer-keppler/

└── bronze/

    ├── home_credit/

    ├── lending_accepted/

    └── lending_rejected/
```

---

## 5. Validation

Después de la carga se verifica:

* Existencia del archivo en S3.
* Tamaño mayor a cero bytes.

La validación utiliza:

```python
head_object()
```

mediante el SDK de AWS (boto3).

---

## 6. Cleanup

Una vez validada la carga:

* Se eliminan archivos temporales.
* Se eliminan archivos descargados.
* Se libera espacio en disco.

---

# Airflow Integration

Cada fuente posee una task de ingesta independiente.

Ejemplos:

```python
ingest_home_credit()

ingest_lending_accepted()

ingest_lending_rejected()
```

Estas tareas son orquestadas mediante la DAG:

```text
raw_ingestion
```

---

# Parallel Execution Strategy

Las fuentes son independientes entre sí.

Por esta razón la DAG permite ejecución paralela utilizando CeleryExecutor.

```text
                 START

          /       |       \

 Home Credit   Accepted   Rejected

          \       |       /

                  END
```

---

# Future Roadmap

## Silver Layer

Próximas transformaciones:

* Validación de calidad.
* Normalización.
* Estandarización de esquemas.
* Eliminación de duplicados.

---

## Gold Layer

Construcción de:

* Modelo dimensional.
* Tablas de hechos.
* Dimensiones de negocio.
* Métricas analíticas.

---

# Current Status

* [x] Home Credit Ingestion
* [x] Lending Accepted Ingestion
* [x] Lending Rejected Ingestion
* [x] Amazon S3 Upload
* [x] Amazon S3 Validation
* [x] Airflow DAG Design
* [ ] Silver Layer
* [ ] Gold Layer
