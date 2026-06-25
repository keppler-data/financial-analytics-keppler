# -*- coding: utf-8 -*-
"""
Scoring Baseline de Riesgo Crediticio — Financial Risk Platform

Entrena un modelo baseline (Logistic Regression + Random Forest) sobre
la tabla Gold Customer 360 y genera predicciones de riesgo por cliente.
"""

import json
import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Features esperadas para el modelo
MODEL_FEATURES = [
    "AMT_INCOME_TOTAL","AMT_CREDIT","AMT_ANNUITY","AMT_GOODS_PRICE",
    "DAYS_BIRTH","DAYS_EMPLOYED","CNT_CHILDREN","REGION_RATING_CLIENT",
    "EXT_SOURCE_1","EXT_SOURCE_2","EXT_SOURCE_3",
    "total_installments","avg_payment_delay","max_days_overdue",
    "count_late_payments","total_unpaid_amount",
    "avg_payment_delay_3m","avg_payment_delay_6m","avg_payment_delay_12m",
    "missed_payment_count_90d","payment_consistency_score",
    "total_credits","active_credits","total_overdue_debt",
    "max_overdue_days","total_previous_apps","approval_rate",
    "avg_balance","max_dpd",
    "credit_to_income_ratio","annuity_to_income_ratio",
]


def _load_gold_data() -> pd.DataFrame:
    """Carga la tabla Gold Customer 360."""
    gold_dir = os.getenv("GOLD_DIR", "data/gold")
    customer_path = os.path.join(gold_dir, "gold_customer_360")

    if not os.path.exists(customer_path):
        raise FileNotFoundError(f"No se encontró gold_customer_360 en {customer_path}")

    parquet_files = [f for f in os.listdir(customer_path) if f.endswith(".parquet")]
    if not parquet_files:
        raise FileNotFoundError(f"No hay archivos Parquet en {customer_path}")

    df = pd.read_parquet(os.path.join(customer_path, parquet_files[0]))
    logger.info("Gold Customer 360 cargado: %d filas", len(df))
    return df


def _prepare_features(df: pd.DataFrame) -> tuple:
    """
    Prepara features (X) y target (y) para el modelo.

    Returns
    -------
    tuple de (X, y, feature_names_used)
    """
    # Filtrar filas con TARGET nulo
    df = df.dropna(subset=["TARGET"])
    df["TARGET"] = df["TARGET"].astype(int)

    # Seleccionar features disponibles
    available_features = [f for f in MODEL_FEATURES if f in df.columns]
    missing_features = [f for f in MODEL_FEATURES if f not in df.columns]

    if missing_features:
        logger.warning("Features faltantes (se omitirán): %s", missing_features)

    X = df[available_features].copy()
    y = df["TARGET"]

    # Llenar nulos con 0
    X = X.fillna(0)

    # Reemplazar infinitos
    X = X.replace([np.inf, -np.inf], 0)

    logger.info("Features preparadas: %d disponibles de %d esperadas", len(available_features), len(MODEL_FEATURES))
    logger.info("Distribución de TARGET: %s", y.value_counts().to_dict())

    return X, y, available_features


def _get_feature_importance(model, feature_names: list, model_name: str) -> pd.DataFrame:
    """
    Extrae la importancia de features según el tipo de modelo.

    Parameters
    ----------
    model : modelo sklearn entrenado
    feature_names : list de nombres de features
    model_name : str, nombre del modelo ('logistic_regression' o 'random_forest')

    Returns
    -------
    DataFrame con feature_name e importance, ordenado descendente.
    """
    if model_name == "random_forest" and hasattr(model, "feature_importances_"):
        importance = model.feature_importances_
    elif model_name == "logistic_regression" and hasattr(model, "coef_"):
        importance = np.abs(model.coef_[0])
    else:
        importance = np.zeros(len(feature_names))

    return pd.DataFrame({
        "feature": feature_names,
        "importance": importance,
    }).sort_values("importance", ascending=False)


