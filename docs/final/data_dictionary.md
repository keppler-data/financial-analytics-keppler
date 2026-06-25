# Diccionario de Datos — Plataforma de Riesgo Financiero (Caso 5)

**Versión:** 1.0
**Fecha:** 2025-01
**Autor:** Equipo de Gobernanza de Datos
**Alcance:** Todas las capas del data lakehouse — Bronze, Silver, Intermediate y Gold

---

## 1. Propósito del Diccionario de Datos

Este documento constituye el catálogo maestro de la Plataforma de Riesgo Financiero, proporcionando una descripción detallada de cada tabla y columna a lo largo de las capas del data lakehouse. Su objetivo es servir como referencia única y autoritativa para:

- **Analistas de datos**: Comprender el significado, tipo y origen de cada campo.
- **Científicos de datos**: Identificar features disponibles para modelado.
- **Ingenieros de datos**: Validar transformaciones y tipado entre capas.
- **Auditores**: Rastrear la definición de cada métrica utilizada en reportes regulatorios.

Las convenciones utilizadas son: nombres de columnas en mayúsculas y snake_case (estilo Home Credit/Kaggle), tipos expresados según la convención de pandas (Int64 para enteros nullable, float64 para decimales, string para texto). La nulabilidad se indica con ✅ (acepta nulos) o ❌ (no acepta nulos en condiciones normales).

---

## 2. Capa Bronze

La capa Bronze contiene los 7 datasets originales ingeridos desde CSV a Parquet, sin ninguna transformación de datos. Todas las tablas incluyen 4 columnas técnicas adicionales de auditoría.

### 2.1 application_train (Bronze)

| Columna | Tipo Original | Descripción |
|---------|--------------|-------------|
| `SK_ID_CURR` | int64 | Identificador único de la solicitud de crédito. Clave primaria del dataset. |
| `TARGET` | int64 | Variable objetivo: 1 = cliente con dificultad de pago, 0 = cliente sin dificultad. |
| `NAME_CONTRACT_TYPE` | object | Tipo de contrato: "Cash loans" o "Revolving loans". |
| `CODE_GENDER` | object | Género del solicitante: "M" (masculino), "F" (femenino), "XNA" (no especificado). |
| `FLAG_OWN_CAR` | object | Indicador de propiedad de vehículo: "Y" (sí), "N" (no). |
| `FLAG_OWN_REALTY` | object | Indicador de propiedad de inmueble: "Y" (sí), "N" (no). |
| `CNT_CHILDREN` | int64 | Número de hijos del solicitante. |
| `AMT_INCOME_TOTAL` | float64 | Ingreso total anual del solicitante. |
| `AMT_CREDIT` | float64 | Monto del crédito solicitado. |
| `AMT_ANNUITY` | float64 | Anualidad del préstamo (cuota mensual). |
| `AMT_GOODS_PRICE` | float64 | Precio de los bienes para los cuales se solicita el préstamo. |
| `NAME_TYPE_SUITE` | object | Quién acompañó al solicitante en la solicitud. |
| `NAME_INCOME_TYPE` | object | Tipo de ingreso del cliente: "Working", "Commercial associate", "Pensioner", etc. |
| `NAME_EDUCATION_TYPE` | object | Nivel educativo: "Secondary / secondary special", "Higher education", etc. |
| `NAME_FAMILY_STATUS` | object | Estado civil: "Single / not married", "Married", "Civil marriage", etc. |
| `NAME_HOUSING_TYPE` | object | Tipo de vivienda: "House / apartment", "With parents", "Rented apartment", etc. |
| `DAYS_BIRTH` | int64 | Días desde el nacimiento del solicitante (valor negativo, relativo a la fecha de solicitud). |
| `DAYS_EMPLOYED` | int64 | Días desde el inicio del empleo (valor negativo). El valor 365243 es un valor centinela para desempleado. |
| `REGION_RATING_CLIENT` | int64 | Calificación de la región del cliente (1, 2 o 3). |
| `REGION_RATING_CLIENT_W_CITY` | int64 | Calificación de la región con ponderación de ciudad (1, 2 o 3). |
| `ORGANIZATION_TYPE` | object | Tipo de organización donde trabaja el solicitante. |
| `EXT_SOURCE_1` | float64 | Score de riesgo normalizado de fuente externa 1. |
| `EXT_SOURCE_2` | float64 | Score de riesgo normalizado de fuente externa 2. |
| `EXT_SOURCE_3` | float64 | Score de riesgo normalizado de fuente externa 3. |
| `OCCUPATION_TYPE` | object | Tipo de ocupación del solicitante. |
| `_ingestion_date` | object | Marca temporal UTC de la ingesta (ISO 8601). Columna técnica. |
| `_source_file` | object | Nombre del archivo CSV de origen. Columna técnica. |
| `_dataset_name` | object | Nombre lógico del dataset: "application_train". Columna técnica. |
| `_row_hash` | object | Hash MD5 de la fila para detección de duplicados. Columna técnica. |

