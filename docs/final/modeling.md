# Modelo de Scoring Crediticio — Baseline

> **Autor:** Data Team — Keppler  
> **Versión:** 1.0  
> **Fecha:** Junio 2025  
> **Módulo:** `ml/training/scoring_baseline.py`

---

## 1. Objetivo del Modelo

El objetivo del modelo es **predecir la probabilidad de que un solicitante de crédito incumpla su pago** (variable `TARGET = 1`). Esta probabilidad se utiliza para:

- **Segmentar clientes** en tres niveles de riesgo (bajo, medio, alto) que guían las decisiones de aprobación de créditos.
- **Priorizar revisiones manuales:** los clientes clasificados como riesgo medio son los que más se benefician de una revisión humana.
- **Medir el riesgo de la cartera:** la distribución de probabilidades de default permite estimar las provisiones necesarias para cubrir pérdidas esperadas.

El modelo se diseña como un **baseline**, es decir, un punto de partida simple pero funcional que establece un rendimiento mínimo a mejorar con técnicas más avanzadas. No se pretende que este modelo se despliegue en producción tal cual; su valor radica en demostrar la viabilidad del enfoque y generar un primer conjunto de predicciones sobre el cual iterar.

---

## 2. Datos de Entrenamiento

### Fuente

Los datos de entrenamiento provienen de la tabla **Gold Customer 360** (`data/gold/gold_customer_360/gold_customer_360.parquet`), que es la salida consolidada del pipeline de datos. Esta tabla contiene una fila por cliente con información demográfica, financiera y de comportamiento de pago.

### Variable objetivo

- **`TARGET`**: Variable binaria donde `0` indica que el cliente cumplió con sus pagos y `1` indica que incurrió en default (no pagó).
- Se filtran filas con `TARGET` nulo antes del entrenamiento.
- Se convierte a tipo `int` para evitar problemas con tipos nullable de Pandas.

### Split de datos

```
Total de clientes con TARGET: ~307,511
├── Train (80%): ~246,009 clientes
└── Test  (20%): ~61,502 clientes
```

El split utiliza `train_test_split` con los siguientes parámetros:

- `test_size=0.2`: 20% de los datos se reservan para evaluación.
- `random_state=42`: Semilla para reproducibilidad.
- `stratify=y`: Se mantiene la proporción original de clases (TARGET=0 y TARGET=1) en ambos conjuntos. Esto es crítico porque el dataset está desbalanceado (~8% de defaults).

### Preprocesamiento

- **Imputación de nulos:** Se rellenan todos los valores nulos con `0`. Esta estrategia es simple pero consistente con la limpieza realizada en Gold (donde los nulos numéricos ya se rellenaron con 0).
- **Manejo de infinitos:** Se reemplazan valores `inf` y `-inf` con `0`, que pueden aparecer tras cálculos de ratios (división por cero).
- **Selección de features:** Se filtran solo las features que existen en el DataFrame. Si una feature definida no está presente (porque la tabla Intermediate correspondiente no se generó), se omite con un warning.

---

## 3. Features Utilizadas

El modelo utiliza **29 features numéricas** que combinan datos de la solicitud del cliente, fuentes externas de riesgo y métricas de comportamiento financiero derivadas de la capa Intermediate.

### Lista completa de features