def train_scoring_baseline() -> dict:
    """
    Entrena modelos baseline de scoring crediticio sobre Gold Customer 360.

    Entrena Logistic Regression y Random Forest, selecciona el mejor
    según AUC-ROC, genera predicciones sobre todo el dataset y guarda
    resultados.

    Returns
    -------
    dict con métricas, rutas de archivos generados y resumen del modelo.
    """
    logger.info("=" * 60)
    logger.info("Iniciando entrenamiento de Scoring Baseline")
    logger.info("=" * 60)

    # ── 1. Cargar y preparar datos ────────────────────────────────────────
    df = _load_gold_data()
    df_original = df.copy()  # Guardar para predicciones finales

    X, y, feature_names = _prepare_features(df)

    if len(X) == 0 or len(y) == 0:
        raise ValueError("No hay datos suficientes para entrenar el modelo.")

    # ── 2. Split train/test ───────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info("Split: train=%d, test=%d", len(X_train), len(X_test))

    # ── 3. Entrenar modelos ───────────────────────────────────────────────
    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=42, class_weight="balanced"
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
        ),
    }

    best_model_name = None
    best_auc = 0
    best_model = None
    all_metrics = {}

    for name, model in models.items():
        logger.info("Entrenando %s...", name)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

        auc = roc_auc_score(y_test, y_prob)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred).tolist()

        metrics = {
            "model": name,
            "auc_roc": round(float(auc), 4),
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": cm,
        }
        all_metrics[name] = metrics

        logger.info("  %s — AUC: %.4f | Accuracy: %.4f | F1: %.4f", name, auc, acc, f1)

        if auc > best_auc:
            best_auc = auc
            best_model_name = name
            best_model = model

    logger.info("Mejor modelo: %s (AUC=%.4f)", best_model_name, best_auc)

    # ── 4. Importancia de features ────────────────────────────────────────
    importance_df = _get_feature_importance(best_model, feature_names, best_model_name)
    logger.info("Top 5 features: %s", importance_df.head()["feature"].tolist())

    # ── 5. Generar predicciones sobre TODO el dataset ─────────────────────
    X_full = df_original[feature_names].fillna(0).replace([np.inf, -np.inf], 0)
    df_original["predicted_default_prob"] = best_model.predict_proba(X_full)[:, 1]
    df_original["predicted_default"] = (df_original["predicted_default_prob"] >= 0.5).astype(int)

    # Segmentación de riesgo basada en probabilidad
    def _risk_segment(prob):
        if prob < 0.3:
            return "LOW_RISK"
        elif prob < 0.6:
            return "MEDIUM_RISK"
        return "HIGH_RISK"

    df_original["risk_segment_predicted"] = df_original["predicted_default_prob"].apply(_risk_segment)

    segment_dist = df_original["risk_segment_predicted"].value_counts().to_dict()
    logger.info("Segmentación de riesgo (modelo): %s", segment_dist)

    # ── 6. Guardar outputs ────────────────────────────────────────────────
    base_dir = os.getenv("DATA_DIR", ".")
    ml_dir = os.path.join(base_dir, "ml", "scoring")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(ml_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # Scores por cliente
    scores_path = os.path.join(ml_dir, "customer_risk_scores.parquet")
    df_original.to_parquet(scores_path, index=False, compression="snappy")
    logger.info("Scores guardados: %s (%d filas)", scores_path, len(df_original))

    # Métricas del modelo
    metrics_path = os.path.join(reports_dir, "model_metrics.json")
    metrics_output = {
        "generated_at": datetime.utcnow().isoformat(),
        "best_model": best_model_name,
        "best_auc": round(float(best_auc), 4),
        "models": all_metrics,
        "training_rows": len(X_train),
        "test_rows": len(X_test),
        "features_used": len(feature_names),
        "risk_segmentation": segment_dist,
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_output, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Métricas guardadas: %s", metrics_path)

    # Importancia de features
    importance_path = os.path.join(reports_dir, "model_feature_importance.csv")
    importance_df.to_csv(importance_path, index=False)
    logger.info("Importancia de features guardada: %s", importance_path)

    # Export para Power BI (CSV listo para conectar)
    pbi_path = os.path.join(reports_dir, "gold_customer_360_for_powerbi.csv")
    export_cols = [
        "SK_ID_CURR","TARGET","risk_segment","risk_segment_predicted",
        "predicted_default_prob","AMT_INCOME_TOTAL","AMT_CREDIT",
        "payment_consistency_score","max_days_overdue","age_years",
        "credit_to_income_ratio","total_credits","active_credits",
    ]
    available_export_cols = [c for c in export_cols if c in df_original.columns]
    df_original[available_export_cols].to_csv(pbi_path, index=False)
    logger.info("Export para Power BI: %s", pbi_path)

    return {
        "best_model": best_model_name,
        "best_auc": round(float(best_auc), 4),
        "metrics": all_metrics,
        "scores_path": scores_path,
        "metrics_path": metrics_path,
        "importance_path": importance_path,
        "powerbi_path": pbi_path,
        "risk_segmentation": segment_dist,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    result = train_scoring_baseline()
    print(f"\nMejor modelo: {result['best_model']} (AUC={result['best_auc']})")
    print(f"Segmentación: {result['risk_segmentation']}")