### 2.2 bureau (Bronze)

| Columna | Tipo Original | Descripción |
|---------|--------------|-------------|
| `SK_ID_CURR` | int64 | Identificador único del cliente (FK hacia application_train). |
| `SK_ID_BUREAU` | int64 | Identificador único del registro en el buró de crédito. Clave primaria. |
| `CREDIT_ACTIVE` | object | Estado del crédito: "Closed", "Active", "Sold", "Bad debt". |
| `CREDIT_CURRENCY` | object | Moneda del crédito: "currency 1", "currency 2", "currency 3", "currency 4". |
| `DAYS_CREDIT` | int64 | Días desde la apertura del crédito en el buró (relativo a la fecha de solicitud actual). |
| `CREDIT_DAY_OVERDUE` | int64 | Días de atraso en el crédito del buró al momento de la solicitud. |
| `AMT_CREDIT_SUM` | float64 | Monto total del crédito en el buró. |
| `AMT_CREDIT_SUM_DEBT` | float64 | Deuda actual del crédito en el buró. |
| `AMT_CREDIT_SUM_OVERDUE` | float64 | Monto vencido del crédito en el buró. |
| `CREDIT_TYPE` | object | Tipo de crédito: "Consumer credit", "Credit card", "Mortgage", etc. |
| `_ingestion_date` | object | Columna técnica — marca temporal de ingesta. |
| `_source_file` | object | Columna técnica — archivo de origen. |
| `_dataset_name` | object | Columna técnica — nombre del dataset. |
| `_row_hash` | object | Columna técnica — hash de fila. |

### 2.3 bureau_balance (Bronze)

| Columna | Tipo Original | Descripción |
|---------|--------------|-------------|
| `SK_ID_BUREAU` | int64 | Identificador del registro en el buró (FK hacia bureau). |
| `MONTHS_BALANCE` | int64 | Mes del balance relativo a la fecha de solicitud (0 = mes actual, -1 = mes anterior). |
| `STATUS` | object | Estado del crédito en ese mes: "C" (cerrado), "X" (desconocido), "0" (sin atraso), "1"-"5" (atraso de 1 a 5+ meses). |
| `_ingestion_date` | object | Columna técnica. |
| `_source_file` | object | Columna técnica. |
| `_dataset_name` | object | Columna técnica. |
| `_row_hash` | object | Columna técnica. |

### 2.4 previous_application (Bronze)