| # | Feature | Origen | Descripción |
|---|---------|--------|-------------|
| 1 | `AMT_INCOME_TOTAL` | Silver (application_train) | Ingreso total declarado por el solicitante |
| 2 | `AMT_CREDIT` | Silver (application_train) | Monto del crédito solicitado |
| 3 | `AMT_ANNUITY` | Silver (application_train) | Anualidad del crédito (cuota mensual) |
| 4 | `AMT_GOODS_PRICE` | Silver (application_train) | Precio de los bienes para los cuales se solicita el crédito |
| 5 | `DAYS_BIRTH` | Silver (application_train) | Edad del solicitante en días (negativo, relativo a la fecha de solicitud) |
| 6 | `DAYS_EMPLOYED` | Silver (application_train) | Días de empleo del solicitante (negativo, corregido de anomalía 365243) |
| 7 | `CNT_CHILDREN` | Silver (application_train) | Número de hijos del solicitante |
| 8 | `REGION_RATING_CLIENT` | Silver (application_train) | Calificación de la región del cliente (1, 2 o 3) |
| 9 | `EXT_SOURCE_1` | Silver (application_train) | Score de riesgo normalizado de fuente externa 1 |
| 10 | `EXT_SOURCE_2` | Silver (application_train) | Score de riesgo normalizado de fuente externa 2 |
| 11 | `EXT_SOURCE_3` | Silver (application_train) | Score de riesgo normalizado de fuente externa 3 |
| 12 | `total_installments` | Intermediate (installment history) | Cantidad total de cuotas registradas para el cliente |
| 13 | `avg_payment_delay` | Intermediate (installment history) | Retraso promedio de pago en días |
| 14 | `max_days_overdue` | Intermediate (installment history) | Máximo de días de retraso registrado |
| 15 | `count_late_payments` | Intermediate (installment history) | Cantidad de pagos realizados con retraso |
| 16 | `total_unpaid_amount` | Intermediate (installment history) | Monto total que no se cubrió (pago < cuota esperada) |
| 17 | `avg_payment_delay_3m` | Intermediate (payment behavior) | Retraso promedio en las últimas 3 cuotas |
| 18 | `avg_payment_delay_6m` | Intermediate (payment behavior) | Retraso promedio en las últimas 6 cuotas |
| 19 | `avg_payment_delay_12m` | Intermediate (payment behavior) | Retraso promedio en las últimas 12 cuotas |
| 20 | `missed_payment_count_90d` | Intermediate (payment behavior) | Cantidad de pagos atrasados en las últimas 3 cuotas |
| 21 | `payment_consistency_score` | Intermediate (payment behavior) | Puntuación de consistencia de pago (0-100, donde 100 es perfecto) |
| 22 | `total_credits` | Intermediate (bureau history) | Cantidad total de créditos registrados en el buró |
| 23 | `active_credits` | Intermediate (bureau history) | Créditos activos actualmente en el buró |
| 24 | `total_overdue_debt` | Intermediate (bureau history) | Suma total de deudas vencidas reportadas al buró |
| 25 | `max_overdue_days` | Intermediate (bureau history) | Máximo de días de atraso en créditos del buró |
| 26 | `total_previous_apps` | Intermediate (previous applications) | Total de solicitudes previas de crédito en Home Credit |
| 27 | `approval_rate` | Intermediate (previous applications) | Tasa de aprobación de solicitudes previas (0.0 a 1.0) |
| 28 | `avg_balance` | Intermediate (credit card behavior) | Saldo promedio en tarjetas de crédito |
| 29 | `max_dpd` | Intermediate (credit card behavior) | Máximo de días de atraso (Days Past Due) en tarjetas |
| 30 | `credit_to_income_ratio` | Gold (calculada) | Ratio entre monto del crédito e ingreso total |
| 31 | `annuity_to_income_ratio` | Gold (calculada) | Ratio entre anualidad e ingreso total |

### Nota sobre features faltantes

Si una tabla Intermediate no se generó (por ejemplo, porque el CSV de `credit_card_balance` no estaba disponible en `data/seed/`), las features correspondientes no estarán presentes en Gold. El modelo las omite con un warning y entrena con las disponibles. Las 3 fuentes externas (`EXT_SOURCE_1/2/3`) son consistentemente las features más importantes, por lo que el modelo sigue siendo funcional aunque falten algunas features de comportamiento.

---

## 4. Modelos Evaluados

Se evaluaron dos modelos de clasificación binaria con configuraciones simples (sin optimización de hiperparámetros):

### 4.1 Logistic Regression

