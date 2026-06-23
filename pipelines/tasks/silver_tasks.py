"""
Tareas de transformación hacia la capa Silver.

Este módulo lee archivos Parquet de la capa Bronze y produce archivos Parquet
limpios y estandarizados en la capa Silver para los conjuntos de datos de
Home Credit. Cada dataset se transforma con tipado explícito, eliminación de
duplicados y tratamiento de valores nulos según reglas de negocio.

Funciones principales
---------------------
- transform_to_silver: transforma un único dataset de Bronze a Silver.
- transform_all_silver: transforma todos los datasets soportados.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from pandas.api.types import is_numeric_dtype

# ---------------------------------------------------------------------------
# Configuración de rutas mediante variables de entorno
# ---------------------------------------------------------------------------
BRONZE_DIR: str = os.getenv("BRONZE_DIR", "data/bronze")
SILVER_DIR: str = os.getenv("SILVER_DIR", "data/silver")

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Catálogos de columnas por dataset
# ---------------------------------------------------------------------------

# --- application_train -----------------------------------------------------

_APPLICATION_TRAIN_INT_COLS: List[str] = [
    "SK_ID_CURR",
    "TARGET",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
    "CNT_FAM_MEMBERS",
    "OWN_CAR_AGE",
]

_APPLICATION_TRAIN_STR_COLS: List[str] = [
    "NAME_CONTRACT_TYPE",
    "CODE_GENDER",
    "NAME_TYPE_SUITE",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE",
    "WEEKDAY_APPR_PROCESS_START",
    "ORGANIZATION_TYPE",
]

_APPLICATION_TRAIN_FLOAT_COLS: List[str] = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "REGION_POPULATION_RELATIVE",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
]

# Columnas normalizadas de APARTMENTS_…, …_AVG, …_MEDI, …_MODE
# Se detectan dinámicamente, pero se incluye una lista base de sufijos
_NORMALIZED_SUFFIXES: List[str] = ["AVG", "MEDI", "MODE"]

# --- bureau -----------------------------------------------------------------

_BUREAU_INT_COLS: List[str] = [
    "SK_ID_CURR",
    "SK_ID_BUREAU",
]

_BUREAU_STR_COLS: List[str] = [
    "CREDIT_ACTIVE",
    "CREDIT_CURRENCY",
    "CREDIT_TYPE",
]

_BUREAU_FLOAT_COLS: List[str] = [
    "DAYS_CREDIT",
    "CREDIT_DAY_OVERDUE",
    "DAYS_CREDIT_ENDDATE",
    "AMT_CREDIT_MAX_OVERDUE",
    "CNT_CREDIT_PROLONGATIONS",
    "AMT_CREDIT_SUM",
    "AMT_CREDIT_SUM_DEBT",
    "AMT_CREDIT_SUM_LIMIT",
    "AMT_CREDIT_SUM_OVERDUE",
    "DAYS_ENDDATE_FACT",
]

# --- bureau_balance ---------------------------------------------------------

_BUREAU_BALANCE_INT_COLS: List[str] = [
    "SK_ID_BUREAU",
    "MONTHS_BALANCE",
]

_BUREAU_BALANCE_STR_COLS: List[str] = [
    "STATUS",
]

# --- previous_application ---------------------------------------------------

_PREV_APP_INT_COLS: List[str] = [
    "SK_ID_PREV",
    "SK_ID_CURR",
    "NFLAG_LAST_APPL_IN_DAY",
    "NFLAG_INSURED_ON_APPROVAL",
]

_PREV_APP_STR_COLS: List[str] = [
    "NAME_CONTRACT_TYPE",
    "NAME_CONTRACT_STATUS",
    "NAME_TYPE_SUITE",
    "NAME_CLIENT_TYPE",
    "NAME_GOODS_CATEGORY",
    "NAME_PORTFOLIO",
    "NAME_PRODUCT_TYPE",
    "CHANNEL_TYPE",
    "NAME_SELLER_INDUSTRY",
    "NAME_YIELD_GROUP",
    "PRODUCT_COMBINATION",
]

_PREV_APP_FLOAT_COLS: List[str] = [
    "AMT_ANNUITY",
    "AMT_APPLICATION",
    "AMT_CREDIT",
    "AMT_DOWN_PAYMENT",
    "AMT_GOODS_PRICE",
    "RATE_DOWN_PAYMENT",
    "RATE_INTEREST_PRIMARY",
    "RATE_INTEREST_PRIVILEGED",
    "DAYS_DECISION",
    "SELLERPLACE_AREA",
    "CNT_PAYMENT",
]

# --- installments_payments --------------------------------------------------

_INSTALL_INT_COLS: List[str] = [
    "SK_ID_PREV",
    "SK_ID_CURR",
    "NUM_INSTALMENT_NUMBER",
    "NUM_INSTALMENT_VERSION",
]

_INSTALL_FLOAT_COLS: List[str] = [
    "DAYS_INSTALMENT",
    "DAYS_ENTRY_PAYMENT",
    "AMT_INSTALMENT",
    "AMT_PAYMENT",
]

# --- credit_card_balance ----------------------------------------------------

_CCB_INT_COLS: List[str] = [
    "SK_ID_PREV",
    "SK_ID_CURR",
    "MONTHS_BALANCE",
    "CNT_DRAWINGS_ATM_CURRENT",
    "CNT_DRAWINGS_CURRENT",
    "CNT_DRAWINGS_OTHER_CURRENT",
    "CNT_DRAWINGS_POS_CURRENT",
    "CNT_INSTALMENT_MATURE_CUM",
    "SK_DPD",
    "SK_DPD_DEF",
]

_CCB_FLOAT_COLS: List[str] = [
    "AMT_DRAWINGS_ATM_CURRENT",
    "AMT_DRAWINGS_CURRENT",
    "AMT_DRAWINGS_OTHER_CURRENT",
    "AMT_DRAWINGS_POS_CURRENT",
    "AMT_INST_MIN_REGULARITY",
    "AMT_PAYMENT_CURRENT",
    "AMT_PAYMENT_TOTAL_CURRENT",
    "AMT_RECEIVABLE_PRINCIPAL",
    "AMT_RECIVABLES",
    "AMT_TOTAL_RECEIVABLE",
]

# --- POS_CASH_balance -------------------------------------------------------

_POSH_INT_COLS: List[str] = [
    "SK_ID_PREV",
    "SK_ID_CURR",
    "MONTHS_BALANCE",
    "CNT_INSTALMENT",
    "CNT_INSTALMENT_FUTURE",
    "SK_DPD",
    "SK_DPD_DEF",
]

_POSH_STR_COLS: List[str] = [
    "NAME_CONTRACT_STATUS",
]

# ---------------------------------------------------------------------------
# Registro (registry) de datasets
# ---------------------------------------------------------------------------

_DATASET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "application_train": {
        "int_cols": _APPLICATION_TRAIN_INT_COLS,
        "str_cols": _APPLICATION_TRAIN_STR_COLS,
        "float_cols": _APPLICATION_TRAIN_FLOAT_COLS,
        "dedup_cols": ["SK_ID_CURR"],
        "has_normalized_cols": True,
    },
    "bureau": {
        "int_cols": _BUREAU_INT_COLS,
        "str_cols": _BUREAU_STR_COLS,
        "float_cols": _BUREAU_FLOAT_COLS,
        "dedup_cols": ["SK_ID_BUREAU"],
    },
    "bureau_balance": {
        "int_cols": _BUREAU_BALANCE_INT_COLS,
        "str_cols": _BUREAU_BALANCE_STR_COLS,
        "float_cols": [],
        "dedup_cols": ["SK_ID_BUREAU", "MONTHS_BALANCE"],
    },
    "previous_application": {
        "int_cols": _PREV_APP_INT_COLS,
        "str_cols": _PREV_APP_STR_COLS,
        "float_cols": _PREV_APP_FLOAT_COLS,
        "dedup_cols": ["SK_ID_PREV"],
    },
    "installments_payments": {
        "int_cols": _INSTALL_INT_COLS,
        "str_cols": [],
        "float_cols": _INSTALL_FLOAT_COLS,
        "dedup_cols": ["SK_ID_PREV", "NUM_INSTALMENT_NUMBER"],
    },
    "credit_card_balance": {
        "int_cols": _CCB_INT_COLS,
        "str_cols": [],
        "float_cols": _CCB_FLOAT_COLS,
        "dedup_cols": ["SK_ID_PREV", "MONTHS_BALANCE"],
    },
    "POS_CASH_balance": {
        "int_cols": _POSH_INT_COLS,
        "str_cols": _POSH_STR_COLS,
        "float_cols": [],
        "dedup_cols": ["SK_ID_PREV", "MONTHS_BALANCE"],
    },
}


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def _leer_bronze(dataset_name: str) -> Optional[pd.DataFrame]:
    """Lee todos los archivos Parquet de la capa Bronze para un dataset.

    Busca recursivamente dentro de ``BRONZE_DIR/<dataset_name>/`` todos los
    archivos ``*.parquet`` y los concatena en un único DataFrame.

    Parameters
    ----------
    dataset_name : str
        Nombre del dataset (por ejemplo ``"application_train"``).

    Returns
    -------
    pd.DataFrame | None
        DataFrame con los datos leídos o ``None`` si no se encuentra ningún
        archivo.
    """
    base_path = os.path.join(BRONZE_DIR, dataset_name)
    if not os.path.isdir(base_path):
        logger.warning(
            "Directorio Bronze no encontrado para '%s': %s", dataset_name, base_path
        )
        return None

    parquet_files: List[str] = []
    for root, _dirs, files in os.walk(base_path):
        for fname in files:
            if fname.endswith(".parquet"):
                parquet_files.append(os.path.join(root, fname))

    if not parquet_files:
        logger.warning(
            "No se encontraron archivos Parquet para '%s' en %s",
            dataset_name,
            base_path,
        )
        return None

    logger.info(
        "Leyendo %d archivo(s) Parquet de Bronze para '%s'",
        len(parquet_files),
        dataset_name,
    )
    frames: List[pd.DataFrame] = []
    for fpath in sorted(parquet_files):
        try:
            df = pd.read_parquet(fpath)
            frames.append(df)
        except Exception as exc:
            logger.error("Error leyendo %s: %s", fpath, exc)

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)
    logger.info(
        "'%s': %d filas leídas en total desde Bronze", dataset_name, len(combined)
    )
    return combined


def _escribir_silver(df: pd.DataFrame, dataset_name: str) -> str:
    """Escribe el DataFrame transformado a la capa Silver en formato Parquet.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame limpio y tipado.
    dataset_name : str
        Nombre del dataset.

    Returns
    -------
    str
        Ruta del directorio de salida.
    """
    output_dir = os.path.join(SILVER_DIR, dataset_name)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{dataset_name}.parquet")
    df.to_parquet(output_path, index=False, compression="snappy")
    logger.info(
        "'%s': %d filas escritas en %s", dataset_name, len(df), output_path
    )
    return output_dir


def _cast_columns(
    df: pd.DataFrame,
    *,
    int_cols: Optional[List[str]] = None,
    str_cols: Optional[List[str]] = None,
    float_cols: Optional[List[str]] = None,
    extra_float_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Convierte las columnas al tipo especificado cuando están presentes.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame de entrada.
    int_cols : list[str] | None
        Columnas a convertir a ``Int64`` (entero nullable de pandas).
    str_cols : list[str] | None
        Columnas a convertir a ``string``.
    float_cols : list[str] | None
        Columnas a convertir a ``float64``.
    extra_float_cols : list[str] | None
        Columnas adicionales a convertir a ``float64`` (útil para columnas
        detectadas dinámicamente como las normalizadas).

    Returns
    -------
    pd.DataFrame
        DataFrame con los tipos convertidos.
    """
    int_cols = int_cols or []
    str_cols = str_cols or []
    float_cols = float_cols or []
    extra_float_cols = extra_float_cols or []

    # Enteros — usar Int64 para soportar nulos
    for col in int_cols:
        if col in df.columns:
            try:
                df[col] = df[col].astype("Int64")
            except (ValueError, TypeError) as exc:
                logger.warning("No se pudo convertir '%s' a Int64: %s", col, exc)

    # Cadenas
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype("string")

    # Flotantes (incluyendo columnas extra)
    all_float = float_cols + extra_float_cols
    for col in all_float:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
            except (ValueError, TypeError) as exc:
                logger.warning("No se pudo convertir '%s' a float64: %s", col, exc)

    return df


