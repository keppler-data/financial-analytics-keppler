# -*- coding: utf-8 -*-
"""
DAG Principal — Caso 5: Financial Risk Pipeline

Pipeline end-to-end que orquesta todas las capas del Data Platform:
Bronze -> Silver -> Intermediate -> Gold -> Quality -> Scoring -> Export Metrics

Las métricas se exportan como JSON que el metrics-exporter lee y expone
en formato Prometheus para que Grafana las consuma.
"""

import sys
sys.path.append("/opt/airflow")

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from ml.training.scoring_baseline import train_scoring_baseline
from pipelines.tasks.caso_5.bronze_tasks import ingest_all_bronze
from pipelines.tasks.caso_5.gold_tasks import build_gold_customer_360
from pipelines.tasks.caso_5.intermediate_tasks import build_all_intermediate
from pipelines.tasks.caso_5.silver_tasks import transform_all_silver
from quality.data_quality_report import run_quality_checks

default_args = {
    "owner": "data-team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 1, 1),
}


def log_pipeline_summary(**kwargs):
    """Registra un resumen final de toda la ejecución del pipeline."""
    ti = kwargs["ti"]

    bronze_result = ti.xcom_pull(task_ids="ingest_bronze", key="return_value")
    silver_result = ti.xcom_pull(task_ids="transform_silver", key="return_value")
    intermediate_result = ti.xcom_pull(task_ids="build_intermediate", key="return_value")
    gold_result = ti.xcom_pull(task_ids="build_gold", key="return_value")
    quality_result = ti.xcom_pull(task_ids="quality_report", key="return_value")
    scoring_result = ti.xcom_pull(task_ids="ml_scoring", key="return_value")

    import logging
    log = logging.getLogger(__name__)
    log.info("=" * 70)
    log.info("RESUMEN DEL PIPELINE — CASO 5 FINANCIAL RISK")
    log.info("=" * 70)
    log.info("Bronze: %s", bronze_result)
    log.info("Silver: %s", silver_result)
    log.info("Intermediate: %s", intermediate_result)
    log.info("Gold: %s", gold_result)
    log.info("Quality: %s", quality_result)
    log.info("Scoring: %s", scoring_result)
    log.info("=" * 70)
    log.info("Pipeline completado exitosamente.")
    log.info("Las métricas están disponibles en Grafana (http://localhost:3000)")
    log.info("  - Dashboard: Data Quality")
    log.info("  - Dashboard: ML Model Metrics")
    log.info("  - Dashboard: Risk Segmentation")
    log.info("  - Dashboard: Financial Risk Pipeline")
    return {
        "bronze": bronze_result,
        "silver": silver_result,
        "intermediate": intermediate_result,
        "gold": gold_result,
        "quality": quality_result,
        "scoring": scoring_result,
    }


with DAG(
    dag_id="case_5_financial_risk_pipeline",
    default_args=default_args,
    description="Pipeline completo Caso 5: Bronze -> Silver -> Intermediate -> Gold -> Quality -> Scoring",
    schedule_interval=None,  # Ejecución manual para demo
    catchup=False,
    tags=["caso-5", "financial-risk", "end-to-end"],
) as dag:

    ingest_bronze = PythonOperator(
        task_id="ingest_bronze",
        python_callable=ingest_all_bronze,
    )

    transform_silver = PythonOperator(
        task_id="transform_silver",
        python_callable=transform_all_silver,
    )

    build_intermediate = PythonOperator(
        task_id="build_intermediate",
        python_callable=build_all_intermediate,
    )

    build_gold = PythonOperator(
        task_id="build_gold",
        python_callable=build_gold_customer_360,
    )

    quality_report = PythonOperator(
        task_id="quality_report",
        python_callable=run_quality_checks,
    )

    ml_scoring = PythonOperator(
        task_id="ml_scoring",
        python_callable=train_scoring_baseline,
    )

    pipeline_summary = PythonOperator(
        task_id="pipeline_summary",
        python_callable=log_pipeline_summary,
    )

    # Cadena secuencial: cada capa depende de la anterior
    # Al finalizar, el metrics-exporter (contenedor Docker) lee automáticamente
    # los JSON generados y los expone a Prometheus para Grafana.
    (
        ingest_bronze
        >> transform_silver
        >> build_intermediate
        >> build_gold
        >> quality_report
        >> ml_scoring
        >> pipeline_summary
    )
