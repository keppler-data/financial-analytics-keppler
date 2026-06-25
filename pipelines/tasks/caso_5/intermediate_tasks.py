"""
Módulo de agregaciones intermedias para análisis de riesgo financiero.

Este módulo lee datos de la capa Silver (Parquet limpio) y produce tablas
de características agregadas en la capa Intermediate, optimizadas para
modelos de riesgo de crédito.

Datasets generados:
- agg_customer_installment_history: Historial agregado de cuotas por cliente
- fct_customer_payment_behavior_features: Comportamiento de pago temporal
- agg_customer_bureau_history: Historial de buró de crédito por cliente
- agg_previous_application_history: Historial de solicitudes previas
- agg_credit_card_behavior: Comportamiento de tarjeta de crédito
- agg_pos_cash_behavior: Comportamiento de POS CASH
"""

import os
import logging
from typing import Optional

import pandas as pd

# Configuración de rutas desde variables de entorno
SILVER_DIR = os.getenv("SILVER_DIR", "data/silver")
INTERMEDIATE_DIR = os.getenv("INTERMEDIATE_DIR", "data/intermediate")

# Configuración de logging
logger = logging.getLogger(__name__)


def _cargar_parquet_silver(nombre_archivo: str) -> Optional[pd.DataFrame]:
    """
    Carga un archivo Parquet desde el directorio Silver.

    Parameters
    ----------
    nombre_archivo : str
        Nombre del archivo Parquet (con o sin extensión .parquet).

    Returns
    -------
    pd.DataFrame or None
        DataFrame con los datos cargados, o None si el archivo no existe
        o está vacío.
    """
    ruta = os.path.join(SILVER_DIR, nombre_archivo)
    if not ruta.endswith(".parquet"):
        ruta += ".parquet"

    if not os.path.exists(ruta):
        logger.warning("Archivo Silver no encontrado: %s", ruta)
        return None

    try:
        df = pd.read_parquet(ruta)
        if df.empty:
            logger.warning("Archivo Silver vacío: %s", ruta)
            return None
        logger.info("Cargados %d registros desde %s", len(df), ruta)
        return df
    except Exception as e:
        logger.error("Error al leer %s: %s", ruta, e)
        return None


def _guardar_intermediate(df: pd.DataFrame, nombre_dataset: str) -> str:
    """
    Guarda un DataFrame como Parquet en el directorio Intermediate.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame a guardar.
    nombre_dataset : str
        Nombre del subdirectorio dentro de Intermediate.

    Returns
    -------
    str
        Ruta donde se guardó el archivo.
    """
    directorio = os.path.join(INTERMEDIATE_DIR, nombre_dataset)
    os.makedirs(directorio, exist_ok=True)
    ruta = os.path.join(directorio, f"{nombre_dataset}.parquet")
    df.to_parquet(ruta, index=False, compression="snappy")
    logger.info("Guardado %d registros en %s", len(df), ruta)
    return ruta


