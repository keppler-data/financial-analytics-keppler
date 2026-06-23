# Reglas de Negocio — Plataforma de Riesgo Financiero (Caso 5)

**Versión:** 1.0
**Fecha:** 2025-01
**Autor:** Equipo de Gobernanza de Datos
**Alcance:** Reglas de calidad de datos, ingeniería de features, scoring ML y validación por capa

---

## 1. Propósito del Documento

Este documento cataloga de forma exhaustiva todas las reglas de negocio implementadas en la Plataforma de Riesgo Financiero. Su objetivo es proporcionar un registro auditable y versionado que permita:

- **Reproducibilidad**: Cualquier miembro del equipo debe poder entender exactamente cómo se transforma cada dato.
- **Auditoría regulatoria**: Documentar las decisiones de negocio que afectan los cálculos de riesgo crediticio.
- **Mantenibilidad**: Facilitar la identificación del impacto de cambios en reglas específicas.
- **Validación**: Servir como base para las pruebas automatizadas de la plataforma.

Las reglas se organizan en cuatro categorías: (1) Calidad de Datos, (2) Ingeniería de Features, (3) Scoring ML y (4) Validación por Capa.

---

## 2. Reglas de Calidad de Datos

Estas reglas se aplican durante la transformación de Bronze a Silver en el módulo `silver_tasks.py`.

### 2.1 Anomalía en DAYS_EMPLOYED

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | DQ-001 |
| **Columna afectada** | `application_train.DAYS_EMPLOYED` |
| **Valor anómalo** | `365243` (equivalente a aproximadamente 1,000 años) |
| **Acción** | Reemplazar por `None` (nulo) |
| **Implementación** | `df["DAYS_EMPLOYED"] = df["DAYS_EMPLOYED"].replace(365243, None)` |
| **Justificación** | Este valor es un valor centinela utilizado por Home Credit para indicar que el solicitante no proporcionó información de empleo o está desempleado. Si se tratara como un valor real, distorsionaría gravemente cualquier métrica derivada como `employed_years` o análisis de antigüedad laboral. En el dataset original, aproximadamente 55,374 registros (≈18% del total) presentan esta anomalía. |
| **Impacto downstream** | La columna `employed_years` en Gold será nula para estos registros. Los modelos ML reciben 0 como valor tras el reemplazo de nulos en la preparación de features. |
| **Validación** | Post-transformación, no debe existir ningún registro con `DAYS_EMPLOYED == 365243` en la capa Silver. |

### 2.2 Imputación de NAME_TYPE_SUITE

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | DQ-002 |
| **Columna afectada** | `application_train.NAME_TYPE_SUITE` |
| **Valores nulos** | Aproximadamente 1,292 registros (≈0.4%) |
| **Valor de reemplazo** | `"Unaccompanied"` |
| **Implementación** | `df["NAME_TYPE_SUITE"] = df["NAME_TYPE_SUITE"].fillna("Unaccompanied")` |
| **Justificación** | "Unaccompanied" es la categoría más frecuente en la columna y representa al solicitante que acudió solo a la oficina. La imputación con la moda es adecuada dado el bajo porcentaje de nulos. |
| **Impacto downstream** | No hay impacto significativo en features numéricas; la columna es categórica y se utiliza para segmentación descriptiva, no como feature directa en el modelo. |

### 2.3 Imputación de OCCUPATION_TYPE

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | DQ-003 |
| **Columna afectada** | `application_train.OCCUPATION_TYPE` |
| **Valores nulos** | Aproximadamente 96,391 registros (≈31%) |
| **Valor de reemplazo** | `"Unknown"` |
| **Implementación** | `df["OCCUPATION_TYPE"] = df["OCCUPATION_TYPE"].fillna("Unknown")` |
| **Justificación** | El porcentaje de nulos es demasiado alto (31%) para usar imputación por moda sin riesgo de sesgo. Se crea una categoría explícita "Unknown" que permite al modelo ML tratar la ausencia de información como un signal potencialmente informativo (la falta de ocupación puede correlacionarse con mayor riesgo). |

