# -*- coding: utf-8 -*-
"""
Prometheus Metrics Exporter — Financial Risk Platform (Caso 5)

Expone métricas de calidad de datos y del modelo ML como endpoints
Prometheus (/metrics) para que Grafana las consuma.

Este exporter puede ejecutarse de dos formas:
1. Standalone:  python -m quality.metrics_exporter
2. En Docker:   Como contenedor en docker-compose (recomendado para prod)

Lee los archivos JSON generados por el pipeline:
  - reports/data_quality_summary.json  → Métricas de calidad por capa/dataset
  - reports/model_metrics.json         → Métricas del modelo ML
"""

import json
import logging
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
EXPORTER_PORT = int(os.getenv("METRICS_EXPORTER_PORT", "8000"))
DATA_DIR = os.getenv("DATA_DIR", ".")
QUALITY_JSON_PATH = os.path.join(DATA_DIR, "reports", "data_quality_summary.json")
MODEL_JSON_PATH = os.path.join(DATA_DIR, "reports", "model_metrics.json")
POLL_INTERVAL_SECONDS = int(os.getenv("METRICS_POLL_INTERVAL", "30"))


# ============================================================================
# CACHÉ DE MÉTRICAS
# ============================================================================
_cached_quality_report = None
_cached_model_metrics = None
_last_load_time = 0