def _construir_agg_customer_installment_history() -> dict:
    """
    Construye el dataset agregado de historial de cuotas por cliente.

    Lee la tabla de pagos de cuotas (installments_payments) desde Silver
    y calcula métricas agregadas por cliente (SK_ID_CURR) para análisis
    de comportamiento de pago.

    Métricas calculadas:
    - total_installments: Cantidad total de cuotas registradas
    - total_amount_paid: Suma total de pagos realizados
    - total_amount_due: Suma total de cuotas esperadas
    - avg_payment_delay: Retraso promedio de pago (días)
    - max_days_overdue: Máximo de días de retraso
    - min_days_overdue: Mínimo de días de retraso (pagos anticipados negativos)
    - count_late_payments: Cantidad de pagos con retraso
    - count_early_payments: Cantidad de pagos anticipados
    - total_unpaid_amount: Monto total no cubierto (pago < cuota)

    Returns
    -------
    dict
        Diccionario con estado, filas procesadas y ruta del archivo.
    """
    logger.info("Construyendo agg_customer_installment_history...")
    df = _cargar_parquet_silver("installments_payments")

    if df is None:
        return {
            "dataset": "agg_customer_installment_history",
            "status": "skipped",
            "rows": 0,
            "reason": "Datos fuente no disponibles",
        }

    # Verificar columnas necesarias
    columnas_requeridas = [
        "SK_ID_CURR","AMT_PAYMENT","AMT_INSTALMENT",
        "DAYS_ENTRY_PAYMENT","DAYS_INSTALMENT",
    ]
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        logger.error("Columnas faltantes en installments_payments: %s", columnas_faltantes)
        return {
            "dataset": "agg_customer_installment_history",
            "status": "error",
            "rows": 0,
            "reason": f"Columnas faltantes: {columnas_faltantes}",
        }

    # Calcular retraso de pago en días
    df = df.copy()
    df["payment_delay"] = df["DAYS_ENTRY_PAYMENT"] - df["DAYS_INSTALMENT"]

    # Identificar pagos donde no se cubrió el monto total
    df["unpaid_amount"] = (df["AMT_INSTALMENT"] - df["AMT_PAYMENT"]).clip(lower=0)

    # Agrupar por cliente
    agg = df.groupby("SK_ID_CURR").agg(
        total_installments=("SK_ID_CURR", "count"),
        total_amount_paid=("AMT_PAYMENT", "sum"),
        total_amount_due=("AMT_INSTALMENT", "sum"),
        avg_payment_delay=("payment_delay", "mean"),
        max_days_overdue=("payment_delay", "max"),
        min_days_overdue=("payment_delay", "min"),
        count_late_payments=("payment_delay", lambda x: (x > 0).sum()),
        count_early_payments=("payment_delay", lambda x: (x < 0).sum()),
        total_unpaid_amount=("unpaid_amount", "sum"),
    ).reset_index()

    # Rellenar valores nulos con 0 para todas las columnas numéricas
    agg = agg.fillna(0)

    ruta = _guardar_intermediate(agg, "agg_customer_installment_history")
    logger.info("agg_customer_installment_history completado: %d clientes", len(agg))

    return {
        "dataset": "agg_customer_installment_history",
        "status": "success",
        "rows": len(agg),
        "path": ruta,
    }


