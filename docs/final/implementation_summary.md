# Resumen de Implementación — Caso 5

> **Autor:** Data Team — Keppler  
> **Versión:** 1.0  
> **Fecha:** Junio 2025

---

## 1. Objetivo del Proyecto

Una entidad financiera digital especializada en préstamos y microcréditos en Latinoamérica enfrenta problemas críticos de operación: aumento sostenido en incumplimientos de pago, crecimiento de la cartera vencida, fraudes de identidad, aprobación de créditos a clientes de alto riesgo e inconsistencias entre las plataformas financieras internas.

El objetivo de este proyecto es construir una **plataforma de datos end-to-end** que centralice la información financiera dispersa, mejore la trazabilidad de créditos, detecte patrones de mora y riesgo crediticio, y consolide métricas confiables para la toma de decisiones. La plataforma debe ser orquestada, reproducible, monitoreada y capaz de alimentar tanto dashboards de negocio (Power BI) como modelos de scoring predictivo.

---

## 2. Alcance Implementado (80–90%)

A continuación se presenta un checklist de lo que se construyó y lo que quedó pendiente:

### Construido ✅

- [x] **Ingesta Bronze:** Lectura de 7 CSVs con detección automática de codificación, enriquecimiento con 4 columnas técnicas de auditoría, escritura como Parquet con compresión Snappy.
- [x] **Transformación Silver:** Tipado explícito por dataset (enteros nullable, cadenas, flotantes), detección dinámica de columnas normalizadas (sufijos AVG/MEDI/MODE), deduplicación por clave primaria, corrección de la anomalía `DAYS_EMPLOYED=365243`, imputación de nulos críticos.
- [x] **Capa Intermediate:** 6 tablas de agregación de comportamiento financiero por cliente (cuotas, comportamiento temporal de pago, bureau, solicitudes previas, tarjeta de crédito, POS CASH).
- [x] **Capa Gold Customer 360:** Vista unificada por cliente con left joins de todas las capas anteriores, columnas calculadas (edad, años empleados, ratios financieros), segmentación de riesgo en tres niveles.
- [x] **Reporte de calidad de datos:** Perfilado automático por capa y dataset con métricas de completitud, unicidad y cardinalidad. Reporte HTML autocontenido y reporte JSON para consumo programático.
- [x] **Modelo de scoring baseline:** Logistic Regression + Random Forest con selección por AUC-ROC, predicción sobre todo el dataset, segmentación de riesgo predictivo, exportación de scores y métricas.
- [x] **Export para Power BI:** CSV con las columnas clave del Customer 360 listas para conectar al connector de archivos.
- [x] **Orquestación con Airflow 3.x:** DAG principal `case_5_financial_risk_pipeline` con 7 tareas secuenciales (Bronze → Silver → Intermediate → Gold → Quality → Scoring → Summary), ejecutable manualmente (trigger).
- [x] **Infraestructura Docker Compose:** 7 servicios desplegados en EC2 (PostgreSQL, RabbitMQ, Airflow Master, Airflow Worker, Spark, Nginx Proxy Manager, Prometheus + Grafana).
- [x] **Monitoreo Prometheus + Grafana:** Scrapeo de métricas de Airflow y dashboard de salud del pipeline.
- [x] **EDA en notebooks:** 7 notebooks Jupyter con análisis exploratorio por dataset.
- [x] **Documentación técnica:** README, diagramas de arquitectura, guías de despliegue y variables de entorno.

### Pendiente / Parcial ⚠️

- [ ] Migración a PySpark para transformaciones pesadas (actualmente Pandas).
- [ ] Integración de dbt para transformaciones SQL (modelos diseñados en rama `SCRUM-85`, no integrados).
- [ ] Ingesta automatizada desde APIs externas (actualmente descarga manual de CSVs).
- [ ] Conector Athena + Glue Catalog para consultas ad-hoc.
- [ ] Schema Registry para evolución de esquemas.
- [ ] Optimización de hiperparámetros del modelo (GridSearch, Optuna).
- [ ] Exporters de PostgreSQL y RabbitMQ en Prometheus.
- [ ] CI/CD con tests automáticos por capa.
- [ ] Dashboard de Power BI (se genera el CSV pero no el archivo .pbix).