### 2.4 Imputación de NAME_FAMILY_STATUS

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | DQ-004 |
| **Columna afectada** | `application_train.NAME_FAMILY_STATUS` |
| **Valor de reemplazo** | `"Unknown"` |
| **Implementación** | `df["NAME_FAMILY_STATUS"] = df["NAME_FAMILY_STATUS"].fillna("Unknown")` |
| **Justificación** | Categoría de respaldo para los pocos registros con estado civil no informado. |

### 2.5 Deduplicación por Clave Primaria

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | DQ-005 |
| **Aplica a** | Todos los 7 datasets |
| **Estrategia** | `drop_duplicates(subset=dedup_cols, keep="first")` |
| **Regla de conflicto** | En caso de duplicados, se conserva el primer registro encontrado (por orden de lectura del Parquet). |

Las claves de deduplicación por dataset son:

| Dataset | Columnas de Deduplicación |
|---------|--------------------------|
| application_train | `SK_ID_CURR` |
| bureau | `SK_ID_BUREAU` |
| bureau_balance | `SK_ID_BUREAU`, `MONTHS_BALANCE` |
| previous_application | `SK_ID_PREV` |
| installments_payments | `SK_ID_PREV`, `NUM_INSTALMENT_NUMBER` |
| credit_card_balance | `SK_ID_PREV`, `MONTHS_BALANCE` |
| POS_CASH_balance | `SK_ID_PREV`, `MONTHS_BALANCE` |

### 2.6 Imputación de Valores Numéricos Faltantes (Gold)

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | DQ-006 |
| **Capa** | Gold |
| **Regla** | Todos los valores nulos numéricos → `0`; todos los valores nulos de texto → `"Unknown"` |
| **Justificación** | La tabla Gold es la vista final para consumo de modelos ML y dashboards. Los modelos no aceptan nulos. El valor 0 es neutro para features agregadas (indica ausencia de historial en esa dimensión). |

---

## 3. Reglas de Ingeniería de Features

Estas reglas definen las columnas calculadas que se generan en las capas Intermediate y Gold.

### 3.1 Cálculo de Edad

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | FE-001 |
| **Columna origen** | `DAYS_BIRTH` (Silver application_train) |
| **Columna destino** | `age_years` (Gold) |
| **Fórmula** | `age_years = abs(DAYS_BIRTH) / 365.25` |
| **Precisión** | 1 decimal (`.round(1)`) |
| **Notas** | DAYS_BIRTH es negativo (días antes de la solicitud). Se usa valor absoluto. El divisor 365.25 corrige por años bisiestos. Rango típico: 20-69 años. |

### 3.2 Ratio Crédito a Ingreso

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | FE-002 |
| **Columnas origen** | `AMT_CREDIT`, `AMT_INCOME_TOTAL` |
| **Columna destino** | `credit_to_income_ratio` (Gold) |
| **Fórmula** | `credit_to_income_ratio = AMT_CREDIT / max(AMT_INCOME_TOTAL, 1)` |
| **Precisión** | 4 decimales (`.round(4)`) |
| **Protección** | Si `AMT_INCOME_TOTAL` es 0, se reemplaza por 1 antes de la división para evitar división por cero. |
| **Interpretación** | Valores altos (>5) indican un nivel de endeudamiento preocupante. Valores <1 indican que el crédito es menor que el ingreso anual. |

### 3.3 Ratio Anualidad a Ingreso

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | FE-003 |
| **Columnas origen** | `AMT_ANNUITY`, `AMT_INCOME_TOTAL` |
| **Columna destino** | `annuity_to_income_ratio` (Gold) |
| **Fórmula** | `annuity_to_income_ratio = AMT_ANNUITY / max(AMT_INCOME_TOTAL, 1)` |
| **Precisión** | 4 decimales (`.round(4)`) |
| **Protección** | Misma protección contra división por cero que FE-002. |
| **Interpretación** | Representa la carga mensual del préstamo relativa al ingreso anual. Valores >0.5 son generalmente considerados de alto riesgo. |

### 3.4 Segmentación de Riesgo (Gold)

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | FE-004 |
| **Columnas origen** | `payment_consistency_score`, `max_days_overdue` |
| **Columna destino** | `risk_segment` (Gold) |
| **Criterios** | Ver tabla a continuación. Si las columnas de entrada no existen, se asigna `"MEDIUM_RISK"` por defecto. |

