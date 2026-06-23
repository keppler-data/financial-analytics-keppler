# -*- coding: utf-8 -*-
"""
Tareas de la capa Gold — Construcción de Customer 360

Consolida información del cliente desde Silver (application_train) y todas
las tablas Intermediate en una única vista de 360° por cliente, incluyendo
segmentación de riesgo.
"""

import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _load_parquet_safe(path: str, dataset_name: str) -> pd.DataFrame:
    """Carga un Parquet con manejo graceful de errores."""
    if not os.path.exists(path):
        logger.warning("Dataset no encontrado: %s en %s", dataset_name, path)
        return pd.DataFrame()
    try:
        df = pd.read_parquet(path)
        logger.info("Cargado %s: %d filas desde %s", dataset_name, len(df), path)
        return df
    except Exception as e:
        logger.error("Error cargando %s desde %s: %s", dataset_name, path, e)
        return pd.DataFrame()


def _safe_merge(left: pd.DataFrame, right: pd.DataFrame, on: str,
                how: str = "left", suffix: str = "") -> pd.DataFrame:
    """Merge seguro que no falla si el DataFrame derecho está vacío."""
    if right.empty:
        logger.warning("Merge omitido: DataFrame derecho vacío (sufijo: %s)", suffix)
        return left
    cols_to_use = [c for c in right.columns if c != on]
    right_renamed = right.rename(columns={c: f"{c}{suffix}" for c in cols_to_use})
    return left.merge(right_renamed, on=on, how=how)