def _detectar_columnas_normalizadas(df: pd.DataFrame) -> List[str]:
    """Detecta columnas normalizadas (sufijos AVG, MEDI, MODE).

    En el dataset ``application_train`` existen muchas columnas del estilo
    ``APARTMENTS_AVG``, ``APARTMENTS_MEDI``, ``BASEMENTAREA_MODE``, etc.
    Esta función las identifica por sufijo para poder castearlas a ``float64``.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame de ``application_train``.

    Returns
    -------
    list[str]
        Lista de columnas que terminan en alguno de los sufijos normalizados.
    """
    normalized: List[str] = []
    for col in df.columns:
        upper = col.upper()
        if any(upper.endswith(f"_{sfx}") for sfx in _NORMALIZED_SUFFIXES):
            normalized.append(col)
    return normalized


# ---------------------------------------------------------------------------
# Funciones de transformación específicas por dataset
# ---------------------------------------------------------------------------

def _transform_application_train(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma el dataset ``application_train`` a la capa Silver.

    Aplica:
    - Tipado explícito (enteros, cadenas, flotantes).
    - Detección y casteo de columnas normalizadas (AVG/MEDI/MODE).
    - Eliminación de duplicados por ``SK_ID_CURR``.
    - Corrección de anomalías: ``DAYS_EMPLOYED == 365243`` → nulo.
    - Imputación de valores nulos críticos.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame crudo leído de Bronze.

    Returns
    -------
    pd.DataFrame
        DataFrame limpio y tipado.
    """
    # Detectar columnas normalizadas que no estén ya en el catálogo
    extra_float = _detectar_columnas_normalizadas(df)
    # Excluir las que ya están en float_cols para evitar trabajo duplicado
    existing_float = set(_APPLICATION_TRAIN_FLOAT_COLS)
    extra_float = [c for c in extra_float if c not in existing_float]

    df = _cast_columns(
        df,
        int_cols=_APPLICATION_TRAIN_INT_COLS,
        str_cols=_APPLICATION_TRAIN_STR_COLS,
        float_cols=_APPLICATION_TRAIN_FLOAT_COLS,
        extra_float_cols=extra_float,
    )

    # Corregir anomalía: DAYS_EMPLOYED == 365243 es un valor centinela
    if "DAYS_EMPLOYED" in df.columns:
        anomalias = (df["DAYS_EMPLOYED"] == 365243).sum()
        if anomalias > 0:
            logger.info(
                "Corrigiendo %d valores anómalos en DAYS_EMPLOYED (365243 → nulo)",
                anomalias,
            )
            df["DAYS_EMPLOYED"] = df["DAYS_EMPLOYED"].replace(365243, None)

    # Imputación de valores nulos críticos
    nulls_filled = 0
    fill_map: Dict[str, Any] = {
        "NAME_TYPE_SUITE": "Unaccompanied",
        "OCCUPATION_TYPE": "Unknown",
        "NAME_FAMILY_STATUS": "Unknown",
    }
    for col, fill_value in fill_map.items():
        if col in df.columns:
            before = df[col].isna().sum()
            if before > 0:
                df[col] = df[col].fillna(fill_value)
                nulls_filled += int(before)
                logger.info(
                    "'%s': se imputaron %d valores nulos con '%s'",
                    col,
                    before,
                    fill_value,
                )

    # Registrar totales de nulos imputados para el reporte
    df.attrs["nulls_filled"] = nulls_filled

    return df


def _transform_generic(
    df: pd.DataFrame, config: Dict[str, Any]
) -> pd.DataFrame:
    """Transforma un dataset genérico usando la configuración del registro.

    Aplica casteo de tipos según las listas de columnas definidas en el
    registro del dataset.  No realiza imputación ni corrección de anomalías
    (esas se manejan en funciones específicas como
    ``_transform_application_train``).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame crudo leído de Bronze.
    config : dict
        Configuración del dataset desde ``_DATASET_REGISTRY``.

    Returns
    -------
    pd.DataFrame
        DataFrame tipado.
    """
    df = _cast_columns(
        df,
        int_cols=config.get("int_cols", []),
        str_cols=config.get("str_cols", []),
        float_cols=config.get("float_cols", []),
    )
    return df


# ---------------------------------------------------------------------------
# Funciones públicas
# ---------------------------------------------------------------------------


def transform_to_silver(dataset_name: str) -> Dict[str, Any]:
    """Transforma un dataset individual de la capa Bronze a la capa Silver.

    Lee todos los archivos Parquet de ``BRONZE_DIR/<dataset_name>/``, aplica
    las reglas de limpieza, tipado y des-duplicación correspondientes, y
    escribe el resultado en ``SILVER_DIR/<dataset_name>/``.

    Parameters
    ----------
    dataset_name : str
        Nombre del dataset a transformar.  Debe estar registrado en
        ``_DATASET_REGISTRY``.

    Returns
    -------
    dict
        Diccionario con estadísticas de la transformación:
        ``dataset``, ``rows_in``, ``rows_out``, ``duplicates_removed``,
        ``nulls_filled``, ``output_path``.

    Raises
    ------
    ValueError
        Si ``dataset_name`` no está registrado en el catálogo.
    """
    if dataset_name not in _DATASET_REGISTRY:
        raise ValueError(
            f"Dataset '{dataset_name}' no registrado. "
            f"Datasets disponibles: {list(_DATASET_REGISTRY.keys())}"
        )

    config = _DATASET_REGISTRY[dataset_name]
    logger.info("=== Iniciando transformación Silver: %s ===", dataset_name)

    # --- Lectura ---
    df = _leer_bronze(dataset_name)
    if df is None:
        logger.warning(
            "No se encontraron datos Bronze para '%s'. Se omite la transformación.",
            dataset_name,
        )
        return {
            "dataset": dataset_name,
            "rows_in": 0,
            "rows_out": 0,
            "duplicates_removed": 0,
            "nulls_filled": 0,
            "output_path": None,
        }

    rows_in: int = len(df)
    logger.info("'%s': %d filas leídas desde Bronze", dataset_name, rows_in)

    # --- Transformación específica o genérica ---
    if dataset_name == "application_train":
        df = _transform_application_train(df)
    else:
        df = _transform_generic(df, config)

    # --- Eliminación de duplicados ---
    dedup_cols: List[str] = config["dedup_cols"]
    # Solo considerar columnas que existan en el DataFrame
    dedup_cols_present = [c for c in dedup_cols if c in df.columns]
    if dedup_cols_present:
        before_dedup = len(df)
        df = df.drop_duplicates(subset=dedup_cols_present, keep="first")
        duplicates_removed: int = before_dedup - len(df)
    else:
        duplicates_removed = 0
        logger.warning(
            "'%s': no se encontraron columnas de des-duplicación %s",
            dataset_name,
            dedup_cols,
        )

    rows_out: int = len(df)

    # --- Recuperar nulos imputados (solo application_train lo registra) ---
    nulls_filled: int = int(df.attrs.get("nulls_filled", 0))

    # --- Escritura ---
    output_path = _escribir_silver(df, dataset_name)

    # --- Registro de estadísticas ---
    stats = {
        "dataset": dataset_name,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "duplicates_removed": duplicates_removed,
        "nulls_filled": nulls_filled,
        "output_path": output_path,
    }

    logger.info(
        "'%s' — Filas entrada: %d | Filas salida: %d | "
        "Duplicados eliminados: %d | Nulos imputados: %d",
        dataset_name,
        rows_in,
        rows_out,
        duplicates_removed,
        nulls_filled,
    )
    logger.info("=== Transformación Silver completada: %s ===", dataset_name)

    return stats


def transform_all_silver() -> List[Dict[str, Any]]:
    """Ejecuta la transformación a Silver para todos los datasets registrados.

    Itera sobre cada dataset en ``_DATASET_REGISTRY``, invoca
    ``transform_to_silver`` y recopila las estadísticas.

    Returns
    -------
    list[dict]
        Lista de diccionarios con las estadísticas de cada transformación.
    """
    logger.info("======= INICIO: transformación batch a capa Silver =======")
    results: List[Dict[str, Any]] = []

    for dataset_name in _DATASET_REGISTRY:
        try:
            stats = transform_to_silver(dataset_name)
            results.append(stats)
        except Exception as exc:
            logger.error("Error transformando '%s': %s", dataset_name, exc, exc_info=True)
            results.append({
                "dataset": dataset_name,
                "rows_in": 0,
                "rows_out": 0,
                "duplicates_removed": 0,
                "nulls_filled": 0,
                "output_path": None,
                "error": str(exc),
            })

    # Resumen general
    total_in = sum(r.get("rows_in", 0) for r in results)
    total_out = sum(r.get("rows_out", 0) for r in results)
    total_dups = sum(r.get("duplicates_removed", 0) for r in results)
    total_nulls = sum(r.get("nulls_filled", 0) for r in results)

    logger.info(
        "======= FIN: transformación batch Silver =======\n"
        "  Datasets procesados: %d\n"
        "  Total filas entrada:  %d\n"
        "  Total filas salida:   %d\n"
        "  Duplicados eliminados: %d\n"
        "  Nulos imputados:      %d",
        len(results),
        total_in,
        total_out,
        total_dups,
        total_nulls,
    )

    return results