| Columna | Tipo Original | Descripción |
|---------|--------------|-------------|
| `SK_ID_PREV` | int64 | Identificador único de la solicitud previa. Clave primaria. |
| `SK_ID_CURR` | int64 | Identificador del cliente (FK hacia application_train). |
| `NAME_CONTRACT_TYPE` | object | Tipo de contrato de la solicitud previa. |
| `NAME_CONTRACT_STATUS` | object | Estado: "Approved", "Refused", "Canceled", "Unused offer". |
| `AMT_APPLICATION` | float64 | Monto solicitado en la aplicación previa. |
| `AMT_CREDIT` | float64 | Monto aprobado finalmente. |
| `AMT_ANNUITY` | float64 | Anualidad de la solicitud previa. |
| `AMT_DOWN_PAYMENT` | float64 | Pago inicial de la solicitud previa. |
| `DAYS_DECISION` | int64 | Días relativos desde la decisión de la solicitud previa. |
| `CNT_PAYMENT` | float64 | Plazo del préstamo previo en cuotas. |
| `CHANNEL_TYPE` | object | Canal de adquisición: "Country-wide", "AP+ (Cash loan)", "Credit and cash offices", etc. |
| `_ingestion_date` | object | Columna técnica. |
| `_source_file` | object | Columna técnica. |
| `_dataset_name` | object | Columna técnica. |
| `_row_hash` | object | Columna técnica. |

### 2.5 installments_payments (Bronze)

| Columna | Tipo Original | Descripción |
|---------|--------------|-------------|
| `SK_ID_PREV` | int64 | Identificador de la solicitud previa (FK). |
| `SK_ID_CURR` | int64 | Identificador del cliente (FK hacia application_train). |
| `NUM_INSTALMENT_NUMBER` | int64 | Número de la cuota. |
| `NUM_INSTALMENT_VERSION` | int64 | Versión de la cuota (cambia si hubo reestructuración). |
| `DAYS_INSTALMENT` | float64 | Fecha esperada del pago (días relativos a la fecha de solicitud). |
| `DAYS_ENTRY_PAYMENT` | float64 | Fecha real del pago (días relativos). |
| `AMT_INSTALMENT` | float64 | Monto esperado de la cuota. |
| `AMT_PAYMENT` | float64 | Monto realmente pagado por el cliente. |
| `_ingestion_date` | object | Columna técnica. |
| `_source_file` | object | Columna técnica. |
| `_dataset_name` | object | Columna técnica. |
| `_row_hash` | object | Columna técnica. |

### 2.6 credit_card_balance (Bronze)

| Columna | Tipo Original | Descripción |
|---------|--------------|-------------|
| `SK_ID_PREV` | int64 | Identificador de la solicitud previa (FK). |
| `SK_ID_CURR` | int64 | Identificador del cliente (FK hacia application_train). |
| `MONTHS_BALANCE` | int64 | Mes del balance relativo a la solicitud actual. |
| `AMT_BALANCE` | float64 | Saldo actual de la tarjeta de crédito. |
| `AMT_CREDIT_LIMIT_ACTUAL` | float64 | Límite de crédito actual de la tarjeta. |
| `AMT_DRAWINGS_CURRENT` | float64 | Monto total de retiros en el mes. |
| `AMT_PAYMENT_TOTAL_CURRENT` | float64 | Monto total pagado en el mes. |
| `CNT_DRAWINGS_CURRENT` | int64 | Número de transacciones/retiros en el mes. |
| `SK_DPD` | int64 | Días de atraso en el período. |
| `SK_DPD_DEF` | int64 | Días de atraso con tolerancia (DPD con definición de incumplimiento). |
| `_ingestion_date` | object | Columna técnica. |
| `_source_file` | object | Columna técnica. |
| `_dataset_name` | object | Columna técnica. |
| `_row_hash` | object | Columna técnica. |

### 2.7 POS_CASH_balance (Bronze)

| Columna | Tipo Original | Descripción |
|---------|--------------|-------------|
| `SK_ID_PREV` | int64 | Identificador de la solicitud previa (FK). |
| `SK_ID_CURR` | int64 | Identificador del cliente (FK hacia application_train). |
| `MONTHS_BALANCE` | int64 | Mes del balance relativo a la solicitud actual. |
| `CNT_INSTALMENT` | int64 | Número de cuotas del contrato. |
| `CNT_INSTALMENT_FUTURE` | int64 | Cuotas restantes del contrato. |
| `NAME_CONTRACT_STATUS` | object | Estado del contrato: "Active", "Completed", "Signed", etc. |
| `SK_DPD` | int64 | Días de atraso. |
| `SK_DPD_DEF` | int64 | Días de atraso con tolerancia. |
| `_ingestion_date` | object | Columna técnica. |
| `_source_file` | object | Columna técnica. |
| `_dataset_name` | object | Columna técnica. |
| `_row_hash` | object | Columna técnica. |

