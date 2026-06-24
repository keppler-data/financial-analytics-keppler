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

Datasets
---------
- Home Credit Default Risk
- Lending Club Accepted Loans
- Lending Club Rejected Loans

Arquitectura
-------------
Kaggle
    ↓
Download
    ↓
Extract
    ↓
Parquet
    ↓
Amazon S3 Bronze
    ↓
Validation
    ↓
Cleanup

Notas
------
Los imports de los pipelines se realizan
dentro de los callables para evitar que
Airflow ejecute dependencias externas
durante el parseo del DAG.
"""

import sys

# ==========================================
# DATA PLATFORM PATH
# ==========================================

sys.path.append(
    "/opt/airflow/data-platform"
)

from airflow import DAG
from airflow.operators.empty import (
    EmptyOperator,
)
from airflow.operators.python import (
    PythonOperator,
)

from pendulum import datetime


# ==========================================
# HOME CREDIT
# ==========================================

def run_home_credit():

    from pipelines.tasks.homeCredit.ingestion_task import (
        ingest_home_credit,
    )

    return ingest_home_credit()


# ==========================================
# LENDING ACCEPTED
# ==========================================

def run_lending_accepted():

    from pipelines.tasks.lendingClub.accepted.ingest_lending_accepted import (
        ingest_lending_accepted,
    )

    return ingest_lending_accepted()


# ==========================================
# LENDING REJECTED
# ==========================================

def run_lending_rejected():

    from pipelines.tasks.lendingClub.rejected.ingest_lending_rejected import (
        ingest_lending_rejected,
    )

    return ingest_lending_rejected()


# ==========================================
# DAG DEFINITION
# ==========================================

with DAG(
    dag_id="raw_ingestion",
    description=(
        "Carga datasets financieros "
        "desde Kaggle hacia Bronze S3"
    ),
    start_date=datetime(
        2026,
        1,
        1,
        tz="UTC",
    ),
    schedule=None,
    catchup=False,
    tags=[
        "bronze",
        "raw",
        "financial",
        "ingestion",
    ],
) as dag:

    # ======================================
    # START
    # ======================================

    start = EmptyOperator(
        task_id="start"
    )

    # ======================================
    # HOME CREDIT
    # ======================================

    home_credit = PythonOperator(
        task_id="home_credit_ingestion",
        python_callable=run_home_credit,
    )

    # ======================================
    # LENDING ACCEPTED
    # ======================================

    lending_accepted = PythonOperator(
        task_id="lending_accepted_ingestion",
        python_callable=run_lending_accepted,
    )

    # ======================================
    # LENDING REJECTED
    # ======================================

    lending_rejected = PythonOperator(
        task_id="lending_rejected_ingestion",
        python_callable=run_lending_rejected,
    )

    # ======================================
    # END
    # ======================================

    end = EmptyOperator(
        task_id="end"
    )

    # ======================================
    # DEPENDENCIES
    # ======================================
    #
    # Las tres ingestas son independientes
    # y pueden ejecutarse en paralelo.
    #

    start >> [
        home_credit,
        lending_accepted,
        lending_rejected,
    ] >> end