| Hiperparámetro | Valor | Justificación |
|----------------|-------|---------------|
| `max_iter` | 1000 | Suficiente iteraciones para convergencia del algoritmo de optimización (LBFGS) |
| `random_state` | 42 | Reproducibilidad |
| `class_weight` | `"balanced"` | Ajusta los pesos inversamente proporcionales a la frecuencia de clases. Compensa el desbalance (~92% clase 0, ~8% clase 1) dando más importancia a la clase minoritaria (defaults) |

**Características:** Modelo lineal que asume una relación lineal entre las features y el log-odds de la probabilidad de default. Es interpretable (los coeficientes indican dirección y magnitud de la relación) y rápido de entrenar. Limitado en su capacidad para capturar relaciones no lineales.

### 4.2 Random Forest

| Hiperparámetro | Valor | Justificación |
|----------------|-------|---------------|
| `n_estimators` | 100 | 100 árboles ofrecen un buen balance entre rendimiento y tiempo de entrenamiento |
| `max_depth` | 10 | Limita la profundidad para evitar overfitting. 10 niveles permiten capturar interacciones complejas sin memorizar el training set |
| `random_state` | 42 | Reproducibilidad |
| `class_weight` | `"balanced"` | Mismo balanceo que Logistic Regression |

**Características:** Modelo de ensemble que construye 100 árboles de decisión independientes y promedia sus predicciones. Captura relaciones no lineales e interacciones entre features automáticamente. Más robusto a outliers y escalas diferentes de features. Mayor costo computacional pero mejor rendimiento en la mayoría de problemas tabulares.

---

## 5. Métricas de Evaluación

Todas las métricas se calculan sobre el conjunto de **test** (20% de los datos, no vistos durante el entrenamiento).

### 5.1 AUC-ROC (Área Bajo la Curva ROC)

Es la **métrica principal** para selección del modelo. Mide la capacidad del modelo para distinguir entre clientes que cumplen y clientes que incumplen, independientemente del umbral de decisión.

- **Rango:** 0.5 (sin capacidad discriminativa, equivalente a lanzar una moneda) a 1.0 (discriminación perfecta).
- **Interpretación práctica:** Un AUC de 0.75 significa que si se toman un par aleatorio (un cumplidor y un incumplidor), el modelo asigna una probabilidad más alta al incumplidor el 75% de las veces.
- **Benchmark Kaggle:** En la competencia de Home Credit, los modelos ganadores lograron AUC > 0.80. Un baseline razonable debería estar entre 0.70 y 0.76.

### 5.2 Accuracy (Exactitud)

```
accuracy = (VP + VN) / (VP + VN + FP + FN)
```

Proporción de predicciones correctas. **Cuidado con esta métrica en datasets desbalanceados:** un modelo que siempre predice "no default" tendría ~92% de accuracy sin aprender nada útil.

### 5.3 Precision (Precisión)

```
precision = VP / (VP + FP)
```

De todos los clientes que el modelo predijo como default, ¿qué porcentaje realmente hizo default? Una precisión baja significa muchos falsos positivos (rechazar clientes que habrían pagado).

### 5.4 Recall (Sensibilidad / Tasa de verdaderos positivos)

```
recall = VP / (VP + FN)
```

De todos los clientes que realmente hicieron default, ¿qué porcentaje el modelo detectó correctamente? Un recall bajo significa que muchos incumplidores pasan desapercibidos (falsos negativos). En riesgo crediticio, el recall es crítico porque cada incumplidor no detectado representa una pérdida financiera.

### 5.5 F1-Score

```
f1 = 2 × (precision × recall) / (precision + recall)
```

Media armónica de precision y recall. Útil como métrica única de compromiso entre ambas. Un F1 alto indica un buen balance entre detectar defaults y no rechazar clientes buenos.

### 5.6 Confusion Matrix (Matriz de Confusión)