| Segmento | Condición 1 | Condición 2 |
|----------|------------|-------------|
| `LOW_RISK` | `payment_consistency_score >= 80` | `max_days_overdue <= 5` |
| `MEDIUM_RISK` | `payment_consistency_score >= 50` | `max_days_overdue <= 30` |
| `HIGH_RISK` | No cumple ninguna de las anteriores | — |

**Notas de implementación:** Se utiliza `np.select(conditions, choices, default="HIGH_RISK")` con valores nulos rellenados como 0 (consistency) y 0 (overdue) antes de la evaluación. Esto significa que clientes sin historial de pagos (nulos→0) serán clasificados como `HIGH_RISK` por defecto.

### 3.5 Score de Consistencia de Pago

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | FE-005 |
| **Columnas origen** | `AMT_PAYMENT` de Silver installments_payments |
| **Columna destino** | `payment_consistency_score` (fct_customer_payment_behavior_features) |
| **Fórmula** | Coeficiente de variación invertido: `score = 100 * (1 - CV)` donde `CV = std(AMT_PAYMENT) / mean(AMT_PAYMENT)` |
| **Rango** | 0 a 100 |
| **Interpretación** | 100 = pagos perfectamente consistentes (misma cantidad cada mes). 0 = alta variabilidad en los montos de pago. Valores bajos pueden indicar pagos parciales o irregulares. |
| **Manejo de nulos** | Si no hay historial de pagos, el score es nulo (→ 0 en Gold). |

### 3.6 Agregaciones Temporales de Ventana (3m, 6m, 12m)

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | FE-006 |
| **Columnas origen** | `DAYS_INSTALMENT`, `DAYS_ENTRY_PAYMENT`, `AMT_PAYMENT` de Silver installments_payments |
| **Columnas destino** | `avg_payment_delay_3m`, `avg_payment_delay_6m`, `avg_payment_delay_12m` (fct_customer_payment_behavior_features) |
| **Ventanas** | Últimos 90 días (3m), 180 días (6m), 365 días (12m) |
| **Fórmula** | Para cada ventana, se filtran los pagos donde `DAYS_INSTALMENT >= -(ventana_en_días)` y se calcula `mean(DAYS_ENTRY_PAYMENT - DAYS_INSTALMENT)` |
| **Signo** | Valores positivos = pago tardío; negativos = pago anticipado. |

### 3.7 Cálculo de Años de Empleo

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | FE-007 |
| **Columnas origen** | `DAYS_EMPLOYED` (ya corregido por DQ-001) |
| **Columna destino** | `employed_years` (Gold) |
| **Fórmula** | `employed_years = abs(DAYS_EMPLOYED) / 365.25` — solo se aplica cuando `DAYS_EMPLOYED != 365243` |
| **Precisión** | 1 decimal |
| **Nota** | Los registros con la anomalía 365243 (ya convertidos a nulo en Silver) tendrán `employed_years = nulo → 0` en Gold. |

---

## 4. Reglas de Scoring ML

Estas reglas definen el comportamiento de los modelos de machine learning implementados en `scoring_baseline.py`.

### 4.1 Selección de Modelo

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | ML-001 |
| **Modelos evaluados** | Regresión Logística (`LogisticRegression`) y Random Forest (`RandomForestClassifier`) |
| **Métrica principal** | AUC-ROC (Área Bajo la Curva ROC) |
| **Criterio de selección** | Se selecciona el modelo con mayor AUC-ROC en el conjunto de test. |
| **Métricas secundarias reportadas** | Accuracy, Precision, Recall, F1-Score, Confusion Matrix |
| **Justificación** | AUC-ROC es la métrica estándar en la industria financiera para evaluar modelos de scoring crediticio, ya que mide la capacidad de discriminación entre buenos y malos pagadores independientemente del umbral de decisión. |

### 4.2 Manejo de Desbalance de Clases

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | ML-002 |
| **Parámetro** | `class_weight="balanced"` en ambos modelos |
| **Descripción** | Ajusta automáticamente los pesos de las clases de forma inversamente proporcional a su frecuencia. La clase minoritaria (default=1, aproximadamente 8.1% del dataset) recibe un peso mayor (~11.3x) durante el entrenamiento. |
| **Justificación** | El dataset de Home Credit tiene una proporción de default de aproximadamente 8:1. Sin este ajuste, los modelos tenderían a predecir la clase mayoritaria (no default) en casi todos los casos. |

