# -*- coding: utf-8 -*-
"""
Reporte de Calidad de Datos — Financial Risk Platform

Genera reportes HTML y JSON con métricas de calidad por dataset y capa.
"""

import json
import logging
import os
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


def _find_parquet_files(directory: str) -> list[str]:
    """Busca archivos .parquet recursivamente en un directorio."""
    if not os.path.exists(directory):
        return []
    parquet_files = []
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".parquet"):
                parquet_files.append(os.path.join(root, f))
    return parquet_files


def _load_dataset(path: str) -> pd.DataFrame:
    """Carga un dataset Parquet con manejo de errores."""
    try:
        return pd.read_parquet(path)
    except Exception as e:
        logger.error("Error cargando %s: %s", path, e)
        return pd.DataFrame()


def profile_dataset(dataset_path: str, dataset_name: str) -> dict:
    """
    Perfila un dataset individual calculando métricas de calidad.

    Parameters
    ----------
    dataset_path : str
        Ruta al directorio o archivo Parquet del dataset.
    dataset_name : str
        Nombre descriptivo del dataset.

    Returns
    -------
    dict con métricas de perfilado.
    """
    # Determinar si es un archivo o un directorio
    if os.path.isfile(dataset_path):
        files = [dataset_path]
    else:
        files = _find_parquet_files(dataset_path)

    if not files:
        logger.warning("No se encontraron archivos Parquet en %s", dataset_path)
        return {
            "dataset": dataset_name, "layer": "unknown",
            "row_count": 0, "column_count": 0, "total_nulls": 0,
            "total_duplicates": 0, "quality_score": 0.0,
            "null_percentage_by_column": {}, "column_types": {},
            "cardinality_by_column": {}, "error": "No data found"
        }

    # Cargar todos los archivos Parquet del dataset
    dfs = [_load_dataset(f) for f in files]
    df = pd.concat([d for d in dfs if not d.empty], ignore_index=True)

    if df.empty:
        return {
            "dataset": dataset_name, "layer": "unknown",
            "row_count": 0, "column_count": 0, "total_nulls": 0,
            "total_duplicates": 0, "quality_score": 0.0,
            "null_percentage_by_column": {}, "column_types": {},
            "cardinality_by_column": {},
        }

    row_count = len(df)
    col_count = len(df.columns)
    total_cells = row_count * col_count
    total_nulls = int(df.isnull().sum().sum())
    total_duplicates = int(df.duplicated().sum())

    # Porcentaje de nulos por columna
    null_pct = (df.isnull().sum() / row_count * 100).round(2).to_dict()

    # Tipos de columna
    col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # Cardinalidad por columna
    cardinality = {col: int(df[col].nunique()) for col in df.columns}

    # Score de calidad
    quality_score = compute_quality_score({
        "row_count": row_count, "total_nulls": total_nulls,
        "total_cells": total_cells, "total_duplicates": total_duplicates,
        "row_count": row_count,
    })

    logger.info("Perfilado %s: %d filas, %d cols, score=%.1f",
                dataset_name, row_count, col_count, quality_score)

    return {
        "dataset": dataset_name,
        "row_count": row_count,
        "column_count": col_count,
        "total_nulls": total_nulls,
        "total_duplicates": total_duplicates,
        "null_percentage_by_column": null_pct,
        "column_types": col_types,
        "cardinality_by_column": cardinality,
        "quality_score": round(quality_score, 1),
    }


def compute_quality_score(profile: dict) -> float:
    """
    Calcula un score de calidad 0-100 basado en nulos y duplicados.

    Fórmula: 100 - (penalización_nulos) - (penalización_duplicados) + (bonificación_completitud)
    """
    row_count = profile.get("row_count", 0)
    total_cells = profile.get("total_cells", 1)
    total_nulls = profile.get("total_nulls", 0)
    total_duplicates = profile.get("total_duplicates", 0)

    if row_count == 0:
        return 0.0

    null_pct = (total_nulls / total_cells) * 100
    dup_pct = (total_duplicates / row_count) * 100

    null_penalty = null_pct * 0.3  # Máximo 30 puntos de penalización
    dup_penalty = dup_pct * 0.2    # Máximo 20 puntos de penalización

    score = 100.0 - null_penalty - dup_penalty
    return max(0.0, min(100.0, score))


def generate_quality_report() -> dict:
    """
    Genera el reporte de calidad completo para todas las capas.

    Returns
    -------
    dict con reporte completo por capa y dataset.
    """
    base_dir = os.getenv("DATA_DIR", ".")
    report = {"generated_at": datetime.utcnow().isoformat(), "layers": {}}

    layers_config = {
        "bronze": os.path.join(base_dir, "data", "bronze"),
        "silver": os.path.join(base_dir, "data", "silver"),
        "intermediate": os.path.join(base_dir, "data", "intermediate"),
        "gold": os.path.join(base_dir, "data", "gold"),
    }

    for layer_name, layer_path in layers_config.items():
        if not os.path.exists(layer_path):
            logger.warning("Capa %s no encontrada en %s", layer_name, layer_path)
            continue

        datasets = []
        for entry in sorted(os.listdir(layer_path)):
            entry_path = os.path.join(layer_path, entry)
            if os.path.isdir(entry_path):
                profile = profile_dataset(entry_path, entry)
                profile["layer"] = layer_name
                datasets.append(profile)

        report["layers"][layer_name] = datasets

    # Resumen global
    all_scores = []
    for layer_datasets in report["layers"].values():
        for ds in layer_datasets:
            if "quality_score" in ds:
                all_scores.append(ds["quality_score"])

    report["summary"] = {
        "total_datasets": len(all_scores),
        "avg_quality_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "min_quality_score": min(all_scores) if all_scores else 0,
        "max_quality_score": max(all_scores) if all_scores else 0,
    }

    logger.info("Reporte generado: %d datasets, score promedio: %.1f",
                report["summary"]["total_datasets"], report["summary"]["avg_quality_score"])

    return report