```
                    Predicho
                DEFAULT (1)   NO DEFAULT (0)
Real  DEFAULT(1)    VP             FN
      NO DEF. (0)   FP             VN
```

| Celda | Significado en riesgo crediticio |
|-------|----------------------------------|
| VP (Verdaderos Positivos) | Incumplidores correctamente identificados. El modelo recomienda rechazar. |
| VN (Verdaderos Negativos) | Cumplidores correctamente identificados. El modelo recomienda aprobar. |
| FP (Falsos Positivos) | Cumplidores rechazados incorrectamente. **Pérdida de negocio** (créditos que se habrían pagado). |
| FN (Falsos Negativos) | Incumplidores aprobados incorrectamente. **Pérdida financiera** (créditos que no se pagarán). |

---

## 6. Selección del Mejor Modelo

El criterio de selección es **mayor AUC-ROC**. Este criterio se elige por las siguientes razones:

1. **Invariabilidad al umbral:** AUC no depende del punto de corte elegido para clasificar. Evalúa la calidad de las probabilidades, no solo las etiquetas predichas.
2. **Robustez al desbalance:** AUC no se ve afectada por la proporción de clases, a diferencia de Accuracy.
3. **Estándar de la industria:** AUC-ROC es la métrica más utilizada en evaluación de modelos de riesgo crediticio, tanto en la literatura académica como en la práctica bancaria (Basilea III/GARP).

En la práctica, **Random Forest suele superar a Logistic Regression** en este problema porque:

- Las relaciones entre features y default son no lineales (ej. el riesgo no sube linealmente con la edad).
- Existen interacciones entre features (ej. un cliente joven con alto ingreso tiene un perfil diferente de un cliente joven con bajo ingreso).
- Random Forest captura estas complejidades de forma automática mediante las particiones de los árboles.

---

## 7. Segmentación de Riesgo

Una vez entrenado el mejor modelo, se generan predicciones de probabilidad para **todos los clientes** (no solo el conjunto de test). Cada cliente recibe una probabilidad de default entre 0.0 y 1.0, que se clasifica en tres segmentos:

| Segmento | Rango de probabilidad | Criterio de asignación | Perfil del cliente | Acción de negocio sugerida |
|----------|----------------------|----------------------|--------------------|---------------------------|
| `LOW_RISK` | `prob < 0.3` | El modelo estima baja probabilidad de incumplimiento | Historial de pagos limpio, fuentes externas favorables, bajo nivel de endeudamiento | **Aprobación automática** del crédito con condiciones estándar |
| `MEDIUM_RISK` | `0.3 ≤ prob < 0.6` | El modelo no tiene alta certeza en ninguna dirección | Perfil mixto: algunas señales positivas, otras negativas | **Revisión manual** por un analista de crédito. Evaluar caso a caso |
| `HIGH_RISK` | `prob ≥ 0.6` | El modelo estima alta probabilidad de incumplimiento | Historial de pagos problemático, alto endeudamiento, fuentes externas desfavorables | **Rechazo** del crédito o condiciones especiales: garantía adicional, tasa de interés más alta, monto reducido |

### Nota sobre el umbral de 0.5

El modelo utiliza un umbral de 0.5 para la predicción binaria (`predicted_default`), pero este umbral es ajustable según la tolerancia al riesgo de la entidad financiera:

- **Reducir el umbral a 0.3:** Se detectan más defaults (mayor recall) pero se rechazan más clientes buenos (menor precision). Apropiado si la entidad es muy conservadora.
- **Aumentar el umbral a 0.7:** Se rechazan menos clientes (mayor precision) pero se pasan más incumplidores (menor recall). Apropiado si la entidad quiere crecer su cartera.

---

## 8. Outputs Generados

El módulo de scoring genera **cuatro archivos de salida**:

### 8.1 `customer_risk_scores.parquet`