def _construir_fct_customer_payment_behavior_features() -> dict:
    """
    Construye características de comportamiento de pago temporal por cliente.

    Utiliza el dataset agregado de cuotas para calcular métricas de
    tendencia temporal del comportamiento de pago. Estas características
    son útiles para detectar deterioro o mejora reciente en el pago.

    Métricas calculadas:
    - avg_payment_delay_3m: Retraso promedio de las últimas 3 cuotas
    - avg_payment_delay_6m: Retraso promedio de las últimas 6 cuotas
    - avg_payment_delay_12m: Retraso promedio de las últimas 12 cuotas
    - missed_payment_count_90d: Pagos con retraso en las últimas 3 cuotas
    - payment_consistency_score: Puntuación de consistencia [0, 100]

    Returns
    -------
    dict
        Diccionario con estado, filas procesadas y ruta del archivo.
    """
    logger.info("Construyendo fct_customer_payment_behavior_features...")

    # Cargar datos crudos de cuotas para cálculos de ventanas temporales
    df = _cargar_parquet_silver("installments_payments")

    if df is None:
        return {
            "dataset": "fct_customer_payment_behavior_features",
            "status": "skipped",
            "rows": 0,
            "reason": "Datos fuente no disponibles",
        }

    # Verificar columnas necesarias
    columnas_requeridas = [
        "SK_ID_CURR","AMT_PAYMENT","AMT_INSTALMENT",
        "DAYS_ENTRY_PAYMENT","DAYS_INSTALMENT","NUM_INSTALMENT_NUMBER",
    ]
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        logger.error("Columnas faltantes en installments_payments: %s", columnas_faltantes)
        return {
            "dataset": "fct_customer_payment_behavior_features",
            "status": "error",
            "rows": 0,
            "reason": f"Columnas faltantes: {columnas_faltantes}",
        }

    df = df.copy()
    df["payment_delay"] = df["DAYS_ENTRY_PAYMENT"] - df["DAYS_INSTALMENT"]

    # Ordenar por cliente y número de cuota para cálculos de ventanas
    df = df.sort_values(
        by=["SK_ID_CURR","NUM_INSTALMENT_NUMBER"],
        ascending=[True, True],
    ).reset_index(drop=True)

    # Función auxiliar para calcular retraso promedio de las últimas N cuotas
    def _avg_delay_ultimas_n(grupo: pd.DataFrame, n: int) -> float:
        """Calcula el retraso promedio de las últimas N cuotas de un grupo."""
        if len(grupo) == 0:
            return 0.0
        ultimas = grupo.tail(n)
        return ultimas["payment_delay"].mean()

    # Función auxiliar para contar pagos atrasados en las últimas N cuotas
    def _missed_count_ultimas_n(grupo: pd.DataFrame, n: int) -> int:
        """Cuenta pagos con retraso > 0 en las últimas N cuotas."""
        if len(grupo) == 0:
            return 0
        ultimas = grupo.tail(n)
        return int((ultimas["payment_delay"] > 0).sum())

    # Calcular características por cliente
    resultados = []
    for sk_id, grupo in df.groupby("SK_ID_CURR"):
        avg_3m = _avg_delay_ultimas_n(grupo, 3)
        avg_6m = _avg_delay_ultimas_n(grupo, 6)
        avg_12m = _avg_delay_ultimas_n(grupo, 12)
        missed_90d = _missed_count_ultimas_n(grupo, 3)

        # Puntuación de consistencia: 100 menos penalización por retraso
        # Se limita al rango [0, 100]
        consistency_score = 100.0 - (avg_12m * 2.5)
        consistency_score = max(0.0, min(100.0, consistency_score))

        resultados.append({
            "SK_ID_CURR": sk_id,
            "avg_payment_delay_3m": avg_3m,
            "avg_payment_delay_6m": avg_6m,
            "avg_payment_delay_12m": avg_12m,
            "missed_payment_count_90d": missed_90d,
            "payment_consistency_score": consistency_score,
        })

    features_df = pd.DataFrame(resultados)
    features_df = features_df.fillna(0)

    ruta = _guardar_intermediate(features_df, "fct_customer_payment_behavior_features")
    logger.info("fct_customer_payment_behavior_features completado: %d clientes", len(features_df))

    return {
        "dataset": "fct_customer_payment_behavior_features",
        "status": "success",
        "rows": len(features_df),
        "path": ruta,
    }


