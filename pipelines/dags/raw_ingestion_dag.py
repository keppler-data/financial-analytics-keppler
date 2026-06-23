"""
RAW INGESTION DAG
=================

Orquesta la carga de datasets externos
hacia la capa Bronze del Data Lake.

Objetivo
---------
Automatizar la descarga, transformación y
almacenamiento de datasets financieros
utilizados en el proyecto Financial Analytics.

Flujo general
-------------
Kaggle
    ↓
Descarga
    ↓
Extracción
    ↓
Conversión a Parquet
    ↓
Carga a Amazon S3 (Bronze)
    ↓
Validación
    ↓
Limpieza de temporales

Datasets actuales
-----------------
- Home Credit Default Risk
- Lending Club Accepted Loans
- Lending Club Rejected Loans

Arquitectura
------------
Las tareas son independientes y pueden
ejecutarse en paralelo utilizando
CeleryExecutor.
"""

import sys 

sys.path.append(
    "/opt/airflow/data-platform"
)

from airflow.sdk import dag, task

from pendulum import datetime

from pipelines.tasks.homeCredit.ingestion_task import (
    ingest_home_credit,
)

from pipelines.tasks.lendingClub.accepted.ingestion_task import (
    ingest_lending_accepted,
)

from pipelines.tasks.lendingClub.rejected.ingestion_task import (
    ingest_lending_rejected,
)


@dag(
    dag_id="raw_ingestion",
    description=(
        "Carga datasets financieros "
        "desde Kaggle hacia Bronze S3"
    ),
    start_date=datetime(
        2026,
        1,
        1,
        tz="UTC"
    ),
    schedule=None,
    catchup=False,
    tags=[
        "bronze",
        "raw",
        "financial",
        "ingestion",
    ],
)
def raw_ingestion():
    """
    DAG principal de ingesta Raw.

    Cada dataset ejecuta:

        Download
            ↓
        Extract
            ↓
        Parquet
            ↓
        Upload S3
            ↓
        Validate
            ↓
        Cleanup

    Las cargas son independientes,
    por lo que Airflow puede ejecutarlas
    en paralelo.
    """

    # ==================================
    # HOME CREDIT
    # ==================================

    home_credit = task(
        task_id="home_credit_ingestion"
    )(
        ingest_home_credit
    )()

    # ==================================
    # LENDING CLUB - ACCEPTED
    # ==================================

    lending_accepted = task(
        task_id="lending_accepted_ingestion"
    )(
        ingest_lending_accepted
    )()

    # ==================================
    # LENDING CLUB - REJECTED
    # ==================================

    lending_rejected = task(
        task_id="lending_rejected_ingestion"
    )(
        ingest_lending_rejected
    )()

    # ==================================
    # EJECUCIÓN PARALELA
    # ==================================
    #
    # No existen dependencias entre
    # datasets, por lo que Airflow
    # puede distribuir la carga entre
    # distintos workers Celery.
    #
    (
        home_credit,
        lending_accepted,
        lending_rejected,
    )


raw_ingestion()