### 4.3 División Train/Test

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | ML-003 |
| **Proporción** | 80% entrenamiento, 20% prueba |
| **Parámetros** | `test_size=0.2`, `random_state=42`, `stratify=y` |
| **Estratificación** | La división mantiene la proporción de TARGET=0 y TARGET=1 en ambos conjuntos. |
| **Reproducibilidad** | `random_state=42` garantiza que la división sea idéntica en cada ejecución. |

### 4.4 Umbral de Clasificación

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | ML-004 |
| **Umbral de default** | `0.5` |
| **Implementación** | `predicted_default = (probability >= 0.5).astype(int)` |
| **Nota** | Este umbral es conservador. En producción, se recomienda ajustar basándose en el costo-beneficio de falsos positivos vs. falsos negativos según las políticas de la entidad financiera. |

### 4.5 Segmentación de Riesgo por Modelo

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | ML-005 |
| **Columna destino** | `risk_segment_predicted` |
| **Criterios** | Basados en `predicted_default_prob` (probabilidad de default del modelo). |

| Segmento | Rango de Probabilidad | Descripción |
|----------|----------------------|-------------|
| `LOW_RISK` | `prob < 0.3` | Baja probabilidad de incumplimiento. Clientes con perfil de pago saludable. |
| `MEDIUM_RISK` | `0.3 ≤ prob < 0.6` | Probabilidad moderada. Requiere monitoreo y posiblemente condiciones especiales. |
| `HIGH_RISK` | `prob ≥ 0.6` | Alta probabilidad de incumplimiento. Requiere evaluación adicional o rechazo. |

### 4.6 Preparación de Features para ML

| Atributo | Detalle |
|----------|---------|
| **ID de Regla** | ML-006 |
| **Features totales esperadas** | 31 (ver lista en `MODEL_FEATURES` del código) |
| **Manejo de nulos** | `fillna(0)` — valores faltantes reemplazados por 0 |
| **Manejo de infinitos** | `replace([np.inf, -np.inf], 0)` — valores infinitos reemplazados por 0 |
| **Eliminación de registros** | Se eliminan filas donde `TARGET` es nulo. |

### 4.7 Hiperparámetros del Modelo

| Modelo | Hiperparámetro | Valor | Justificación |
|--------|---------------|-------|---------------|
| LogisticRegression | `max_iter` | 1000 | Suficiente para convergencia en datos numéricos escalados. |
| LogisticRegression | `random_state` | 42 | Reproducibilidad. |
| LogisticRegression | `class_weight` | "balanced" | Manejo de desbalance (ML-002). |
| RandomForestClassifier | `n_estimators` | 100 | Compromiso entre rendimiento y tiempo de entrenamiento. |
| RandomForestClassifier | `max_depth` | 10 | Previene sobreajuste. |
| RandomForestClassifier | `random_state` | 42 | Reproducibilidad. |
| RandomForestClassifier | `class_weight` | "balanced" | Manejo de desbalance (ML-002). |

---

## 5. Reglas de Validación por Capa

### 5.1 Validación de la Capa Bronze

| Verificación | Criterio de Aceptación |
|-------------|----------------------|
| Existencia de archivos | Los 7 archivos Parquet deben existir en `data/bronze/<dataset_name>/`. |
| Columnas técnicas | Cada tabla debe contener `_ingestion_date`, `_source_file`, `_dataset_name`, `_row_hash`. |
| Integridad de filas | El conteo de filas en Parquet debe coincidir con el conteo de filas en el CSV original. |
| Hash de filas | `_row_hash` no debe tener valores nulos ni duplicados globales (dentro del mismo dataset). |

### 5.2 Validación de la Capa Silver

| Verificación | Criterio de Aceptación |
|-------------|----------------------|
| Tipado correcto | Las columnas deben tener los tipos definidos en el registro del dataset (`_DATASET_REGISTRY`). |
| Cero anomalías DAYS_EMPLOYED | No debe existir ningún registro con `DAYS_EMPLOYED == 365243` en application_train. |
| Cero duplicados | No deben existir registros duplicados según las claves de deduplicación de cada dataset. |
| Imputación completa | No deben existir valores nulos en `NAME_TYPE_SUITE`, `OCCUPATION_TYPE` ni `NAME_FAMILY_STATUS` de application_train. |
| Score de calidad | El score de calidad debe ser ≥ 80 según la fórmula del Quality Report (100 - penalización_nulos*0.3 - penalización_duplicados*0.2). |