---

## 3. Capa Silver

La capa Silver contiene los mismos 7 datasets con transformaciones aplicadas: tipado explícito, corrección de anomalías, imputación de nulos y deduplicación. Las columnas técnicas de Bronze se conservan.

### 3.1 Cambios de Tipo Principales

| Dataset | Columna | Tipo en Bronze | Tipo en Silver | Notas |
|---------|---------|---------------|----------------|-------|
| application_train | `SK_ID_CURR`, `TARGET`, `FLAG_OWN_CAR`, `FLAG_OWN_REALTY`, `CNT_FAM_MEMBERS`, `OWN_CAR_AGE` | int64/object | **Int64** (nullable) | Int64 de pandas soporta nulos. |
| application_train | `NAME_CONTRACT_TYPE`, `CODE_GENDER`, `NAME_TYPE_SUITE`, `NAME_INCOME_TYPE`, `NAME_EDUCATION_TYPE`, `NAME_FAMILY_STATUS`, `NAME_HOUSING_TYPE`, `OCCUPATION_TYPE`, `WEEKDAY_APPR_PROCESS_START`, `ORGANIZATION_TYPE` | object | **string** | Tipado de cadena explícito de pandas. |
| application_train | `DAYS_BIRTH`, `DAYS_EMPLOYED`, `DAYS_REGISTRATION`, `DAYS_ID_PUBLISH` | int64/float64 | **Int64** | Días como enteros nullable. |
| application_train | `AMT_INCOME_TOTAL`, `AMT_CREDIT`, `AMT_ANNUITY`, `AMT_GOODS_PRICE`, `REGION_POPULATION_RELATIVE`, `EXT_SOURCE_1/2/3` | float64 | **float64** | Verificado con `pd.to_numeric(errors="coerce")`. |
| application_train | Columnas `*_AVG`, `*_MEDI`, `*_MODE` (≈50 columnas) | float64 | **float64** | Detectadas dinámicamente por sufijo y casteadas. |
| bureau | `SK_ID_CURR`, `SK_ID_BUREAU` | int64 | **Int64** | |
| bureau | `CREDIT_ACTIVE`, `CREDIT_CURRENCY`, `CREDIT_TYPE` | object | **string** | |
| bureau | `DAYS_CREDIT`, `CREDIT_DAY_OVERDUE`, `AMT_CREDIT_SUM`, etc. | int64/float64 | **float64** | Verificación numérica con coerce. |
| bureau_balance | `SK_ID_BUREAU`, `MONTHS_BALANCE` | int64 | **Int64** | |
| bureau_balance | `STATUS` | object | **string** | |
| previous_application | `SK_ID_PREV`, `SK_ID_CURR`, `NFLAG_LAST_APPL_IN_DAY`, `NFLAG_INSURED_ON_APPROVAL` | int64 | **Int64** | |
| previous_application | 12 columnas categóricas | object | **string** | |
| previous_application | `AMT_ANNUITY`, `AMT_APPLICATION`, `AMT_CREDIT`, `DAYS_DECISION`, etc. | int64/float64 | **float64** | |
| installments_payments | `SK_ID_PREV`, `SK_ID_CURR`, `NUM_INSTALMENT_NUMBER`, `NUM_INSTALMENT_VERSION` | int64 | **Int64** | |
| installments_payments | `DAYS_INSTALMENT`, `DAYS_ENTRY_PAYMENT`, `AMT_INSTALMENT`, `AMT_PAYMENT` | float64 | **float64** | |
| credit_card_balance | `SK_ID_PREV`, `SK_ID_CURR`, `MONTHS_BALANCE`, `CNT_DRAWINGS_*`, `SK_DPD`, `SK_DPD_DEF` | int64/float64 | **Int64** | |
| credit_card_balance | `AMT_DRAWINGS_*`, `AMT_PAYMENT_*`, `AMT_RECEIVABLE_*` | float64 | **float64** | |
| POS_CASH_balance | `SK_ID_PREV`, `SK_ID_CURR`, `MONTHS_BALANCE`, `CNT_INSTALMENT`, `SK_DPD`, `SK_DPD_DEF` | int64 | **Int64** | |
| POS_CASH_balance | `NAME_CONTRACT_STATUS` | object | **string** | |