def _construir_agg_customer_bureau_history() -> dict:
    """
    Construye el dataset agregado de historial en buró de crédito por cliente.

    Lee la tabla de buró (bureau) desde Silver y calcula métricas agregadas
    por cliente para evaluar el historial crediticio externo.

    Métricas calculadas:
    - total_credits: Cantidad total de créditos registrados
    - active_credits: Créditos activos
    - closed_credits: Créditos cerrados
    - sold_credits: Créditos vendidos
    - bad_debt_credits: Créditos con deuda incobrable
    - total_credit_sum: Suma total de montos de crédito
    - total_overdue_debt: Suma total de deudas vencidas
    - avg_credit_amount: Monto promedio de crédito
    - max_overdue_days: Máximo de días de atraso en buró
    - avg_prolongations: Promedio de prolongaciones de crédito
    - credit_types_count: Cantidad de tipos de crédito distintos
    - has_overdue: Indicador de si tiene algún atraso

    Returns
    -------
    dict
        Diccionario con estado, filas procesadas y ruta del archivo.
    """
    logger.info("Construyendo agg_customer_bureau_history...")
    df = _cargar_parquet_silver("bureau")

    if df is None:
        return {
            "dataset": "agg_customer_bureau_history",
            "status": "skipped",
            "rows": 0,
            "reason": "Datos fuente no disponibles",
        }

    columnas_requeridas = [
        "SK_ID_CURR","CREDIT_ACTIVE","AMT_CREDIT_SUM",
        "AMT_CREDIT_SUM_OVERDUE","CREDIT_DAY_OVERDUE",
        "CNT_CREDIT_PROLONGATIONS","CREDIT_TYPE",
    ]
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        logger.error("Columnas faltantes en bureau: %s", columnas_faltantes)
        return {
            "dataset": "agg_customer_bureau_history",
            "status": "error",
            "rows": 0,
            "reason": f"Columnas faltantes: {columnas_faltantes}",
        }

    df = df.copy()

    # Contar créditos por estado
    active_mask = df["CREDIT_ACTIVE"] == "Active"
    closed_mask = df["CREDIT_ACTIVE"] == "Closed"
    sold_mask = df["CREDIT_ACTIVE"] == "Sold"
    bad_debt_mask = df["CREDIT_ACTIVE"] == "Bad debt"

    agg = df.groupby("SK_ID_CURR").agg(
        total_credits=("SK_ID_CURR", "count"),
        active_credits=("CREDIT_ACTIVE", lambda x: (x == "Active").sum()),
        closed_credits=("CREDIT_ACTIVE", lambda x: (x == "Closed").sum()),
        sold_credits=("CREDIT_ACTIVE", lambda x: (x == "Sold").sum()),
        bad_debt_credits=("CREDIT_ACTIVE", lambda x: (x == "Bad debt").sum()),
        total_credit_sum=("AMT_CREDIT_SUM", "sum"),
        total_overdue_debt=("AMT_CREDIT_SUM_OVERDUE", "sum"),
        avg_credit_amount=("AMT_CREDIT_SUM", "mean"),
        max_overdue_days=("CREDIT_DAY_OVERDUE", "max"),
        avg_prolongations=("CNT_CREDIT_PROLONGATIONS", "mean"),
        credit_types_count=("CREDIT_TYPE", "nunique"),
    ).reset_index()

    # Indicador de atraso: 1 si el máximo de días atrasados es mayor a 0
    agg["has_overdue"] = (agg["max_overdue_days"] > 0).astype(int)

    # Rellenar valores nulos con 0
    agg = agg.fillna(0)

    ruta = _guardar_intermediate(agg, "agg_customer_bureau_history")
    logger.info("agg_customer_bureau_history completado: %d clientes", len(agg))

    return {
        "dataset": "agg_customer_bureau_history",
        "status": "success",
        "rows": len(agg),
        "path": ruta,
    }