---

## 3. Datasets Utilizados

Todos los datos provienen del dataset **Home Credit Default Risk** de Kaggle, que contiene información histórica de solicitudes de crédito de Home Credit, una empresa internacional de préstamos al consumo.

| # | Dataset | CSV de origen | Filas (aprox.) | Clave primaria | Descripción |
|---|---------|---------------|----------------|----------------|-------------|
| 1 | `application_train` | `application_train.csv` | 307,511 | `SK_ID_CURR` | Solicitud de crédito principal con información demográfica, financiera y la variable objetivo `TARGET` (0 = pago, 1 = default) |
| 2 | `bureau` | `bureau.csv` | 1,716,428 | `SK_ID_BUREAU` | Créditos previos del cliente reportados al buró de crédito |
| 3 | `bureau_balance` | `bureau_balance.csv` | 27,299,925 | `SK_ID_BUREAU` + `MONTHS_BALANCE` | Estado mensual de cada crédito del buró (D, C, X, 0-5) |
| 4 | `previous_application` | `previous_application.csv` | 1,670,214 | `SK_ID_PREV` | Solicitudes previas de crédito del cliente en Home Credit |
| 5 | `installments_payments` | `installments_payments.csv` | 13,605,401 | `SK_ID_PREV` + `NUM_INSTALMENT_NUMBER` | Historial de pagos de cuotas para créditos previos |
| 6 | `credit_card_balance` | `credit_card_balance.csv` | 3,840,313 | `SK_ID_PREV` + `MONTHS_BALANCE` | Saldo mensual de tarjetas de crédito de Home Credit |
| 7 | `POS_CASH_balance` | `POS_CASH_balance.csv` | 10,001,358 | `SK_ID_PREV` + `MONTHS_BALANCE` | Saldo mensual de préstamos POS (punto de venta) y cash loans |

**Total de filas procesadas:** ~43.7 millones de registros distribuidos en 7 tablas.

---

## 4. Capa Bronze

La capa Bronze es la primera etapa del pipeline y representa la captura fiel de los datos de origen sin ninguna modificación de contenido. Su propósito es servir como un **almacén inmutable de registro** (audit trail) que preserva los datos exactamente como llegaron.

### Qué hace

1. **Lectura de CSVs:** Lee cada uno de los 7 archivos CSV desde `data/seed/` con detección automática de codificación (prueba utf-8, luego latin-1, luego cp1252).
2. **Enriquecimiento con columnas técnicas:** Se añaden 4 columnas de metadata a cada registro:

| Columna técnica | Tipo | Descripción |
|----------------|------|-------------|
| `_ingestion_date` | string (ISO 8601) | Marca temporal UTC del momento de la ingesta. Ej: `2025-06-15T14:30:00.123456+00:00` |
| `_source_file` | string | Nombre del archivo CSV de origen. Ej: `application_train.csv` |
| `_dataset_name` | string | Nombre lógico del dataset. Ej: `application_train` |
| `_row_hash` | string (MD5 hex) | Hash de 32 caracteres calculado sobre los valores de la fila (ordenados alfabéticamente por nombre de columna). Permite detectar duplicados exactos incluso si provienen de diferentes archivos o ingestas. |

3. **Escritura como Parquet:** Cada dataset se guarda como un archivo `.parquet` con compresión Snappy en `data/bronze/<dataset_name>/<dataset_name>.parquet`.

### Por qué estas columnas técnicas

- **Trazabilidad:** `_ingestion_date` y `_source_file` permiten responder "¿cuándo se ingirió este dato?" y "¿de qué archivo proviene?".
- **Linaje:** `_dataset_name` facilita el rastreo del dato a través de las capas.
- **Deduplicación:** `_row_hash` permite identificar registros duplicados (misma información) sin depender de una clave primaria que podría no existir en la capa cruda.

---

## 5. Capa Silver

La capa Silver aplica limpieza, estandarización y tipado a los datos crudos de Bronze. Es la capa donde los datos pasan de ser "crudos" a ser "confiables para análisis".

### Transformaciones por dataset