**Ruta:** `ml/scoring/customer_risk_scores.parquet`  
**Formato:** Parquet (Snappy)  
**Contenido:** Tabla Gold Customer 360 completa más 3 columnas adicionales:

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `predicted_default_prob` | float64 | Probabilidad de default predicha por el modelo (0.0 a 1.0) |
| `predicted_default` | int64 | Clasificación binaria (0 o 1) basada en umbral 0.5 |
| `risk_segment_predicted` | string | Segmento de riesgo (`LOW_RISK`, `MEDIUM_RISK`, `HIGH_RISK`) |

**Filas:** ~307,511 (todos los clientes con TARGET no nulo).

### 8.2 `model_metrics.json`

**Ruta:** `reports/model_metrics.json`  
**Formato:** JSON  
**Contenido:**

```json
{
  "generated_at": "2025-06-15T14:40:00",
  "best_model": "random_forest",
  "best_auc": 0.7356,
  "models": {
    "logistic_regression": {
      "auc_roc": 0.7102,
      "accuracy": 0.6823,
      "precision": 0.2105,
      "recall": 0.6234,
      "f1_score": 0.3146,
      "confusion_matrix": [[10000, 4000], [1500, 2500]]
    },
    "random_forest": {
      "auc_roc": 0.7356,
      "accuracy": 0.7012,
      "precision": 0.2298,
      "recall": 0.5891,
      "f1_score": 0.3312,
      "confusion_matrix": [[10500, 3500], [1800, 2200]]
    }
  },
  "training_rows": 246009,
  "test_rows": 61502,
  "features_used": 29,
  "risk_segmentation": {
    "LOW_RISK": 180000,
    "MEDIUM_RISK": 95000,
    "HIGH_RISK": 32511
  }
}
```

### 8.3 `model_feature_importance.csv`

**Ruta:** `reports/model_feature_importance.csv`  
**Formato:** CSV  
**Contenido:** Dos columnas (`feature`, `importance`) ordenadas por importancia descendente. Para Random Forest, la importancia se calcula como la reducción media de impureza (Gini) que cada feature aporta a los árboles. Para Logistic Regression, se usa el valor absoluto de los coeficientes.

**Ejemplo esperado (Top 5):**

| feature | importance |
|---------|-----------|
| EXT_SOURCE_3 | 0.142 |
| EXT_SOURCE_2 | 0.108 |
| EXT_SOURCE_1 | 0.089 |
| payment_consistency_score | 0.065 |
| DAYS_BIRTH | 0.048 |

Las fuentes externas (`EXT_SOURCE`) suelen dominar porque son scores de riesgo pre-calculados por agencias externas que ya incorporan información historial del cliente.

### 8.4 `gold_customer_360_for_powerbi.csv`

**Ruta:** `reports/gold_customer_360_for_powerbi.csv`  
**Formato:** CSV  
**Contenido:** Subconjunto de columnas de Gold Customer 360 optimizado para visualización en Power BI:

`SK_ID_CURR`, `TARGET`, `risk_segment`, `risk_segment_predicted`, `predicted_default_prob`, `AMT_INCOME_TOTAL`, `AMT_CREDIT`, `payment_consistency_score`, `max_days_overdue`, `age_years`, `credit_to_income_ratio`, `total_credits`, `active_credits`.

Este archivo se conecta a Power BI mediante el conector de archivos CSV o se sube a SharePoint/OneDrive para acceso automatizado.

---

## 9. Limitaciones del Modelo

### 9.1 Sin optimización de hiperparámetros

Los modelos se entrenan con hiperparámetros por defecto (o valores razonables simples como `max_depth=10`). No se realizó búsqueda de hiperparámetros (Grid Search, Random Search u Optuna). Esto significa que el rendimiento actual probablemente está **varios puntos por debajo del potencial real** del modelo.

**Impacto:** Se estima que una optimización de hiperparámetros podría mejorar el AUC en 0.01-0.03 puntos.

### 9.2 Balanceo de clases limitado

