# Calidad de Datos — Metodología y Resultados

> **Autor:** Data Team — Keppler  
> **Versión:** 1.0  
> **Fecha:** Junio 2025  
> **Módulo:** `quality/data_quality_report.py`

---

## 1. Marco de Calidad

La calidad de datos es un pilar fundamental de cualquier plataforma de datos. Sin datos confiables, los modelos predictivos y los dashboards de negocio generan conclusiones erróneas que pueden traducirse en pérdidas financieras reales. En el contexto de riesgo crediticio, un dato de baja calidad podría llevar a aprobar créditos a clientes de alto riesgo o rechazar a clientes confiables.

Este proyecto implementa un marco de calidad de datos basado en **cuatro dimensiones** clásicas de la literatura de gestión de datos:

### 1.1 Completitud (Completeness)

Mide la proporción de valores no nulos respecto al total de celdas esperadas. Una columna con muchos nulos puede indicar: (a) datos que no se recopilaron, (b) errores en la ingesta, o (c) campos opcionales legítimos.

**Cálculo:** `1 - (total_nulls / total_cells)`

En el contexto de Home Credit, columnas como `EXT_SOURCE_1` tienen ~56% de nulos (fuente externa no disponible para todos los clientes), mientras que `AMT_INCOME_TOTAL` tiene 0% de nulos (campo obligatorio en la solicitud).

### 1.2 Unicidad (Uniqueness)

Mide la presencia de registros duplicados. Los duplicados pueden surgir de: (a) ingesta repetida del mismo archivo, (b) errores en el sistema origen, o (c) uniones cartesianas accidentales.

**Cálculo:** `1 - (total_duplicates / row_count)`

En la capa Bronze, los duplicados se detectan mediante la columna `_row_hash` (hash MD5 de todos los valores de la fila). En Silver, la deduplicación se realiza por clave primaria, por lo que no deberían existir duplicados post-transformación.

### 1.3 Consistencia (Consistency)

Mide la coherencia de los datos entre tablas y a lo largo del pipeline. Por ejemplo:

- Si `application_train` tiene 307,511 clientes únicos (`SK_ID_CURR`), la capa Gold debería tener exactamente 307,511 filas (uno por cliente).
- Si `installments_payments` reporta pagos para un `SK_ID_CURR`, ese cliente debería existir en `application_train`.
- Los tipos de datos deben ser consistentes entre capas (ej. `DAYS_BIRTH` como entero en Bronze, Silver e Intermediate).

Esta dimensión se verifica de forma implícita a través del conteo de filas por capa y la cardinalidad de las claves primarias.

### 1.4 Puntualidad (Timeliness)

Mide si los datos están disponibles cuando se necesitan. En un pipeline batch, esto se traduce en: (a) el DAG se ejecuta en el momento programado, (b) las tareas completan dentro del tiempo esperado, y (c) los datos de origen están actualizados.

En el caso actual, los datos son estáticos (CSVs descargados manualmente), por lo que la puntualidad se gestiona mediante la ejecución manual del DAG. En un escenario de producción, se automatizaría la ingesta desde APIs o bases de datos operativas.

---

## 2. Métricas Calculadas

El módulo `data_quality_report.py` implementa la función `profile_dataset()` que calcula las siguientes métricas para cada dataset:

### 2.1 Métricas generales

| Métrica | Tipo | Cálculo | Ejemplo |
|---------|------|---------|---------|
| `row_count` | entero | `len(df)` | `307,511` |
| `column_count` | entero | `len(df.columns)` | `125` (application_train en Bronze) |
| `total_nulls` | entero | `df.isnull().sum().sum()` | `9,247,820` |
| `total_duplicates` | entero | `df.duplicated().sum()` | `0` |

### 2.2 Métricas por columna

| Métrica | Tipo | Cálculo | Propósito |
|---------|------|---------|-----------|
| `null_percentage_by_column` | diccionario `{col: float}` | `(df.isnull().sum() / row_count * 100).round(2)` | Identificar columnas con alta tasa de nulos que pueden necesitar imputación o exclusión |
| `column_types` | diccionario `{col: str}` | `{col: str(dtype) for col, dtype in df.dtypes.items()}` | Verificar que el tipado es correcto post-transformación |
| `cardinality_by_column` | diccionario `{col: int}` | `{col: df[col].nunique() for col in df.columns}` | Detectar anomalías: cardinalidad 1 (constante), cardinalidad = row_count (ID), cardinalidad inusualmente baja/alta |