### 3.2 Claves de Deduplicación por Dataset (Silver)

| Dataset | Columnas de Deduplicación |
|---------|--------------------------|
| application_train | `SK_ID_CURR` |
| bureau | `SK_ID_BUREAU` |
| bureau_balance | `SK_ID_BUREAU`, `MONTHS_BALANCE` (clave compuesta) |
| previous_application | `SK_ID_PREV` |
| installments_payments | `SK_ID_PREV`, `NUM_INSTALMENT_NUMBER` (clave compuesta) |
| credit_card_balance | `SK_ID_PREV`, `MONTHS_BALANCE` (clave compuesta) |
| POS_CASH_balance | `SK_ID_PREV`, `MONTHS_BALANCE` (clave compuesta) |

---

## 4. Capa Intermediate

La capa Intermediate contiene 6 tablas de agregación y features generadas a partir de la capa Silver. Cada tabla tiene como clave primaria `SK_ID_CURR` y representa una dimensión del comportamiento crediticio del cliente.

### 4.1 agg_customer_installment_history

Historial agregado de cuotas por cliente. Fuente: Silver installments_payments.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `SK_ID_CURR` | Int64 | Identificador único del cliente. Clave primaria. |
| `total_installments` | float64 | Conteo total de cuotas registradas para el cliente. |
| `total_amount_paid` | float64 | Suma total de todos los montos pagados por el cliente. |
| `avg_installment_amount` | float64 | Monto promedio de cuota (total_amount_paid / total_installments). |
| `avg_days_installment_difference` | float64 | Diferencia promedio en días entre la fecha esperada y la fecha real de pago (DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT). |

### 4.2 fct_customer_payment_behavior_features

Features avanzados de comportamiento de pago temporal. Fuente: Silver installments_payments. Esta tabla incluye métricas de ventana temporal (3, 6 y 12 meses) y un score de consistencia.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `SK_ID_CURR` | Int64 | Identificador único del cliente. Clave primaria. |
| `avg_payment_delay` | float64 | Retraso promedio de pago en días sobre todo el historial. |
| `max_days_overdue` | float64 | Máximo número de días de atraso registrado. |
| `count_late_payments` | float64 | Conteo total de pagos realizados después de la fecha esperada. |
| `avg_payment_delay_3m` | float64 | Retraso promedio de pago en los últimos 3 meses. |
| `avg_payment_delay_6m` | float64 | Retraso promedio de pago en los últimos 6 meses. |
| `avg_payment_delay_12m` | float64 | Retraso promedio de pago en los últimos 12 meses. |
| `missed_payment_count_90d` | float64 | Conteo de pagos faltantes (AMT_PAYMENT = 0 o nulo) en los últimos 90 días. |
| `payment_consistency_score` | float64 | Score de consistencia de pago calculado mediante el coeficiente de variación de los montos pagados. Valores más altos indican mayor regularidad (escala 0-100). |
| `total_unpaid_amount` | float64 | Monto total impagado acumulado (diferencia entre AMT_INSTALMENT y AMT_PAYMENT cuando el pago es menor). |

### 4.3 agg_customer_bureau_history