def save_report_html(report: dict, output_path: str = None) -> str:
    """
    Genera un reporte HTML autocontenido con métricas de calidad.

    Parameters
    ----------
    report : dict
        Reporte generado por generate_quality_report().
    output_path : str, optional
        Ruta de salida. Por defecto reports/data_quality_report.html.

    Returns
    -------
    str con la ruta del archivo generado.
    """
    if output_path is None:
        output_path = os.path.join(
            os.getenv("DATA_DIR", "."), "reports", "data_quality_report.html"
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    def _score_color(score):
        if score >= 80:
            return "#27ae60"
        elif score >= 50:
            return "#f39c12"
        return "#e74c3c"

    # Construir filas de la tabla
    rows_html = ""
    for layer_name, datasets in report.get("layers", {}).items():
        for ds in datasets:
            score = ds.get("quality_score", 0)
            color = _score_color(score)
            rows_html += f"""
            <tr>
                <td><span class="layer-badge layer-{layer_name}">{layer_name.upper()}</span></td>
                <td>{ds.get('dataset', 'N/A')}</td>
                <td>{ds.get('row_count', 0):,}</td>
                <td>{ds.get('column_count', 0)}</td>
                <td>{ds.get('total_nulls', 0):,}</td>
                <td>{ds.get('total_duplicates', 0):,}</td>
                <td><span class="score-badge" style="background:{color}">{score:.1f}</span></td>
            </tr>"""

    summary = report.get("summary", {})

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Quality Report - Financial Risk Platform</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; color: #f8fafc; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; text-align: center; }}
        .card .value {{ font-size: 2rem; font-weight: 700; }}
        .card .label {{ font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }}
        th {{ background: #334155; padding: 0.75rem 1rem; text-align: left; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #334155; font-size: 0.9rem; }}
        tr:hover {{ background: #334155; }}
        .layer-badge {{ padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }}
        .layer-bronze {{ background: #92400e; color: #fbbf24; }}
        .layer-silver {{ background: #1e3a5f; color: #60a5fa; }}
        .layer-intermediate {{ background: #3b0764; color: #c084fc; }}
        .layer-gold {{ background: #713f12; color: #fcd34d; }}
        .score-badge {{ padding: 0.25rem 0.75rem; border-radius: 20px; color: white; font-weight: 600; font-size: 0.85rem; }}
        .footer {{ margin-top: 2rem; text-align: center; color: #64748b; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Data Quality Report</h1>
        <p class="subtitle">Financial Risk Platform - Caso 5 | Generado: {report.get('generated_at', 'N/A')}</p>

        <div class="cards">
            <div class="card">
                <div class="value">{summary.get('total_datasets', 0)}</div>
                <div class="label">Datasets Evaluados</div>
            </div>
            <div class="card">
                <div class="value" style="color: #60a5fa">{summary.get('avg_quality_score', 0):.1f}</div>
                <div class="label">Score Promedio</div>
            </div>
            <div class="card">
                <div class="value" style="color: #f87171">{summary.get('min_quality_score', 0):.1f}</div>
                <div class="label">Score Mínimo</div>
            </div>
            <div class="card">
                <div class="value" style="color: #4ade80">{summary.get('max_quality_score', 0):.1f}</div>
                <div class="label">Score Máximo</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Capa</th>
                    <th>Dataset</th>
                    <th>Filas</th>
                    <th>Columnas</th>
                    <th>Nulos</th>
                    <th>Duplicados</th>
                    <th>Calidad</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <p class="footer">Financial Risk Data Platform - Keppler | Caso 5: Descontrol Operacional y Riesgo Crediticio</p>
    </div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Reporte HTML guardado en %s", output_path)
    return output_path


def save_report_json(report: dict, output_path: str = None) -> str:
    """
    Guarda el reporte de calidad como JSON.

    Parameters
    ----------
    report : dict
        Reporte generado por generate_quality_report().
    output_path : str, optional
        Ruta de salida. Por defecto reports/data_quality_summary.json.

    Returns
    -------
    str con la ruta del archivo generado.
    """
    if output_path is None:
        output_path = os.path.join(
            os.getenv("DATA_DIR", "."), "reports", "data_quality_summary.json"
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convertir numpy types a nativos de Python para JSON
    def _convert(obj):
        if hasattr(obj, "item"):
            return obj.item()
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_convert(v) for v in obj]
        return obj

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_convert(report), f, indent=2, ensure_ascii=False, default=str)

    logger.info("Reporte JSON guardado en %s", output_path)
    return output_path


def run_quality_checks() -> dict:
    """
    Ejecuta el pipeline completo de calidad: genera reporte, guarda HTML y JSON.

    Returns
    -------
    dict con el reporte completo y las rutas de los archivos generados.
    """
    logger.info("Iniciando checks de calidad de datos...")

    report = generate_quality_report()
    html_path = save_report_html(report)
    json_path = save_report_json(report)

    summary = report.get("summary", {})
    logger.info("Checks completados: %d datasets, score promedio=%.1f",
                summary.get("total_datasets", 0), summary.get("avg_quality_score", 0))

    return {
        "report": report,
        "html_path": html_path,
        "json_path": json_path,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    result = run_quality_checks()
    print(f"\nHTML: {result['html_path']}")
    print(f"JSON: {result['json_path']}")
    print(f"Resumen: {result['report']['summary']}")