El único mecanismo de balanceo es `class_weight="balanced"`, que ajusta los pesos de las clases durante el entrenamiento. No se aplicaron técnicas más avanzadas como:

- **SMOTE** (Synthetic Minority Over-sampling Technique): genera ejemplos sintéticos de la clase minoritaria.
- **Undersampling aleatorio:** reduce la clase mayoritaria.
- **Class weights personalizados:** ponderaciones ajustadas manualmente según el costo financiero de FP vs FN.

### 9.3 Sin feature engineering avanzado

Las features son principalmente las columnas numéricas disponibles más ratios simples calculados. No se aplicaron técnicas de feature engineering como:

- **Binning** de variables continuas (ej. rangos de edad, rangos de ingreso).
- **Interacciones** entre features (ej. `EXT_SOURCE_2 × AMT_CREDIT`).
- **Polinomios** o transformaciones no lineales.
- **Target encoding** para variables categóricas (se excluyeron del modelo).
- **WOE (Weight of Evidence)** y **IV (Information Value)**, estándar en la industria crediticia.

### 9.4 Sin validación cruzada

El modelo se evalúa con un único split train/test. No se utilizó K-Fold Cross-Validation, lo que significa que la estimación de AUC podría variar dependiendo de qué clientes caen en cada conjunto.

### 9.5 Datos estáticos y sin temporalidad

El modelo no considera la dimensión temporal. Todos los datos se tratan como un corte transversal, sin analizar tendencias o estacionalidades. En producción, un modelo de riesgo debería incorporar variables macroeconómicas (tasa de desempleo, inflación, PIB) y la evolución temporal del comportamiento del cliente.

---

## 10. Próximos Pasos

### 10.1 Modelos más potentes

- **XGBoost / LightGBM:** Son los modelos estándar en la industria para tablas estructuradas. Suelen superar a Random Forest con menor cantidad de árboles y entrenamiento más rápido. LightGBM es particularmente eficiente para datasets con millones de filas.
- **CatBoost:** Maneja variables categóricas de forma nativa sin necesidad de one-hot encoding, lo que permitiría incorporar features como `OCCUPATION_TYPE`, `NAME_EDUCATION_TYPE` y `ORGANIZATION_TYPE`.

### 10.2 Optimización de hiperparámetros

- **Optuna:** Framework de optimización bayesiana que encuentra los mejores hiperparámetros de forma eficiente.
- **Grid Search / Random Search:** Métodos clásicos de scikit-learn con `GridSearchCV` o `RandomizedSearchCV`.
- **Parámetros a optimizar:** `n_estimators`, `max_depth`, `learning_rate`, `min_child_weight`, `subsample`, `colsample_bytree`.

### 10.3 Cross-Validation

- **Stratified K-Fold (k=5):** Evaluar el modelo en 5 particiones diferentes para obtener una estimación más robusta del AUC y su desviación estándar.
- **Repeated Stratified K-Fold:** Repetir el K-Fold varias veces con diferentes semillas para mayor confiabilidad estadística.

### 10.4 Feature Engineering avanzado

- **WOE Binning:** Transformar variables continuas en bins con Weight of Evidence, estándar en scorecards crediticias.
- **Target encoding** para variables categóricas (con regularización para evitar data leakage).
- **Interacciones entre features** basadas en conocimiento del dominio (ej. `ingreso / anualidad`, `deuda_bureau / ingreso`).
- **Polynomial features** de grado 2 para capturar no linealidades simples.

### 10.5 Métricas de negocio

- **Expected Loss:** Calcular la pérdida esperada = PD × LGD × EAD (Probabilidad de Default × Loss Given Default × Exposure at Default).
- **ROI del modelo:** Comparar las pérdidas evitadas (por rechazar clientes de alto riesgo) vs el costo de oportunidad (créditos rechazados que habrían pagado).
- **Curva de Lift / Gain:** Evaluar qué porcentaje de defaults se captura al revisar solo el 10%, 20% o 30% superior de riesgo.