Historial agregado del buró de crédito por cliente. Fuente: Silver bureau + Silver bureau_balance (unidos por SK_ID_BUREAU).

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `SK_ID_CURR` | Int64 | Identificador único del cliente. Clave primaria. |
| `total_credits` | float64 | Número total de créditos registrados en el buró para el cliente. |
| `active_credits` | float64 | Número de créditos activos (CREDIT_ACTIVE = "Active"). |
| `closed_credits` | float64 | Número de créditos cerrados (CREDIT_ACTIVE = "Closed"). |
| `total_overdue_debt` | float64 | Suma total de deuda vencida (AMT_CREDIT_SUM_OVERDUE). |
| `max_overdue_days` | float64 | Máximo de días de atraso en el buró (CREDIT_DAY_OVERDUE). |
| `avg_credit_amount` | float64 | Monto promedio de crédito en el buró (AMT_CREDIT_SUM / total_credits). |

### 4.4 agg_previous_application_history

Historial de solicitudes previas de crédito. Fuente: Silver previous_application.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `SK_ID_CURR` | Int64 | Identificador único del cliente. Clave primaria. |
| `total_previous_apps` | float64 | Número total de solicitudes previas del cliente. |
| `approval_rate` | float64 | Tasa de aprobación (solicitudes aprobadas / total de solicitudes). Rango [0.0, 1.0]. |
| `avg_applied_amount` | float64 | Monto promedio solicitado en todas las aplicaciones previas. |
| `avg_rejected_amount` | float64 | Monto promedio de las solicitudes que fueron rechazadas. |

### 4.5 agg_credit_card_behavior

Comportamiento de tarjeta de crédito. Fuente: Silver credit_card_balance.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `SK_ID_CURR` | Int64 | Identificador único del cliente. Clave primaria. |
| `avg_balance` | float64 | Saldo promedio de la tarjeta de crédito a lo largo de todos los meses. |
| `max_dpd` | float64 | Máximo de días de atraso (SK_DPD) registrado en la tarjeta. |
| `total_drawings` | float64 | Suma total de retiros (AMT_DRAWINGS_CURRENT) a lo largo de todos los meses. |
| `total_payments` | float64 | Suma total de pagos (AMT_PAYMENT_TOTAL_CURRENT) realizados en la tarjeta. |

### 4.6 agg_pos_cash_behavior

Comportamiento de préstamos POS CASH. Fuente: Silver POS_CASH_balance.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `SK_ID_CURR` | Int64 | Identificador único del cliente. Clave primaria. |
| `totalcontracts` | float64 | Número total de contratos POS CASH del cliente. |
| `completed_contracts` | float64 | Número de contratos con estado "Completed". |
| `avg_cnt_installment` | float64 | Promedio de cuotas totales (CNT_INSTALMENT) por contrato. |
| `avg_sk_dpd` | float64 | Promedio de días de atraso (SK_DPD) por cliente. |

---

## 5. Capa Gold — gold_customer_360

La tabla Gold Customer 360 es la vista unificada del cliente que consolida información de la capa Silver (application_train) con las 6 tablas de la capa Intermediate. Contiene todas las columnas del perfil del cliente, las agregaciones de comportamiento crediticio, y columnas calculadas derivadas.

### 5.1 Columnas del Perfil del Cliente (de Silver application_train)

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `SK_ID_CURR` | Int64 | Identificador único del cliente. Clave primaria de la tabla Gold. |
| `TARGET` | Int64 | Variable objetivo: 1 = default, 0 = no default. |
| `NAME_CONTRACT_TYPE` | string | Tipo de contrato de la solicitud actual. |
| `CODE_GENDER` | string | Género del solicitante. |
| `FLAG_OWN_CAR` | Int64 | Indicador de propiedad de vehículo (0/1). |
| `FLAG_OWN_REALTY` | Int64 | Indicador de propiedad de inmueble (0/1). |
| `CNT_CHILDREN` | Int64 | Número de hijos. |
| `AMT_INCOME_TOTAL` | float64 | Ingreso total anual del cliente. |
| `AMT_CREDIT` | float64 | Monto del crédito aprobado. |
| `AMT_ANNUITY` | float64 | Anualidad del préstamo. |
| `AMT_GOODS_PRICE` | float64 | Precio de los bienes financiados. |
| `NAME_INCOME_TYPE` | string | Tipo de ingreso. |
| `NAME_EDUCATION_TYPE` | string | Nivel educativo. |
| `NAME_FAMILY_STATUS` | string | Estado civil. |
| `NAME_HOUSING_TYPE` | string | Tipo de vivienda. |
| `DAYS_BIRTH` | Int64 | Días desde el nacimiento. |
| `DAYS_EMPLOYED` | Int64 | Días desde el inicio del empleo (anomalía 365243 convertida a nulo). |
| `REGION_RATING_CLIENT` | Int64 | Calificación de la región. |
| `REGION_RATING_CLIENT_W_CITY` | Int64 | Calificación de la región con ponderación urbana. |
| `ORGANIZATION_TYPE` | string | Tipo de organización empleadora. |
| `EXT_SOURCE_1` | float64 | Score de riesgo externo 1. |
| `EXT_SOURCE_2` | float64 | Score de riesgo externo 2. |
| `EXT_SOURCE_3` | float64 | Score de riesgo externo 3. |

