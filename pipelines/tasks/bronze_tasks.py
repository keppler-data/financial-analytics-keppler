"""
Tareas de ingestión para la capa Bronze — Home Credit Default Risk.

Este módulo se encarga de leer los archivos CSV semilla del dataset de
Home Credit Default Risk (Kaggle) y escribirlos como Parquet particionado
en la capa Bronze del data lakehouse.

Funcionalidades principales:
  - Detección automática de codificación (utf-8, latin-1, cp1252).
  - Enriquecimiento con columnas técnicas: _ingestion_date, _source_file,
    _dataset_name y _row_hash (MD5 para detección de duplicados).
  - Escritura en formato Parquet con compresión Snappy.
  - Registro de conteos de filas mediante el módulo ``logging``.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

CODIFICACIONES_PERMITIDAS: list[str] = ["utf-8", "latin-1", "cp1252"]

# Definición de los 7 datasets de Home Credit con sus archivos CSV asociados.
# Cada entrada contiene:
#   - dataset_name : nombre lógico del dataset (usado como subcarpeta).
#   - filename     : nombre del archivo CSV en el directorio semilla.
DATASETS_HOME_CREDIT: list[dict[str, str]] = [
    {"dataset_name": "application_train",    "filename": "application_train.csv"},
    {"dataset_name": "bureau",               "filename": "bureau.csv"},
    {"dataset_name": "bureau_balance",       "filename": "bureau_balance.csv"},
    {"dataset_name": "previous_application", "filename": "previous_application.csv"},
    {"dataset_name": "installments_payments","filename": "installments_payments.csv"},
    {"dataset_name": "credit_card_balance",  "filename": "credit_card_balance.csv"},
    {"dataset_name": "POS_CASH_balance",     "filename": "POS_CASH_balance.csv"},
]

# Columnas técnicas que se añaden a cada dataset durante la ingestión.
COLUMNA_FECHA_INGESTION = "_ingestion_date"
COLUMNA_ARCHIVO_ORIGEN  = "_source_file"
COLUMNA_NOMBRE_DATASET  = "_dataset_name"
COLUMNA_HASH_FILA       = "_row_hash"


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def _obtener_ruta_seed() -> str:
    """Retorna la ruta base del directorio de datos semilla.

    Lee la variable de entorno ``SEED_DIR``; si no está definida,
    utiliza ``data/seed`` como valor por defecto.
    """
    return os.getenv("SEED_DIR", "data/seed")


def _obtener_ruta_bronze() -> str:
    """Retorna la ruta base del directorio de la capa Bronze.

    Lee la variable de entorno ``BRONZE_DIR``; si no está definida,
    utiliza ``data/bronze`` como valor por defecto.
    """
    return os.getenv("BRONZE_DIR", "data/bronze")


def _leer_csv_con_deteccion_codificacion(ruta_archivo: str) -> pd.DataFrame:
    """Lee un archivo CSV intentando múltiples codificaciones.

    Intenta leer el archivo en orden con las codificaciones definidas en
    ``CODIFICACIONES_PERMITIDAS``. Si ninguna funciona, lanza un
    ``UnicodeDecodeError`` con un mensaje descriptivo.

    Parameters
    ----------
    ruta_archivo: str
        Ruta absoluta o relativa al archivo CSV.

    Returns
    -------
    pd.DataFrame
        DataFrame con el contenido del CSV.

    Raises
    ------
    UnicodeDecodeError
        Si no se logra leer el archivo con ninguna codificación soportada.
    """
    for codificacion in CODIFICACIONES_PERMITIDAS:
        try:
            df = pd.read_csv(ruta_archivo, encoding=codificacion)
            logger.debug(
                "Archivo '%s' leído exitosamente con codificación '%s'.",
                ruta_archivo,
                codificacion,
            )
            return df
        except UnicodeDecodeError:
            logger.debug(
                "Fallo al leer '%s' con codificación '%s'; intentando siguiente.",
                ruta_archivo,
                codificacion,
            )
            continue

    raise UnicodeDecodeError(
        "multi",
        b"",
        0,
        1,
        f"No se pudo decodificar '{ruta_archivo}' con ninguna codificación "
        f"soportada: {CODIFICACIONES_PERMITIDAS}.",
    )


def _calcular_hash_fila(fila: pd.Series) -> str:
    """Calcula un hash MD5 a partir de los valores ordenados de una fila.

    Los valores se ordenan alfabéticamente por nombre de columna antes de
    serializarse, lo que garantiza que el hash sea independiente del orden
    físico de las columnas en el DataFrame.

    Parameters
    ----------
    fila: pd.Series
        Una fila individual de un DataFrame.

    Returns
    -------
    str
        Cadena hexadecimal de 32 caracteres correspondiente al hash MD5.
    """
    valores = fila.sort_index().astype(str).tolist()
    cadena = "|".join(valores)
    return hashlib.md5(cadena.encode("utf-8")).hexdigest()


def _agregar_columnas_tecnicas(
    df: pd.DataFrame,
    nombre_dataset: str,
    nombre_archivo: str,
) -> pd.DataFrame:
    """Añade columnas técnicas de auditoría al DataFrame.

    Columns added:
        - ``_ingestion_date``: marca temporal UTC de la ingestión (ISO 8601).
        - ``_source_file``    : nombre del archivo CSV de origen.
        - ``_dataset_name``   : nombre lógico del dataset.
        - ``_row_hash``       : hash MD5 de la fila (para detección de duplicados).

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame original con los datos del CSV.
    nombre_dataset: str
        Nombre lógico del dataset (ej. ``"application_train"``).
    nombre_archivo: str
        Nombre del archivo CSV de origen (ej. ``"application_train.csv"``).

    Returns
    -------
    pd.DataFrame
        DataFrame enriquecido con las columnas técnicas.
    """
    fecha_ingestion = datetime.now(timezone.utc).isoformat()

    df[COLUMNA_FECHA_INGESTION] = fecha_ingestion
    df[COLUMNA_ARCHIVO_ORIGEN]  = nombre_archivo
    df[COLUMNA_NOMBRE_DATASET]  = nombre_dataset

    # El cálculo del hash se realiza sobre las columnas originales (sin técnicas)
    columnas_originales = [
        c for c in df.columns
        if c not in (COLUMNA_FECHA_INGESTION, COLUMNA_ARCHIVO_ORIGEN,
                      COLUMNA_NOMBRE_DATASET, COLUMNA_HASH_FILA)
    ]
    df[COLUMNA_HASH_FILA] = df[columnas_originales].apply(
        _calcular_hash_fila, axis=1,
    )

    return df


# ---------------------------------------------------------------------------
# Función principal de ingestión por dataset
# ---------------------------------------------------------------------------

def ingest_bronze_dataset(dataset_name: str, filename: str) -> dict[str, Any]:
    """Ingesta un único dataset CSV a la capa Bronze como Parquet.

    Lee el archivo CSV desde el directorio semilla (``SEED_DIR``), lo
    enriquece con columnas técnicas y lo escribe como Parquet con
    compresión Snappy en el subdirectorio correspondiente de la capa
    Bronze (``BRONZE_DIR/<dataset_name>/``).

    Parameters
    ----------
    dataset_name: str
        Nombre lógico del dataset (ej. ``"application_train"``).
        Se utiliza como nombre de subcarpeta en la capa Bronze.
    filename: str
        Nombre del archivo CSV a leer desde el directorio semilla
        (ej. ``"application_train.csv"``).

    Returns
    -------
    dict[str, Any]
        Diccionario con el resultado de la operación:
        ``{"dataset": ..., "rows": ..., "output_path": ...}``.

        Si el archivo no existe, retorna un diccionario con
        ``"rows": 0`` y ``"output_path": ""``.
    """
    resultado: dict[str, Any] = {
        "dataset": dataset_name,
        "rows": 0,
        "output_path": "",
    }

    ruta_seed = _obtener_ruta_seed()
    ruta_bronze = _obtener_ruta_bronze()

    ruta_entrada = os.path.join(ruta_seed, filename)
    directorio_salida = os.path.join(ruta_bronze, dataset_name)
    ruta_salida = os.path.join(directorio_salida, f"{dataset_name}.parquet")

    # ---- Validar existencia del archivo ------------------------------------
    if not os.path.isfile(ruta_entrada):
        logger.warning(
            "Archivo no encontrado: '%s'. Saltando ingestión del dataset '%s'.",
            ruta_entrada,
            dataset_name,
        )
        return resultado

    try:
        # ---- Lectura con detección de codificación -----------------------
        logger.info("Iniciando ingestión Bronze: '%s' desde '%s'.", dataset_name, ruta_entrada)
        df = _leer_csv_con_deteccion_codificacion(ruta_entrada)
        logger.info(
            "Leídas %d filas y %d columnas de '%s'.",
            len(df),
            len(df.columns),
            filename,
        )

        # ---- Enriquecimiento con columnas técnicas ------------------------
        df = _agregar_columnas_tecnicas(df, dataset_name, filename)

        # ---- Escritura como Parquet (Snappy) -------------------------------
        os.makedirs(directorio_salida, exist_ok=True)
        df.to_parquet(ruta_salida, index=False, compression="snappy", engine="pyarrow")

        num_filas = len(df)
        logger.info(
            "Ingestión Bronze completada: '%s' → %d filas escritas en '%s'.",
            dataset_name,
            num_filas,
            ruta_salida,
        )

        resultado["rows"] = num_filas
        resultado["output_path"] = ruta_salida

    except UnicodeDecodeError as exc:
        logger.error(
            "Error de codificación al leer '%s' para el dataset '%s': %s",
            ruta_entrada,
            dataset_name,
            exc,
        )
    except pd.errors.EmptyDataError:
        logger.warning(
            "El archivo '%s' está vacío. No se generó salida para '%s'.",
            ruta_entrada,
            dataset_name,
        )
    except Exception as exc:
        logger.error(
            "Error inesperado durante la ingestión Bronze de '%s': %s",
            dataset_name,
            exc,
            exc_info=True,
        )

    return resultado


# ---------------------------------------------------------------------------
# Función de ingestión masiva
# ---------------------------------------------------------------------------

def ingest_all_bronze() -> list[dict[str, Any]]:
    """Ingesta los 7 datasets de Home Credit a la capa Bronze.

    Itera sobre la lista ``DATASETS_HOME_CREDIT`` y ejecuta
    :func:`ingest_bronze_dataset` para cada uno, recopilando los
    resultados individuales en una lista.

    Returns
    -------
    list[dict[str, Any]]
        Lista de diccionarios, uno por dataset, con la estructura
        ``{"dataset": ..., "rows": ..., "output_path": ...}``.
    """
    logger.info(
        "Iniciando ingestión Bronze masiva para %d datasets de Home Credit.",
        len(DATASETS_HOME_CREDIT),
    )

    resultados: list[dict[str, Any]] = []
    total_filas: int = 0

    for definicion in DATASETS_HOME_CREDIT:
        resultado = ingest_bronze_dataset(
            dataset_name=definicion["dataset_name"],
            filename=definicion["filename"],
        )
        resultados.append(resultado)
        total_filas += resultado["rows"]

    datasets_exitosos = sum(1 for r in resultados if r["rows"] > 0)
    logger.info(
        "Ingestión Bronze masiva finalizada: %d/%d datasets procesados, "
        "%d filas totales escritas.",
        datasets_exitosos,
        len(DATASETS_HOME_CREDIT),
        total_filas,
    )

    return resultados