### 5.3 Validación de la Capa Intermediate

| Verificación | Criterio de Aceptación |
|-------------|----------------------|
| Clave primaria | Todas las tablas deben tener `SK_ID_CURR` como columna. |
| Unicidad | `SK_ID_CURR` no debe tener duplicados en ninguna tabla Intermediate. |
| No-negatividad | Los conteos (total_credits, active_credits, etc.) no deben ser negativos. |
| Rangos válidos | `approval_rate` debe estar en [0.0, 1.0]. `payment_consistency_score` debe estar en [0.0, 100.0] (o ser nulo). |

### 5.4 Validación de la Capa Gold

| Verificación | Criterio de Aceptación |
|-------------|----------------------|
| Cardinalidad de SK_ID_CURR | La tabla Gold debe tener exactamente el mismo número de registros únicos que Silver application_train. |
| Cero nulos | No deben existir valores nulos en ninguna columna después del reemplazo final. |
| Segmentos de riesgo | La columna `risk_segment` solo debe contener valores: "LOW_RISK", "MEDIUM_RISK" o "HIGH_RISK". |
| Ratios financieros | `credit_to_income_ratio` y `annuity_to_income_ratio` no deben contener valores infinitos. |
| Edad válida | `age_years` debe estar en el rango [18, 100] aproximadamente. |

### 5.5 Validación de ML Scoring

| Verificación | Criterio de Aceptación |
|-------------|----------------------|
| AUC-ROC mínimo | El mejor modelo debe alcanzar AUC-ROC ≥ 0.65 (baseline mínimo aceptable). |
| Probabilidades en rango | `predicted_default_prob` debe estar en [0.0, 1.0] para todos los registros. |
| Cobertura de predicción | Todas las filas de Gold deben tener `predicted_default` y `risk_segment_predicted` asignados. |
| Distribución de segmentos | Ningún segmento de riesgo debe tener 0 clientes. |
| Métricas de clasificación | El modelo debe tener recall > 0.50 para la clase minoritaria (TARGET=1). |

---

## 6. Criterios de Aceptación de la Plataforma

La plataforma completa se considera aceptada para pasar a producción cuando se cumplen **todos** los siguientes criterios:

1. **Pipeline completo ejecutado exitosamente**: Las 7 tablas Bronze, 7 tablas Silver, 6 tablas Intermediate y 1 tabla Gold se generan sin errores.

2. **Calidad de datos ≥ 80**: El score promedio de calidad del reporte `data_quality_report.html` es ≥ 80.0 en todas las capas.

3. **Cero anomalías residuales**: No existen valores `DAYS_EMPLOYED == 365243` en ninguna capa posterior a Bronze.

4. **Gold Customer 360 completo**: La tabla Gold contiene al menos 300,000 registros (consistencia con los ~307K de la fuente), todas las columnas calculadas presentes y sin valores nulos.

5. **Modelo ML aceptable**: El mejor modelo (mayor AUC-ROC entre Logistic Regression y Random Forest) alcanza AUC-ROC ≥ 0.65.

6. **Reportes generados**: Existen los archivos `data_quality_report.html`, `data_quality_summary.json`, `model_metrics.json`, `model_feature_importance.csv` y `gold_customer_360_for_powerbi.csv`.

7. **Segmentación de riesgo funcional**: Los tres segmentos (LOW_RISK, MEDIUM_RISK, HIGH_RISK) tienen al menos 1% de la población cada uno en la segmentación basada en el modelo.

---

## 7. Historial de Cambios

| Fecha | Versión | Regla | Cambio | Autor |
|-------|---------|-------|--------|-------|
| 2025-01 | 1.0 | — | Creación inicial del documento con todas las reglas implementadas. | Equipo de Gobernanza de Datos |

---

*Este documento es de carácter regulatorio interno. Cualquier modificación a las reglas aquí descritas debe ser aprobada por el líder del equipo de datos y el responsable de riesgo crediticio antes de su implementación en producción.*