def _construir_agg_previous_application_history() -> dict:
    """
    Construye el dataset agregado de solicitudes previas por cliente.

    Lee la tabla de solicitudes previas (previous_application) desde Silver
    y calcula métricas agregadas que reflejan el historial de solicitudes
    y la tasa de aprobación de cada cliente.

    Métricas calculadas:
    - total_previous_apps: Total de solicitudes previas
    - approved_apps: Solicitudes aprobadas
    - refused_apps: Solicitudes rechazadas
    - canceled_apps: Solicitudes canceladas
    - total_applied_amount: Monto total solicitado
    - total_approved_amount: Monto total aprobado
    - avg_annuity: Anualidad promedio
    - approval_rate: Tasa de aprobación (aprobadas / total)
    - refused_rate: Tasa de rechazo (rechazadas / total)
    - most_common_purpose: Tipo de producto más común
    - most_common_channel: Canal más común

    Returns
    -------
    dict
        Diccionario con estado, filas procesadas y ruta del archivo.
    """
    logger.info("Construyendo agg_previous_application_history...")
    df = _cargar_parquet_silver("previous_application")

    if df is None:
        return {
            "dataset": "agg_previous_application_history",
            "status": "skipped",
            "rows": 0,
            "reason": "Datos fuente no disponibles",
        }

    columnas_requeridas = [
        "SK_ID_CURR","NAME_CONTRACT_STATUS","AMT_APPLICATION",
        "AMT_CREDIT","AMT_ANNUITY","NAME_PRODUCT_TYPE","CHANNEL_TYPE",
    ]
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        logger.error("Columnas faltantes en previous_application: %s", columnas_faltantes)
        return {
            "dataset": "agg_previous_application_history",
            "status": "error",
            "rows": 0,
            "reason": f"Columnas faltantes: {columnas_faltantes}",
        }

    df = df.copy()

    # Monto aprobado: solo para solicitudes aprobadas, resto 0
    df["approved_amount"] = df["AMT_CREDIT"].where(
        df["NAME_CONTRACT_STATUS"] == "Approved", 0.0
    )

    agg = df.groupby("SK_ID_CURR").agg(
        total_previous_apps=("SK_ID_CURR", "count"),
        approved_apps=("NAME_CONTRACT_STATUS", lambda x: (x == "Approved").sum()),
        refused_apps=("NAME_CONTRACT_STATUS", lambda x: (x == "Refused").sum()),
        canceled_apps=("NAME_CONTRACT_STATUS", lambda x: (x == "Canceled").sum()),
        total_applied_amount=("AMT_APPLICATION", "sum"),
        total_approved_amount=("approved_amount", "sum"),
        avg_annuity=("AMT_ANNUITY", "mean"),
        most_common_purpose=("NAME_PRODUCT_TYPE", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Desconocido"),
        most_common_channel=("CHANNEL_TYPE", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Desconocido"),
    ).reset_index()

    # Calcular tasas con protección contra división por cero
    total_apps = agg["total_previous_apps"]
    agg["approval_rate"] = (agg["approved_apps"] / total_apps.replace(0, 1)).fillna(0.0)
    agg["refused_rate"] = (agg["refused_apps"] / total_apps.replace(0, 1)).fillna(0.0)

    # Donde total_previous_apps era 0, las tasas deben ser 0
    agg.loc[total_apps == 0, "approval_rate"] = 0.0
    agg.loc[total_apps == 0, "refused_rate"] = 0.0

    # Rellenar valores nulos restantes
    agg = agg.fillna(0)

    ruta = _guardar_intermediate(agg, "agg_previous_application_history")
    logger.info("agg_previous_application_history completado: %d clientes", len(agg))

    return {
        "dataset": "agg_previous_application_history",
        "status": "success",
        "rows": len(agg),
        "path": ruta,
    }


def _construir_agg_credit_card_behavior() -> dict:
    """
    Construye el dataset agregado de comportamiento de tarjeta de crédito.

    Lee la tabla de saldo de tarjetas de crédito (credit_card_balance)
    desde Silver y calcula métricas agregadas por cliente que reflejan
    el uso y comportamiento de pago con tarjetas.

    Métricas calculadas:
    - avg_balance: Saldo promedio
    - max_balance: Saldo máximo registrado
    - avg_credit_limit: Límite de crédito promedio
    - avg_drawings: Promedio de extracciones realizadas
    - avg_payments: Promedio de pagos totales
    - max_dpd: Máximo de días de atraso (DPD)
    - max_dpd_def: Máximo de DPD en tolerancia
    - months_with_dpd: Meses con algún día de atraso
    - avg_installment_maturity: Promedio de cuotas maduras acumuladas

    Returns
    -------
    dict
        Diccionario con estado, filas procesadas y ruta del archivo.
    """
    logger.info("Construyendo agg_credit_card_behavior...")
    df = _cargar_parquet_silver("credit_card_balance")

    if df is None:
        return {
            "dataset": "agg_credit_card_behavior",
            "status": "skipped",
            "rows": 0,
            "reason": "Datos fuente no disponibles",
        }

    columnas_requeridas = [
        "SK_ID_CURR","AMT_BALANCE","AMT_CREDIT_LIMIT_ACTUAL",
        "AMT_DRAWINGS_CURRENT","AMT_PAYMENT_TOTAL_CURRENT",
        "SK_DPD","SK_DPD_DEF","CNT_INSTALMENT_MATURE_CUM",
    ]
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        logger.error("Columnas faltantes en credit_card_balance: %s", columnas_faltantes)
        return {
            "dataset": "agg_credit_card_behavior",
            "status": "error",
            "rows": 0,
            "reason": f"Columnas faltantes: {columnas_faltantes}",
        }

    df = df.copy()

    agg = df.groupby("SK_ID_CURR").agg(
        avg_balance=("AMT_BALANCE", "mean"),
        max_balance=("AMT_BALANCE", "max"),
        avg_credit_limit=("AMT_CREDIT_LIMIT_ACTUAL", "mean"),
        avg_drawings=("AMT_DRAWINGS_CURRENT", "mean"),
        avg_payments=("AMT_PAYMENT_TOTAL_CURRENT", "mean"),
        max_dpd=("SK_DPD", "max"),
        max_dpd_def=("SK_DPD_DEF", "max"),
        months_with_dpd=("SK_DPD", lambda x: (x > 0).sum()),
        avg_installment_maturity=("CNT_INSTALMENT_MATURE_CUM", "mean"),
    ).reset_index()

    # Rellenar valores nulos con 0
    agg = agg.fillna(0)

    ruta = _guardar_intermediate(agg, "agg_credit_card_behavior")
    logger.info("agg_credit_card_behavior completado: %d clientes", len(agg))

    return {
        "dataset": "agg_credit_card_behavior",
        "status": "success",
        "rows": len(agg),
        "path": ruta,
    }


def _construir_agg_pos_cash_behavior() -> dict:
    """
    Construye el dataset agregado de comportamiento POS CASH.

    Lee la tabla de saldo POS CASH (POS_CASH_balance) desde Silver y
    calcula métricas agregadas por cliente sobre préstamos POS y
    su estado de cumplimiento.

    Métricas calculadas:
    - total_records: Cantidad total de registros
    - avg_months_balance: Promedio de balance mensual
    - avg_instalment: Promedio de cuotas
    - avg_future_instalments: Promedio de cuotas futuras
    - max_dpd: Máximo de días de atraso
    - max_dpd_def: Máximo de DPD en tolerancia
    - months_late: Meses con atraso
    - most_common_status: Estado de contrato más común
    - completed_contracts: Contratos completados o firmados

    Returns
    -------
    dict
        Diccionario con estado, filas procesadas y ruta del archivo.
    """
    logger.info("Construyendo agg_pos_cash_behavior...")
    df = _cargar_parquet_silver("POS_CASH_balance")

    if df is None:
        return {
            "dataset": "agg_pos_cash_behavior",
            "status": "skipped",
            "rows": 0,
            "reason": "Datos fuente no disponibles",
        }

    columnas_requeridas = [
        "SK_ID_CURR","MONTHS_BALANCE","CNT_INSTALMENT",
        "CNT_INSTALMENT_FUTURE","SK_DPD","SK_DPD_DEF",
        "NAME_CONTRACT_STATUS",
    ]
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        logger.error("Columnas faltantes en POS_CASH_balance: %s", columnas_faltantes)
        return {
            "dataset": "agg_pos_cash_behavior",
            "status": "error",
            "rows": 0,
            "reason": f"Columnas faltantes: {columnas_faltantes}",
        }

    df = df.copy()

    agg = df.groupby("SK_ID_CURR").agg(
        total_records=("SK_ID_CURR", "count"),
        avg_months_balance=("MONTHS_BALANCE", "mean"),
        avg_instalment=("CNT_INSTALMENT", "mean"),
        avg_future_instalments=("CNT_INSTALMENT_FUTURE", "mean"),
        max_dpd=("SK_DPD", "max"),
        max_dpd_def=("SK_DPD_DEF", "max"),
        months_late=("SK_DPD", lambda x: (x > 0).sum()),
        most_common_status=("NAME_CONTRACT_STATUS", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Desconocido"),
        completed_contracts=("NAME_CONTRACT_STATUS", lambda x: x.isin(["Completed", "Signed"]).sum()),
    ).reset_index()

    # Rellenar valores nulos con 0 (numéricas)
    columnas_numericas = agg.select_dtypes(include="number").columns
    agg[columnas_numericas] = agg[columnas_numericas].fillna(0)

    ruta = _guardar_intermediate(agg, "agg_pos_cash_behavior")
    logger.info("agg_pos_cash_behavior completado: %d clientes", len(agg))

    return {
        "dataset": "agg_pos_cash_behavior",
        "status": "success",
        "rows": len(agg),
        "path": ruta,
    }


# Mapeo de nombres de dataset a funciones constructoras
_CONSTRUCTORES_DATASET = {
    "agg_customer_installment_history": _construir_agg_customer_installment_history,
    "fct_customer_payment_behavior_features": _construir_fct_customer_payment_behavior_features,
    "agg_customer_bureau_history": _construir_agg_customer_bureau_history,
    "agg_previous_application_history": _construir_agg_previous_application_history,
    "agg_credit_card_behavior": _construir_agg_credit_card_behavior,
    "agg_pos_cash_behavior": _construir_agg_pos_cash_behavior,
}


def build_intermediate_dataset(dataset_name: str) -> dict:
    """
    Construye un dataset específico de la capa Intermediate.

    Busca el dataset por nombre en el registro de constructores y ejecuta
    la función correspondiente. Si el nombre no coincide con ningún dataset
    registrado, devuelve un error.

    Parameters
    ----------
    dataset_name : str
        Nombre del dataset a construir. Debe coincidir con una de las claves
        registradas en _CONSTRUCTORES_DATASET.

    Returns
    -------
    dict
        Diccionario con el resultado de la operación que incluye:
        - dataset: Nombre del dataset
        - status: "success","skipped" o "error"
        - rows: Cantidad de filas procesadas
        - path: Ruta del archivo generado (si exitoso)
        - reason: Motivo del salto o error (si aplica)

    Examples
    --------
    >>> resultado = build_intermediate_dataset("agg_customer_bureau_history")
    >>> print(resultado["status"])
    'success'
    """
    logger.info("Solicitada construcción del dataset Intermediate: %s", dataset_name)

    constructor = _CONSTRUCTORES_DATASET.get(dataset_name)
    if constructor is None:
        datasets_disponibles = sorted(_CONSTRUCTORES_DATASET.keys())
        logger.error(
            "Dataset '%s' no reconocido. Datasets disponibles: %s",
            dataset_name,
            datasets_disponibles,
        )
        return {
            "dataset": dataset_name,
            "status": "error",
            "rows": 0,
            "reason": f"Dataset no reconocido. Disponibles: {datasets_disponibles}",
        }

    try:
        return constructor()
    except Exception as e:
        logger.error("Error inesperado al construir '%s': %s", dataset_name, e, exc_info=True)
        return {
            "dataset": dataset_name,
            "status": "error",
            "rows": 0,
            "reason": str(e),
        }


def build_all_intermediate() -> list[dict]:
    """
    Construye todos los datasets de la capa Intermediate.

    Ejecuta secuencialmente cada constructor de dataset registrado y
    recopila los resultados en una lista. Los errores individuales no
    detienen la ejecución de los demás datasets.

    Returns
    -------
    list[dict]
        Lista de diccionarios con el resultado de cada dataset construido.
        Cada elemento contiene: dataset, status, rows, path/reason.

    Examples
    --------
    >>> resultados = build_all_intermediate()
    >>> exitosos = [r for r in resultados if r["status"] == "success"]
    >>> print(f"Exitosos: {len(exitosos)}/{len(resultados)}")
    """
    logger.info("Iniciando construcción de todos los datasets Intermediate...")
    resultados = []

    for nombre_dataset in sorted(_CONSTRUCTORES_DATASET.keys()):
        logger.info("--- Procesando: %s ---", nombre_dataset)
        resultado = build_intermediate_dataset(nombre_dataset)
        resultados.append(resultado)
        logger.info(
            "Resultado para %s: %s (%d filas)",
            nombre_dataset,
            resultado["status"],
            resultado["rows"],
        )

    # Resumen final
    exitosos = [r for r in resultados if r["status"] == "success"]
    omitidos = [r for r in resultados if r["status"] == "skipped"]
    errores = [r for r in resultados if r["status"] == "error"]

    logger.info("=" * 60)
    logger.info("Resumen de construcción Intermediate:")
    logger.info("  Exitosos: %d", len(exitosos))
    logger.info("  Omitidos:  %d", len(omitidos))
    logger.info("  Errores:   %d", len(errores))
    logger.info("=" * 60)

    return resultados
