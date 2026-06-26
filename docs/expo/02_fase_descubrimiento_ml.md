# Fase 2: Descubrimiento de Variables y Estandarización (Doble Flujo)

Este documento detalla la sustentación técnica de la fase intermedia y de Machine Learning (Spark ML) implementada en el pipeline analítico multi-banco. El objetivo de esta fase es consolidar los datos limpios de la capa Silver y utilizar Inteligencia Artificial para descubrir las 20 variables más importantes (Feature Selection) que dictarán la estructura del modelo de negocio final.

## 1. Capa `Intermediate` (dbt & AWS Athena)

Antes de que los modelos de Machine Learning pudieran ingerir los datos, era imperativo unificarlos y estandarizarlos. Esto se realizó mediante modelos `dbt` sobre AWS Athena.

### Estandarización del Target (`is_default`)
Cada banco (dataset original en CSV) definía la morosidad de forma distinta:
*   **Home Credit:** `TARGET` (1 o 0).
*   **Give Me Some Credit:** `SeriousDlqin2yrs` (1 o 0).
*   **Lending Club:** `loan_status` (Textos como 'Charged Off' o 'Fully Paid').
*   **Loan Prediction:** `Loan_Status` ('N' o 'Y').

**Acción:** La capa Silver limpió estas reglas de negocio complejas y la capa `intermediate` de dbt hereda una única columna estandarizada universal: `is_default` (1 = Moroso, 0 = Pagado).

### Consolidación por Dataset
*   **Home Credit** (*application_train.csv, bureau.csv, previous_application.csv*): Se desarrolló el modelo `int_home_credit_consolidated.sql` que hace `LEFT JOIN` para cruzar la tabla principal de aplicaciones con métricas agregadas del buró de crédito (promedios de deudas) y préstamos previos.
*   **Resto de Bancos:** Se crearon modelos passthrough para estandarizar la lectura directamente hacia Spark.
*   *Nota Técnica:* Se implementó un mapeo de metadatos en `sources.yml` (`identifier: "cs-training"`) para solventar discrepancias de sintaxis entre AWS Glue (que permite guiones) y dbt (que requiere guiones bajos).

---

## 2. Descubrimiento con Machine Learning (Spark MLlib)

Para evitar el sesgo humano al diseñar el modelo de datos final, se desarrolló un script genérico en PySpark (`feature_discovery.py`) que analiza los 4 bancos en paralelo utilizando **Random Forest Classifier**.

### A. Preparación y Calidad de Datos
El algoritmo Random Forest de Spark es estricto y no tolera valores nulos (Null/NaN) ni variables de texto sin codificar:
1.  **Filtro de "Data Leakage":** Se eliminan todas las filas donde `is_default` es nulo (ej. préstamos "vigentes" de los cuales aún no se conoce el desenlace).
2.  **Selección Numérica:** El modelo se entrena exclusivamente con las columnas numéricas.
3.  **Manejo Avanzado de Nulos (Imputer):**
    *   Se implementó un conteo dinámico para detectar y **descartar variables 100% nulas** (causadas por `LEFT JOINs` dispersos o columnas vacías en origen). Esto evita errores fatales (`SparkException`).
    *   Los valores nulos restantes se imputan matemáticamente usando la **mediana** de cada columna.

### B. Entrenamiento del Modelo (Random Forest)
*   **Vector Assembler:** Empaqueta todas las variables imputadas en un único vector de características (`features`).
*   **Muestreo Inteligente:** Si un dataset supera el 1,000,000 de filas, Spark realiza un sampleo aleatorio (`fraction`) para proteger la memoria RAM del clúster (Ejecutores configurados a 1500M y 10 cores compartidos).
*   Se entrena un `RandomForestClassifier` con 50 árboles (`numTrees=50`) y profundidad 5 (`maxDepth=5`) buscando un equilibrio entre precisión y velocidad, dado que el fin no es predecir aún, sino evaluar la entropía y ganancia de información (Gini).

### C. Salida: El Paradigma del Doble Flujo
En lugar de escribir los resultados directamente a una base de datos (lo que rompería el esquema ELT), el script hace lo siguiente:
1.  Extrae las importancias (`featureImportances`).
2.  Aísla el **Top 20** de variables que más peso tienen para predecir si un cliente va a impagar.
3.  **Exporta un JSON** (`<banco>_ml_features.json`) y un reporte Markdown a S3.

**¿Por qué exportar a JSON?**
Esta es la base de la arquitectura. El script ML actúa como un "descubridor". En el siguiente paso (Fase 4), dbt leerá dinámicamente estos archivos JSON desde S3 para saber exactamente qué 20 columnas debe seleccionar para construir la capa `Gold` (Negocio) y `Diamond` (Feature Store definitivo), eliminando el ruido y la información basura para siempre.
