from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

import boto3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os

BUCKET_NAME = "financial-analytics-keppler"
DATASET_KEY = "raw/GiveMeSomeCredit/cs-training.csv"

LOCAL_CSV = "/tmp/cs-training.csv"
REPORT_HTML = "/tmp/eda_report.html"


def download_dataset():

    s3 = boto3.client("s3")

    s3.download_file(
        BUCKET_NAME,
        DATASET_KEY,
        LOCAL_CSV
    )

    print("Dataset descargado desde S3")


def generate_eda():

    df = pd.read_csv(LOCAL_CSV)

    report = []

    report.append("<h1>EDA Report - GiveMeSomeCredit</h1>")

    report.append("<h2>Dimensiones</h2>")
    report.append(f"<p>{df.shape[0]} filas x {df.shape[1]} columnas</p>")

    report.append("<h2>Tipos de Datos</h2>")
    report.append(df.dtypes.to_frame("dtype").to_html())

    report.append("<h2>Estadísticas Descriptivas</h2>")
    report.append(df.describe(include="all").to_html())

    missing = pd.DataFrame({
        "missing": df.isnull().sum(),
        "pct_missing": round(
            (df.isnull().sum() / len(df)) * 100,
            2
        )
    })

    report.append("<h2>Valores Faltantes</h2>")
    report.append(missing.to_html())

    duplicates = df.duplicated().sum()

    report.append("<h2>Duplicados</h2>")
    report.append(f"<p>{duplicates}</p>")

    numeric_cols = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    report.append("<h2>Variables Numéricas</h2>")
    report.append(pd.DataFrame(
        {"column": numeric_cols}
    ).to_html())

    if len(numeric_cols) > 1:

        corr = df[numeric_cols].corr()

        report.append("<h2>Correlaciones</h2>")
        report.append(corr.to_html())

    outlier_rows = []

    for col in numeric_cols:

        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)

        iqr = q3 - q1

        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)

        outliers = (
            (df[col] < lower) |
            (df[col] > upper)
        ).sum()

        outlier_rows.append({
            "column": col,
            "outliers": int(outliers)
        })

    outliers_df = pd.DataFrame(outlier_rows)

    report.append("<h2>Outliers (IQR)</h2>")
    report.append(outliers_df.to_html())

    with open(REPORT_HTML, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print("EDA generado")


def upload_report():

    s3 = boto3.client("s3")

    s3.upload_file(
        REPORT_HTML,
        BUCKET_NAME,
        "reports/cs-training-eda.html"
    )

    print("Reporte cargado en S3")


with DAG(
    dag_id="eda_give_me_some_credit_s3",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    schedule="@daily",
    tags=["eda", "s3", "analytics"]
) as dag:

    download_task = PythonOperator(
        task_id="download_dataset",
        python_callable=download_dataset
    )

    eda_task = PythonOperator(
        task_id="generate_eda",
        python_callable=generate_eda
    )

    upload_task = PythonOperator(
        task_id="upload_report",
        python_callable=upload_report
    )

    download_task >> eda_task >> upload_task