### 2.3 Score resumido

| Métrica | Tipo | Rango | Propósito |
|---------|------|-------|-----------|
| `quality_score` | float | 0.0 – 100.0 | Score único que resume la calidad del dataset, útil para comparación rápida entre capas y datasets |

---

## 3. Fórmula del Score de Calidad

El score de calidad es una función ponderada que penaliza la presencia de nulos y duplicados:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   null_pct  = (total_nulls / total_cells) × 100                │
│   dup_pct   = (total_duplicates / row_count) × 100             │
│                                                                 │
│   quality_score = 100 - (null_pct × 0.3) - (dup_pct × 0.2)    │
│                                                                 │
│   Donde:                                                         │
│     total_cells = row_count × column_count                      │
│     quality_score está acotado al rango [0, 100]               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Ponderación de las penalizaciones

| Factor | Peso | Penalización máxima | Justificación |
|--------|------|---------------------|---------------|
| Nulos (`null_pct × 0.3`) | 30% | 30 puntos | Los nulos son el problema de calidad más frecuente en datos financieros. Pueden distorsionar agregaciones y modelos. Sin embargo, no todos los nulos son errores (algunos son legítimos). |
| Duplicados (`dup_pct × 0.2`) | 20% | 20 puntos | Los duplicados son más graves que los nulos porque inflan artificialmente las métricas. Se asigna un peso menor porque en datos crudos los duplicados son esperados y se corrigen en capas posteriores. |
| Base | 100 | — | Se parte de un score perfecto (100) y se descuentan puntos por problemas detectados. |

### Umbrales de interpretación

| Rango | Color | Etiqueta | Acción recomendada |
|-------|-------|----------|-------------------|
| `score ≥ 80` | 🟢 `#27ae60` | **Aceptable** | Los datos son aptos para modelado y reportes de negocio. No se requiere acción correctiva. |
| `50 ≤ score < 80` | 🟡 `#f39c12` | **Requiere atención** | Los datos tienen problemas moderados de nulos o duplicados. Revisar columnas con mayor porcentaje de nulos y evaluar si la imputación es adecuada. |
| `score < 50` | 🔴 `#e74c3c` | **Crítico** | Los datos tienen problemas severos que pueden invalidar conclusiones. Se requiere investigación y corrección antes de usar los datos. |

### Ejemplo de cálculo

Para `application_train` en la capa Bronze (307,511 filas × 125 columnas):

```
total_cells = 307,511 × 125 = 38,438,875
total_nulls ≈ 9,247,820 (estimado)
total_duplicates = 0

null_pct  = (9,247,820 / 38,438,875) × 100 = 24.06%
dup_pct   = (0 / 307,511) × 100 = 0.00%

quality_score = 100 - (24.06 × 0.3) - (0.00 × 0.2)
              = 100 - 7.22 - 0.00
              = 92.78
```

Resultado: **Score 92.8 (verde)** — calidad alta a pesar de los nulos, porque el porcentaje de nulos respecto al total de celdas es moderado y no hay duplicados.

---

## 4. Reporte HTML

El reporte HTML es un archivo autocontenido (no requiere servidor web ni archivos externos) que presenta los resultados del perfilado de calidad de forma visual e interactiva.

### Estructura del dashboard HTML

```
┌────────────────────────────────────────────────────────────┐
│  Data Quality Report                                       │
│  Financial Risk Platform - Caso 5 | Fecha de generación    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │    15    │ │  85.3    │ │  62.1    │ │  98.4    │     │
│  │ Datasets │ │  Score   │ │  Score   │ │  Score   │     │
│  │evaluados │ │ Promedio │ │  Mínimo  │ │  Máximo  │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Capa │ Dataset      │Filas│Cols │Nulos │Dup │Score│   │
│  ├──────┼──────────────┼─────┼─────┼──────┼────┼─────┤   │
│  │BRONZE│application_..│307K │ 125 │ 9.2M │  0 │92.8 │   │
│  │BRONZE│bureau        │1.7M │  17 │ 0.5M │  0 │95.1 │   │
│  │SILVER│application_..│307K │ 122 │ 8.7M │  0 │93.5 │   │
│  │INTERM│agg_customer_ │305K │  10 │    0 │  0 │100  │   │
│  │GOLD  │gold_customer │307K │  ~80 │    0 │  0 │100  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Financial Risk Data Platform - Keppler | Caso 5          │
└────────────────────────────────────────────────────────────┘
```