### 5.2 Columnas de Agregaciones (de Intermediate)

Todas las columnas de las 6 tablas Intermediate se incorporan mediante LEFT JOIN. Se añaden sufijos para evitar colisiones de nombres: `_install` (agg_customer_installment_history), `_behavior` (fct_customer_payment_behavior_features), `_bureau` (agg_customer_bureau_history), `_prevapp` (agg_previous_application_history), `_cc` (agg_credit_card_behavior), `_pos` (agg_pos_cash_behavior). Ver sección 4 para la descripción de cada columna.

### 5.3 Columnas Calculadas (derivadas en Gold)

| Columna | Tipo | Fórmula | Descripción |
|---------|------|---------|-------------|
| `age_years` | float64 | `abs(DAYS_BIRTH) / 365.25` | Edad del cliente en años con un decimal de precisión. |
| `employed_years` | float64 | `abs(DAYS_EMPLOYED) / 365.25` (solo si DAYS_EMPLOYED ≠ 365243) | Años de empleo del cliente. Nulo si el valor original era el centinela 365243. |
| `credit_to_income_ratio` | float64 | `AMT_CREDIT / AMT_INCOME_TOTAL` (con AMT_INCOME_TOTAL protegido contra división por cero, reemplazando 0 por 1) | Ratio crédito-ingreso. Indica el nivel de endeudamiento del cliente. |
| `annuity_to_income_ratio` | float64 | `AMT_ANNUITY / AMT_INCOME_TOTAL` (con protección contra división por cero) | Ratio anualidad-ingreso. Indica la carga de pago mensual relativa al ingreso. |
| `risk_segment` | string | Basado en `payment_consistency_score` y `max_days_overdue` (ver reglas de negocio) | Segmentación de riesgo del cliente: "LOW_RISK", "MEDIUM_RISK" o "HIGH_RISK". |
| `updated_at` | string | Timestamp ISO 8601 UTC | Marca temporal de la última construcción de la tabla Gold. |

### 5.4 Valores Nulos en Gold

Todos los valores nulos numéricos se reemplazan por **0** y todos los valores nulos de tipo string se reemplazan por **"Unknown"** como paso final de limpieza antes de la escritura a Parquet.

---

## 6. Capa ML Scoring

La capa de ML Scoring no es una tabla persistente del data lakehouse, sino que genera archivos de salida a partir de la tabla Gold:

### 6.1 customer_risk_scores.parquet

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `predicted_default_prob` | float64 | Probabilidad predicha de default (0.0 a 1.0) por el mejor modelo (mayor AUC-ROC entre Logistic Regression y Random Forest). |
| `predicted_default` | int64 | Clasificación binaria: 1 si probabilidad ≥ 0.5, 0 en caso contrario. |
| `risk_segment_predicted` | string | Segmento de riesgo basado en el modelo: "LOW_RISK" (<0.3), "MEDIUM_RISK" (0.3-0.6), "HIGH_RISK" (>0.6). |

---

*Este diccionario debe actualizarse con cada cambio en la estructura de datos o adición de nuevas tablas/columnas. Es la fuente de verdad para cualquier consulta sobre la definición de campos en la plataforma.*