def build_gold_customer_360() -> dict:
    """
    Construye la tabla Gold Customer 360 uniendo Silver e Intermediate.

    Returns
    -------
    dict con keys: rows, columns, output_path, risk_segments
    """
    silver_dir = os.getenv("SILVER_DIR", "data/silver")
    intermediate_dir = os.getenv("INTERMEDIATE_DIR", "data/intermediate")
    gold_dir = os.getenv("GOLD_DIR", "data/gold")

    # ── 1. Cargar base de clientes desde Silver ──────────────────────────
    app_path = os.path.join(silver_dir, "application_train")
    app_files = [f for f in os.listdir(app_path) if f.endswith(".parquet")] if os.path.exists(app_path) else []

    if not app_files:
        logger.error("No se encontraron datos de application_train en Silver.")
        return {"rows": 0, "columns": 0, "output_path": "", "risk_segments": {}}

    app_df = pd.read_parquet(os.path.join(app_path, app_files[0]))
    logger.info("Base Silver application_train: %d filas, %d columnas", len(app_df), len(app_df.columns))

    # Seleccionar columnas relevantes del perfil del cliente
    customer_cols = [
        "SK_ID_CURR","TARGET","NAME_CONTRACT_TYPE","CODE_GENDER",
        "FLAG_OWN_CAR","FLAG_OWN_REALTY","CNT_CHILDREN",
        "AMT_INCOME_TOTAL","AMT_CREDIT","AMT_ANNUITY","AMT_GOODS_PRICE",
        "NAME_INCOME_TYPE","NAME_EDUCATION_TYPE","NAME_FAMILY_STATUS",
        "NAME_HOUSING_TYPE","DAYS_BIRTH","DAYS_EMPLOYED",
        "REGION_RATING_CLIENT","REGION_RATING_CLIENT_W_CITY",
        "ORGANIZATION_TYPE","EXT_SOURCE_1","EXT_SOURCE_2","EXT_SOURCE_3",
    ]
    available_cols = [c for c in customer_cols if c in app_df.columns]
    gold = app_df[available_cols].copy()

    # ── 2. Cargar y mergear Intermediate ──────────────────────────────────

    # 2a. Agregaciones de cuotas
    install_path = os.path.join(intermediate_dir, "agg_customer_installment_history")
    install_files = [f for f in os.listdir(install_path) if f.endswith(".parquet")] if os.path.exists(install_path) else []
    if install_files:
        install_df = pd.read_parquet(os.path.join(install_path, install_files[0]))
        gold = _safe_merge(gold, install_df, "SK_ID_CURR", suffix="_install")

    # 2b. Features de comportamiento de pago
    behavior_path = os.path.join(intermediate_dir, "fct_customer_payment_behavior_features")
    behavior_files = [f for f in os.listdir(behavior_path) if f.endswith(".parquet")] if os.path.exists(behavior_path) else []
    if behavior_files:
        behavior_df = pd.read_parquet(os.path.join(behavior_path, behavior_files[0]))
        gold = _safe_merge(gold, behavior_df, "SK_ID_CURR", suffix="_behavior")

    # 2c. Historial de bureau
    bureau_path = os.path.join(intermediate_dir, "agg_customer_bureau_history")
    bureau_files = [f for f in os.listdir(bureau_path) if f.endswith(".parquet")] if os.path.exists(bureau_path) else []
    if bureau_files:
        bureau_df = pd.read_parquet(os.path.join(bureau_path, bureau_files[0]))
        gold = _safe_merge(gold, bureau_df, "SK_ID_CURR", suffix="_bureau")

    # 2d. Historial de aplicaciones previas
    prev_app_path = os.path.join(intermediate_dir, "agg_previous_application_history")
    prev_app_files = [f for f in os.listdir(prev_app_path) if f.endswith(".parquet")] if os.path.exists(prev_app_path) else []
    if prev_app_files:
        prev_app_df = pd.read_parquet(os.path.join(prev_app_path, prev_app_files[0]))
        gold = _safe_merge(gold, prev_app_df, "SK_ID_CURR", suffix="_prevapp")

    # 2e. Comportamiento tarjeta de crédito
    cc_path = os.path.join(intermediate_dir, "agg_credit_card_behavior")
    cc_files = [f for f in os.listdir(cc_path) if f.endswith(".parquet")] if os.path.exists(cc_path) else []
    if cc_files:
        cc_df = pd.read_parquet(os.path.join(cc_path, cc_files[0]))
        gold = _safe_merge(gold, cc_df, "SK_ID_CURR", suffix="_cc")

    # 2f. Comportamiento POS CASH
    pos_path = os.path.join(intermediate_dir, "agg_pos_cash_behavior")
    pos_files = [f for f in os.listdir(pos_path) if f.endswith(".parquet")] if os.path.exists(pos_path) else []
    if pos_files:
        pos_df = pd.read_parquet(os.path.join(pos_path, pos_files[0]))
        gold = _safe_merge(gold, pos_df, "SK_ID_CURR", suffix="_pos")

    logger.info("Después de merges: %d filas, %d columnas", len(gold), len(gold.columns))

    # ── 3. Columnas calculadas ────────────────────────────────────────────

    # Edad en años
    if "DAYS_BIRTH" in gold.columns:
        gold["age_years"] = (gold["DAYS_BIRTH"].abs() / 365.25).round(1)

    # Años empleados (excluyendo la anomalía 365243)
    if "DAYS_EMPLOYED" in gold.columns:
        mask_valid = gold["DAYS_EMPLOYED"] != 365243
        gold.loc[mask_valid, "employed_years"] = (gold.loc[mask_valid, "DAYS_EMPLOYED"].abs() / 365.25).round(1)

    # Ratio crédito/ingreso
    if "AMT_CREDIT" in gold.columns and "AMT_INCOME_TOTAL" in gold.columns:
        income_safe = gold["AMT_INCOME_TOTAL"].replace(0, 1)
        gold["credit_to_income_ratio"] = (gold["AMT_CREDIT"] / income_safe).round(4)

    # Ratio anualidad/ingreso
    if "AMT_ANNUITY" in gold.columns and "AMT_INCOME_TOTAL" in gold.columns:
        income_safe = gold["AMT_INCOME_TOTAL"].replace(0, 1)
        gold["annuity_to_income_ratio"] = (gold["AMT_ANNUITY"] / income_safe).round(4)

    # ── 4. Segmentación de riesgo ─────────────────────────────────────────
    # Buscar las columnas de comportamiento, pueden tener sufijos por el merge
    consistency_col = "payment_consistency_score"
    max_overdue_col = None
    for candidate in ["max_days_overdue","max_days_overdue_install","max_days_overdue_behavior"]:
        if candidate in gold.columns:
            max_overdue_col = candidate
            break

    if consistency_col in gold.columns and max_overdue_col:
        conditions = [
            (gold[consistency_col].fillna(0) >= 80) & (gold[max_overdue_col].fillna(0) <= 5),
            (gold[consistency_col].fillna(0) >= 50) & (gold[max_overdue_col].fillna(0) <= 30),
        ]
        choices = ["LOW_RISK","MEDIUM_RISK"]
        gold["risk_segment"] = pd.Series(
            np.select(conditions, choices, default="HIGH_RISK"), index=gold.index
        )
    else:
        logger.warning("No se encontraron columnas de riesgo para segmentar. "
                       "Se asigna MEDIUM_RISK por defecto.")
        gold["risk_segment"] = "MEDIUM_RISK"

    # ── 5. Limpieza final ────────────────────────────────────────────────

    # Timestamp de auditoría
    gold["updated_at"] = datetime.utcnow().isoformat()

    # Llenar nulos
    numeric_cols = gold.select_dtypes(include="number").columns
    gold[numeric_cols] = gold[numeric_cols].fillna(0)

    string_cols = gold.select_dtypes(include="object").columns
    gold[string_cols] = gold[string_cols].fillna("Unknown")

    # Conteo de segmentos
    segment_counts = gold["risk_segment"].value_counts().to_dict()

    # ── 6. Guardar ────────────────────────────────────────────────────────
    os.makedirs(os.path.join(gold_dir, "gold_customer_360"), exist_ok=True)
    output_path = os.path.join(gold_dir, "gold_customer_360", "gold_customer_360.parquet")
    gold.to_parquet(output_path, index=False, compression="snappy")

    logger.info("Gold Customer 360 guardado: %d filas, %d columnas en %s",
                len(gold), len(gold.columns), output_path)
    logger.info("Segmentación de riesgo: %s", segment_counts)

    return {
        "rows": len(gold),
        "columns": len(gold.columns),
        "output_path": output_path,
        "risk_segments": segment_counts,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    result = build_gold_customer_360()
    print(f"\nResultado: {result}")