### Cómo leerlo

1. **Tarjetas superiores:** Resumen global. El "Score Promedio" da una idea rápida de la salud general de los datos. Si está en verde, los datos son confiables en su mayoría.
2. **Tabla principal:** Cada fila es un dataset en una capa específica. Las columnas clave son "Nulos" (nulos absolutos), "Dup" (duplicados) y "Score" (con badge de color).
3. **Badges de capa:** Cada dataset tiene un badge de color que indica su capa (Bronze=ámbar, Silver=azul, Intermediate=púrpura, Gold=dorado) para facilitar la identificación visual.
4. **Tendencia esperada:** El score debería mejorar de Bronze a Gold. Si una capa Silver tiene un score menor que su equivalente en Bronze, indica un problema en la transformación.

### Estilo visual

El reporte usa un tema oscuro (`#0f172a` fondo, `#e2e8f0` texto) con colores de acento por capa. Los badges de score usan colores semánticos (verde/amarillo/rojo). Es completamente responsivo para verse bien en pantallas de presentación.

---

## 5. Reporte JSON

El reporte JSON es la versión machine-readable del reporte de calidad. Está diseñado para ser consumido programáticamente por otros sistemas: pipelines de alertas, dashboards personalizados, APIs internas o herramientas de gobierno de datos.

### Estructura del JSON

```json
{
  "generated_at": "2025-06-15T14:35:00.000000",
  "layers": {
    "bronze": [
      {
        "dataset": "application_train",
        "row_count": 307511,
        "column_count": 125,
        "total_nulls": 9247820,
        "total_duplicates": 0,
        "null_percentage_by_column": {
          "AMT_ANNUITY": 0.04,
          "AMT_GOODS_PRICE": 0.09,
          "EXT_SOURCE_1": 56.38,
          "OCCUPATION_TYPE": 31.35
        },
        "column_types": {
          "SK_ID_CURR": "Int64",
          "TARGET": "Int64",
          "AMT_INCOME_TOTAL": "float64"
        },
        "cardinality_by_column": {
          "SK_ID_CURR": 307511,
          "CODE_GENDER": 3,
          "TARGET": 2
        },
        "quality_score": 92.8
      }
    ],
    "silver": [ ... ],
    "intermediate": [ ... ],
    "gold": [ ... ]
  },
  "summary": {
    "total_datasets": 15,
    "avg_quality_score": 85.3,
    "min_quality_score": 62.1,
    "max_quality_score": 100.0
  }
}
```

### Cómo consumirlo programáticamente

```python
import json

with open("reports/data_quality_summary.json") as f:
    report = json.load(f)

# Obtener score promedio
avg_score = report["summary"]["avg_quality_score"]
print(f"Score promedio: {avg_score}")

# Identificar datasets con score bajo (rojo)
for layer_name, datasets in report["layers"].items():
    for ds in datasets:
        if ds["quality_score"] < 50:
            print(f"⚠️  {layer_name}/{ds['dataset']}: {ds['quality_score']}")

# Obtener las 5 columnas con más nulos en application_train
app = next(
    ds for ds in report["layers"]["bronze"]
    if ds["dataset"] == "application_train"
)
top_nulls = sorted(
    app["null_percentage_by_column"].items(),
    key=lambda x: x[1], reverse=True
)[:5]
print("Top 5 columnas con más nulos:", top_nulls)
```

### Integración con sistemas de alerta

El JSON se puede integrar con sistemas de monitoreo existentes:

- **Prometheus Pushgateway:** Publicar el score promedio como métrica de Prometheus para incluirlo en el dashboard de Grafana.
- **Slack/Teams webhook:** Enviar una alerta si algún dataset cae por debajo del umbral amarillo (score < 50).
- **Airflow sensor:** Crear un `PythonSensor` que lea el JSON y falle si el score de Gold es < 80, bloqueando el paso de scoring.

---

## 6. Hallazgos Esperados por Capa

### 6.1 Capa Bronze (score alto, datos crudos)

La capa Bronze debería tener scores **relativamente altos** (generalmente > 80) porque:

- **Pocos duplicados:** Los CSVs de Kaggle no tienen duplicados a nivel de fila completa (el `_row_hash` lo confirma).
- **Nulos esperados:** Los nulos en Bronze son inherentes al dataset original. Home Credit tiene columnas con >50% de nulos (ej. `EXT_SOURCE_1`, `APARTMENTS_AVG`, `OWN_CAR_AGE`) que son legítimos (el cliente no proporcionó esa información).