| Transformación | Detalle |
|----------------|---------|
| **Tipado explícito** | Cada dataset tiene un catálogo (`_DATASET_REGISTRY`) que define qué columnas son enteros (`Int64` nullable), cadenas (`string`) y flotantes (`float64`). Esto elimina la ambigüedad de tipos que los CSV heredan. |
| **Columnas normalizadas** | En `application_train` se detectan dinámicamente todas las columnas con sufijos `_AVG`, `_MEDI`, `_MODE` (ej. `APARTMENTS_AVG`, `BASEMENTAREA_MODE`) y se castean a `float64`. Son ~48 columnas de información normalizada sobre el inmueble del cliente. |
| **Deduplicación** | Cada dataset se deduplica por su clave primaria: `SK_ID_CURR` (application_train), `SK_ID_BUREAU` (bureau), `SK_ID_BUREAU` + `MONTHS_BALANCE` (bureau_balance), `SK_ID_PREV` (previous_application, installments_payments, credit_card_balance, POS_CASH_balance). Se conserva el primer registro encontrado. |
| **Corrección de anomalía DAYS_EMPLOYED** | El valor `365243` en `DAYS_EMPLOYED` es un valor centinela que Home Credit utiliza para indicar "desempleo". En la realidad, 365243 días ≈ 1000 años. Se reemplaza por `None` (nulo) para que los modelos y agregaciones no se distorsionen. |
| **Imputación de nulos críticos** | `NAME_TYPE_SUITE` → `"Unaccompanied"`, `OCCUPATION_TYPE` → `"Unknown"`, `NAME_FAMILY_STATUS` → `"Unknown"`. Estas columnas categóricas con nulos se imputan con valores por defecto que no distorsionan el análisis. |

### Estadísticas típicas de transformación

- **application_train:** 307,511 filas entrada → 307,511 filas salida (sin duplicados por `SK_ID_CURR`). ~55,000 anomalías corregidas en `DAYS_EMPLOYED`. ~700K nulos imputados en columnas categóricas.
- **bureau:** ~1.7M filas entrada → ~1.7M salida tras deduplicar por `SK_ID_BUREAU`.
- **installments_payments:** ~13.6M filas entrada → ~13.6M salida.

---

## 6. Capa Intermediate

La capa Intermediate transforma los datos limpios de Silver en **tablas de características agregadas por cliente**, optimizadas para el modelado de riesgo crediticio. Cada tabla responde a una pregunta de negocio específica sobre el comportamiento financiero del cliente.

### Las 6 tablas de agregación

| # | Tabla | Fuente (Silver) | Métricas principales |
|---|-------|-----------------|---------------------|
| 1 | `agg_customer_installment_history` | `installments_payments` | `total_installments`, `total_amount_paid`, `total_amount_due`, `avg_payment_delay`, `max_days_overdue`, `min_days_overdue`, `count_late_payments`, `count_early_payments`, `total_unpaid_amount` |
| 2 | `fct_customer_payment_behavior_features` | `installments_payments` | `avg_payment_delay_3m`, `avg_payment_delay_6m`, `avg_payment_delay_12m`, `missed_payment_count_90d`, `payment_consistency_score` (0-100) |
| 3 | `agg_customer_bureau_history` | `bureau` | `total_credits`, `active_credits`, `closed_credits`, `sold_credits`, `bad_debt_credits`, `total_credit_sum`, `total_overdue_debt`, `avg_credit_amount`, `max_overdue_days`, `avg_prolongations`, `credit_types_count`, `has_overdue` |
| 4 | `agg_previous_application_history` | `previous_application` | `total_previous_apps`, `approved_apps`, `refused_apps`, `canceled_apps`, `total_applied_amount`, `total_approved_amount`, `avg_annuity`, `approval_rate`, `refused_rate`, `most_common_purpose`, `most_common_channel` |
| 5 | `agg_credit_card_behavior` | `credit_card_balance` | `avg_balance`, `max_balance`, `avg_credit_limit`, `avg_drawings`, `avg_payments`, `max_dpd`, `max_dpd_def`, `months_with_dpd`, `avg_installment_maturity` |
| 6 | `agg_pos_cash_behavior` | `POS_CASH_balance` | `total_records`, `avg_months_balance`, `avg_instalment`, `avg_future_instalments`, `max_dpd`, `max_dpd_def`, `months_late`, `most_common_status`, `completed_contracts` |