def _load_json_safe(path: str) -> dict | None:
    """Carga un archivo JSON de forma segura, retornando None si no existe."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("No se pudo cargar %s: %s", path, e)
        return None


def refresh_metrics_cache():
    """Recarga los JSON de calidad y modelo si han cambiado o si es la primera vez."""
    global _cached_quality_report, _cached_model_metrics, _last_load_time

    now = time.time()
    if now - _last_load_time < POLL_INTERVAL_SECONDS:
        return

    _cached_quality_report = _load_json_safe(QUALITY_JSON_PATH)
    _cached_model_metrics = _load_json_safe(MODEL_JSON_PATH)
    _last_load_time = now

    if _cached_quality_report:
        logger.debug("Quality metrics cache actualizado (%s)", QUALITY_JSON_PATH)
    if _cached_model_metrics:
        logger.debug("Model metrics cache actualizado (%s)", MODEL_JSON_PATH)


# ============================================================================
# GENERACIÓN DE LÍNEAS PROMETHEUS
# ============================================================================

def _prometheus_line(metric: str, value: float | int, labels: dict | None = None) -> str:
    """Genera una línea en formato Prometheus exposition format."""
    label_str = ""
    if labels:
        pairs = [f'{k}="{v}"' for k, v in labels.items()]
        label_str = "{" + ",".join(pairs) + "}"
    return f"{metric}{label_str} {value}"


def generate_quality_metrics() -> list[str]:
    """
    Genera métricas Prometheus de calidad de datos a partir del reporte JSON.

    Métricas generadas:
    - financial_data_quality_score{layer, dataset} — Score 0-100 por dataset
    - financial_data_quality_avg{layer}            — Score promedio por capa
    - financial_data_rows{layer, dataset}           — Total de filas
    - financial_data_nulls{layer, dataset}          — Total de nulos
    - financial_data_duplicates{layer, dataset}     — Total de duplicados
    - financial_data_columns{layer, dataset}        — Total de columnas
    """
    lines = [
        "# HELP financial_data_quality_score Score de calidad 0-100 por dataset y capa",
        "# TYPE financial_data_quality_score gauge",
        "# HELP financial_data_quality_avg Score de calidad promedio por capa",
        "# TYPE financial_data_quality_avg gauge",
        "# HELP financial_data_rows Total de filas por dataset",
        "# TYPE financial_data_rows gauge",
        "# HELP financial_data_nulls Total de valores nulos por dataset",
        "# TYPE financial_data_nulls gauge",
        "# HELP financial_data_duplicates Total de filas duplicadas por dataset",
        "# TYPE financial_data_duplicates gauge",
        "# HELP financial_data_columns Total de columnas por dataset",
        "# TYPE financial_data_columns gauge",
    ]

    if not _cached_quality_report:
        return lines

    layer_scores = {}  # layer -> list of scores

    for layer_name, datasets in _cached_quality_report.get("layers", {}).items():
        scores_in_layer = []
        for ds in datasets:
            ds_name = ds.get("dataset", "unknown")
            layer = ds.get("layer", layer_name)
            score = ds.get("quality_score", 0)
            rows = ds.get("row_count", 0)
            nulls = ds.get("total_nulls", 0)
            dups = ds.get("total_duplicates", 0)
            cols = ds.get("column_count", 0)

            lines.append(_prometheus_line("financial_data_quality_score", score, {"layer": layer, "dataset": ds_name}))
            lines.append(_prometheus_line("financial_data_rows", rows, {"layer": layer, "dataset": ds_name}))
            lines.append(_prometheus_line("financial_data_nulls", nulls, {"layer": layer, "dataset": ds_name}))
            lines.append(_prometheus_line("financial_data_duplicates", dups, {"layer": layer, "dataset": ds_name}))
            lines.append(_prometheus_line("financial_data_columns", cols, {"layer": layer, "dataset": ds_name}))

            scores_in_layer.append(score)

        if scores_in_layer:
            layer_scores[layer_name] = scores_in_layer

    # Promedios por capa
    for layer_name, scores in layer_scores.items():
        avg_score = round(sum(scores) / len(scores), 1)
        lines.append(_prometheus_line("financial_data_quality_avg", avg_score, {"layer": layer_name}))

    return lines


def generate_model_metrics() -> list[str]:
    """
    Genera métricas Prometheus del modelo ML a partir del reporte JSON.

    Métricas generadas:
    - financial_model_auc{model}         — AUC-ROC por modelo
    - financial_model_accuracy{model}    — Accuracy por modelo
    - financial_model_precision{model}   — Precision por modelo
    - financial_model_recall{model}      — Recall por modelo
    - financial_model_f1{model}          — F1 Score por modelo
    - financial_model_best_auc           — AUC del mejor modelo
    - financial_model_features_used      — Cantidad de features usadas
    - financial_model_training_rows      — Filas de entrenamiento
    - financial_model_test_rows          — Filas de test
    - financial_risk_segment_total{segment} — Total clientes por segmento de riesgo
    """
    lines = [
        "# HELP financial_model_auc AUC-ROC del modelo por tipo",
        "# TYPE financial_model_auc gauge",
        "# HELP financial_model_accuracy Accuracy del modelo por tipo",
        "# TYPE financial_model_accuracy gauge",
        "# HELP financial_model_precision Precision del modelo por tipo",
        "# TYPE financial_model_precision gauge",
        "# HELP financial_model_recall Recall del modelo por tipo",
        "# TYPE financial_model_recall gauge",
        "# HELP financial_model_f1 F1 Score del modelo por tipo",
        "# TYPE financial_model_f1 gauge",
        "# HELP financial_model_best_auc AUC del mejor modelo seleccionado",
        "# TYPE financial_model_best_auc gauge",
        "# HELP financial_model_features_used Cantidad de features utilizadas",
        "# TYPE financial_model_features_used gauge",
        "# HELP financial_model_training_rows Filas usadas para entrenamiento",
        "# TYPE financial_model_training_rows gauge",
        "# HELP financial_model_test_rows Filas usadas para test",
        "# TYPE financial_model_test_rows gauge",
        "# HELP financial_risk_segment_total Total de clientes por segmento de riesgo",
        "# TYPE financial_risk_segment_total gauge",
    ]

    if not _cached_model_metrics:
        return lines

    # Métricas por modelo
    for model_name, metrics in _cached_model_metrics.get("models", {}).items():
        lines.append(_prometheus_line("financial_model_auc", metrics.get("auc_roc", 0), {"model": model_name}))
        lines.append(_prometheus_line("financial_model_accuracy", metrics.get("accuracy", 0), {"model": model_name}))
        lines.append(_prometheus_line("financial_model_precision", metrics.get("precision", 0), {"model": model_name}))
        lines.append(_prometheus_line("financial_model_recall", metrics.get("recall", 0), {"model": model_name}))
        lines.append(_prometheus_line("financial_model_f1", metrics.get("f1_score", 0), {"model": model_name}))

    # Métricas globales del modelo
    lines.append(_prometheus_line("financial_model_best_auc", _cached_model_metrics.get("best_auc", 0)))
    lines.append(_prometheus_line("financial_model_features_used", _cached_model_metrics.get("features_used", 0)))
    lines.append(_prometheus_line("financial_model_training_rows", _cached_model_metrics.get("training_rows", 0)))
    lines.append(_prometheus_line("financial_model_test_rows", _cached_model_metrics.get("test_rows", 0)))

    # Segmentación de riesgo
    for segment, count in _cached_model_metrics.get("risk_segmentation", {}).items():
        lines.append(_prometheus_line("financial_risk_segment_total", count, {"segment": segment}))

    return lines


def generate_pipeline_info() -> list[str]:
    """Genera métricas informativas sobre el estado del pipeline."""
    lines = [
        "# HELP financial_pipeline_last_run Timestamp Unix del último run del pipeline",
        "# TYPE financial_pipeline_last_run gauge",
        "# HELP financial_pipeline_status Estado del último run (1=exitoso, 0=fallido)",
        "# TYPE financial_pipeline_status gauge",
    ]

    now = int(time.time())
    quality_ok = 1 if _cached_quality_report else 0
    model_ok = 1 if _cached_model_metrics else 0

    lines.append(_prometheus_line("financial_pipeline_last_run", now))
    lines.append(_prometheus_line("financial_pipeline_status", 1 if (quality_ok or model_ok) else 0))

    return lines


# ============================================================================
# SERVIDOR HTTP
# ============================================================================

class MetricsHandler(BaseHTTPRequestHandler):
    """Handler HTTP que expone el endpoint /metrics en formato Prometheus."""

    def do_GET(self):
        if self.path == "/metrics":
            refresh_metrics_cache()

            all_lines = []
            all_lines.extend(generate_pipeline_info())
            all_lines.extend(generate_quality_metrics())
            all_lines.extend(generate_model_metrics())

            body = "\n".join(all_lines) + "\n"

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Silencia los logs de cada request para no saturar."""
        logger.debug("Metrics request: %s", args[0] if args else format)


def start_exporter(host: str = "0.0.0.0", port: int = EXPORTER_PORT):
    """
    Inicia el servidor HTTP del exporter de métricas.

    Parameters
    ----------
    host : str
        Host de escucha. Por defecto 0.0.0.0 (todas las interfaces).
    port : int
        Puerto de escucha. Por defecto 8000 o METRICS_EXPORTER_PORT env var.
    """
    server = HTTPServer((host, port), MetricsHandler)
    logger.info("=" * 60)
    logger.info("Financial Risk Metrics Exporter — Caso 5")
    logger.info("=" * 60)
    logger.info("Escuchando en http://%s:%d/metrics", host, port)
    logger.info("Health check: http://%s:%d/health", host, port)
    logger.info("Quality JSON: %s", QUALITY_JSON_PATH)
    logger.info("Model JSON:   %s", MODEL_JSON_PATH)
    logger.info("Poll interval: %d seconds", POLL_INTERVAL_SECONDS)
    logger.info("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Exporter detenido por el usuario.")
        server.server_close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    start_exporter()