**Score típico esperado:** 85–95 (verde).

### 6.2 Capa Silver (score mejora tras limpieza)

La capa Silver debería mantener o mejorar ligeramente el score de Bronze porque:

- **Se eliminan duplicados:** La deduplicación por clave primaria reduce el `total_duplicates` a 0.
- **Se corrigen anomalías:** `DAYS_EMPLOYED=365243` se reemplaza por nulo, lo que incrementa `total_nulls` pero mejora la calidad real de los datos (un valor incorrecto es peor que un nulo).
- **Se imputan nulos:** La imputación de `OCCUPATION_TYPE`, `NAME_TYPE_SUITE` y `NAME_FAMILY_STATUS` reduce el conteo de nulos en esas columnas.

**Score típico esperado:** 88–97 (verde). La mejora respecto a Bronze se debe a la eliminación de duplicados, aunque la corrección de `DAYS_EMPLOYED` puede sumar algunos nulos.

### 6.3 Capa Intermediate (score alto, datos agregados)

La capa Intermediate debería tener los **scores más altos** (cercanos a 100) porque:

- **Sin nulos:** Todas las funciones de agregación rellenan valores nulos con 0 (`agg.fillna(0)`).
- **Sin duplicados:** Cada tabla tiene una fila por `SK_ID_CURR` (agregación por `groupby`).
- **Datos numéricos limpios:** Las métricas agregadas (sumas, promedios, conteos) son inherentemente no-nulos.

**Score típico esperado:** 98–100 (verde).

### 6.4 Capa Gold (score alto, datos consolidados)

La capa Gold debería tener scores **altos** pero potencialmente menores que Intermediate porque:

- **Columnas heredadas de Silver:** Los nulos de columnas como `EXT_SOURCE_1` (56% nulos) se propagan a Gold. Sin embargo, se llenan con 0 en la limpieza final (`gold[numeric_cols].fillna(0)`).
- **Columnas de texto imputadas:** Las columnas categóricas se llenan con `"Unknown"`.
- **Sin duplicados:** Solo hay una fila por `SK_ID_CURR`.

**Score típico esperado:** 98–100 (verde), después de la imputación final de nulos.

---

## 7. Integración con el Pipeline

El módulo de calidad de datos está integrado como una **tarea más del DAG principal** (`case_5_financial_risk_pipeline`):

```
ingest_bronze → transform_silver → build_intermediate → build_gold → quality_report → ml_scoring → pipeline_summary
```

### Posición en el flujo

La tarea `quality_report` se ejecuta **después de la capa Gold** y **antes del modelo de scoring**. Esta posición es intencional:

1. **Después de Gold:** Permite evaluar la calidad de los datos consolidados que alimentarán el modelo. Si la calidad de Gold es baja, el scoring se ejecutará de todas formas (para no bloquear el pipeline), pero los resultados deberían interpretarse con cautela.
2. **Antes del Scoring:** El reporte de calidad queda disponible como evidencia antes de ejecutar el modelo, lo que permite justificar las decisiones de modelado con datos objetivos.

### Flujo de ejecución

```python
# En el DAG (case_5_financial_risk_pipeline.py):

quality_report = PythonOperator(
    task_id="quality_report",
    python_callable=run_quality_checks,  # quality/data_quality_report.py
)
```

La función `run_quality_checks()` ejecuta tres pasos:

1. **`generate_quality_report()`:** Recorre las 4 capas (bronze, silver, intermediate, gold), perfila cada dataset y calcula métricas.
2. **`save_report_html(report)`:** Genera el archivo `reports/data_quality_report.html` con el dashboard visual.
3. **`save_report_json(report)`:** Genera el archivo `reports/data_quality_summary.json` con los datos estructurados.

### Salida de la tarea (XCom)

La tarea retorna un diccionario con las rutas de los archivos generados:

```python
{
    "report": { ... },           # Reporte completo con métricas por capa
    "html_path": "reports/data_quality_report.html",
    "json_path": "reports/data_quality_summary.json"
}
```

Este resultado se propaga a través de XCom (sistema de mensajería interno de Airflow) y queda disponible en el log del `pipeline_summary` final, donde se consolida con los resultados de todas las demás tareas.