### Lógica de agregación

Todas las tablas se construyen con `df.groupby("SK_ID_CURR").agg(...)` donde las funciones de agregación incluyen:

- **Conteos:** `count`, `nunique`, conteos condicionales con lambdas `(x > 0).sum()`.
- **Sumas:** `sum` para montos totales (pagos, créditos, deudas).
- **Promedios:** `mean` para valores típicos (retraso promedio, saldo promedio).
- **Extremos:** `max`, `min` para peores casos (máximo de días de atraso).
- **Moda:** `x.mode().iloc[0]` para la categoría más frecuente (tipo de producto, canal, estado de contrato).

Los valores nulos resultantes se rellenan con 0 (numéricas) para que no afecten los modelos downstream.

---

## 7. Capa Gold Customer 360

La capa Gold es el producto final del pipeline de datos. Consolidar toda la información del cliente en una **única vista de 360°** que combina datos demográficos, financieros, de comportamiento de pago, historial crediticio y segmentación de riesgo.

### Columnas principales

| Grupo de columnas | Ejemplos |
|-------------------|----------|
| **Identificación** | `SK_ID_CURR` |
| **Variable objetivo** | `TARGET` (0 = cumplió, 1 = default) |
| **Demográficas** | `CODE_GENDER`, `DAYS_BIRTH`, `NAME_FAMILY_STATUS`, `NAME_EDUCATION_TYPE` |
| **Financieras** | `AMT_INCOME_TOTAL`, `AMT_CREDIT`, `AMT_ANNUITY`, `AMT_GOODS_PRICE` |
| **Comportamiento de pago** (de Intermediate) | `payment_consistency_score`, `avg_payment_delay`, `max_days_overdue`, `count_late_payments`, `total_unpaid_amount` |
| **Historial crediticio** (de Intermediate) | `total_credits`, `active_credits`, `total_overdue_debt`, `max_overdue_days` |
| **Solicitudes previas** (de Intermediate) | `total_previous_apps`, `approval_rate` |
| **Tarjeta de crédito** (de Intermediate) | `avg_balance`, `max_dpd` |
| **POS CASH** (de Intermediate) | `months_late`, `completed_contracts` |
| **Columnas calculadas** | `age_years`, `employed_years`, `credit_to_income_ratio`, `annuity_to_income_ratio` |

### Segmentación de riesgo

La segmentación se realiza mediante reglas basadas en dos indicadores clave:

```
Si payment_consistency_score >= 80  Y  max_days_overdue <= 5   →  LOW_RISK
Si payment_consistency_score >= 50  Y  max_days_overdue <= 30  →  MEDIUM_RISK
En cualquier otro caso                                         →  HIGH_RISK
```

| Segmento | Criterio | Perfil típico del cliente |
|----------|----------|---------------------------|
| `LOW_RISK` | Alta consistencia de pago (≥80) y poco o ningún atraso (≤5 días) | Cliente confiable con historial de pagos puntuales |
| `MEDIUM_RISK` | Consistencia moderada (≥50) y atraso moderado (≤30 días) | Cliente con ocasionalmente retrasos pero que eventualmente paga |
| `HIGH_RISK` | Baja consistencia (<50) o atrasos significativos (>30 días) | Cliente con historial problemático de pagos |

---

## 8. Calidad de Datos

### Qué se mide

El módulo de calidad de datos (`quality/data_quality_report.py`) calcula las siguientes métricas para cada dataset en cada capa:

| Métrica | Cálculo | Propósito |
|---------|---------|-----------|
| `row_count` | `len(df)` | Verificar que no se perdieron filas inesperadamente |
| `column_count` | `len(df.columns)` | Verificar la integridad del esquema |
| `total_nulls` | `df.isnull().sum().sum()` | Medir la cantidad absoluta de valores faltantes |
| `total_duplicates` | `df.duplicated().sum()` | Detectar registros idénticos |
| `null_percentage_by_column` | `(df.isnull().sum() / row_count * 100).round(2)` | Identificar columnas con alta tasa de nulos |
| `cardinality_by_column` | `df[col].nunique()` | Detectar columnas con baja o alta cardinalidad (posibles errores) |
| `quality_score` | Fórmula detallada abajo | Score resumido 0-100 para comparación rápida |

### Fórmula del Score de Calidad

```
null_pct  = (total_nulls / total_cells) × 100
dup_pct   = (total_duplicates / row_count) × 100

quality_score = 100 - (null_pct × 0.3) - (dup_pct × 0.2)
```

- El rango del score es **[0, 100]**.
- La penalización máxima por nulos es de 30 puntos (si el 100% de las celdas son nulas).
- La penalización máxima por duplicados es de 20 puntos (si el 100% de las filas son duplicadas).

### Umbrales de interpretación

| Score | Color | Interpretación |
|-------|-------|----------------|
| ≥ 80 | 🟢 Verde | Datos con alta calidad, aptos para modelado y reportes |
| 50 – 79.9 | 🟡 Amarillo | Datos aceptables con nulos o duplicados que deben revisarse |
| < 50 | 🔴 Rojo | Datos con problemas significativos que requieren atención inmediata |

---

## 9. Modelo de Scoring

El modelo de scoring es un **baseline** de clasificación binaria que predice la probabilidad de que un cliente incumpla su pago (`TARGET=1`).

### Modelos evaluados

| Modelo | Hiperparámetros | Balanceo de clases |
|--------|-----------------|-------------------|
| **Logistic Regression** | `max_iter=1000`, `random_state=42` | `class_weight="balanced"` |
| **Random Forest** | `n_estimators=100`, `max_depth=10`, `random_state=42` | `class_weight="balanced"` |

### Features utilizadas

Se definen 29 features numéricas que combinan datos demográficos (`DAYS_BIRTH`, `AMT_INCOME_TOTAL`), fuentes externas (`EXT_SOURCE_1/2/3`) y todas las métricas de comportamiento de las tablas Intermediate (`payment_consistency_score`, `max_days_overdue`, `total_credits`, `active_credits`, etc.).

### Métricas de evaluación

- **AUC-ROC:** Métrica principal para selección del modelo. Mide la capacidad discriminativa del modelo.
- **Accuracy, Precision, Recall, F1-Score:** Métricas complementarias que informan sobre el balance entre predicciones correctas y falsos positivos/negativos.
- **Confusion Matrix:** Muestra la distribución de verdaderos positivos, verdaderos negativos, falsos positivos y falsos negativos.

### Selección del mejor modelo

Se selecciona el modelo con **mayor AUC-ROC**. En la práctica, Random Forest suele superar a Logistic Regression en este tipo de problemas con features no lineales.

### Segmentación de riesgo del modelo

| Segmento | Rango de probabilidad | Acción sugerida |
|----------|----------------------|-----------------|
| `LOW_RISK` | `prob < 0.3` | Aprobación automática del crédito |
| `MEDIUM_RISK` | `0.3 ≤ prob < 0.6` | Revisión manual por analista |
| `HIGH_RISK` | `prob ≥ 0.6` | Rechazo o condiciones especiales (garantía, tasa más alta) |

---

## 10. Monitoreo

### Prometheus

Prometheus scrapea las métricas de Airflow cada 15 segundos desde el endpoint `/admin/metrics`. Las métricas clave monitoreadas son:

- Tiempos de ejecución de cada tarea del pipeline.
- Estado de DAG runs (success/failed/running).
- Latido del scheduler (heartbeat).
- Tamaño de la cola Celery de tareas pendientes.

### Grafana

Grafana presenta estas métricas en un dashboard interactivo accesible en `http://IP_SERVIDOR:3000`. Los paneles muestran:

- Estado actual del DAG (stat panel con color verde/rojo).
- Duración de cada tarea (bar chart comparativo).
- Distribución de tareas exitosas vs fallidas (pie chart).
- Evolución temporal de la cola de tareas (time series).

Este monitoreo permite detectar en tiempo real si el pipeline está degradado, si una tarea particular está tardando más de lo habitual o si hay acumulación de trabajos en la cola.
