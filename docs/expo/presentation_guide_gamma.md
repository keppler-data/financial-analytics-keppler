# Guía de Presentación: Arquitectura de Datos para Predicción de Riesgo Crediticio

*Nota: Copia y pega el contenido de este documento directamente en herramientas de IA generativa como **Gamma.app** o **NotebookLM** para que te armen las diapositivas de tu exposición automáticamente.*

---

## 1. Título de la Presentación
**Unificando el Riesgo Crediticio:** Construcción de un Data Lakehouse Automatizado e Impulsado por Machine Learning en AWS.

## 2. El Problema (Contexto del Negocio)
En el sector financiero, consolidar información sobre riesgo crediticio es una pesadilla. Tenemos 4 fuentes de datos masivas y completamente dispares (Home Credit, Lending Club, Give Me Some Credit, y Loan Prediction). Cada banco llama a sus variables de forma distinta, tiene millones de registros sucios, variables inútiles y valores nulos. 
**El Reto:** ¿Cómo unificamos esta data masiva en un solo modelo limpio para Business Intelligence (BI) y, al mismo tiempo, descubrimos cuáles son las variables que realmente predicen que un cliente no pague su préstamo (Default)?

## 3. La Solución Arquitectónica
Implementamos un **Data Lakehouse** usando arquitectura Medallion (Bronze, Silver, Gold + Diamond) completamente serverless en AWS (S3, Glue, Athena), orquestado por **Apache Airflow**, procesado por **PySpark** y modelado por **dbt**.

## 4. Fase 1: Ingesta Cruda (Capa Bronze)
* **¿Qué hicimos?** Extraer los datos originales desde las fuentes (APIs, sistemas legacy, Kaggle) y aterrizarlos de forma inmutable en un bucket de S3 en su formato original (CSV).
* **El Valor:** Se preserva la historia pura de los datos. Esta es la única fuente de la verdad inalterada de los 4 bancos.

## 5. Fase 2: Gobierno de Datos (Capa Silver)
* **¿Qué hicimos?** Desarrollamos un trabajo masivo en **PySpark** (`bronze_to_silver_transform.py`) que estandariza automáticamente la data.
* **Lógica Aplicada:**
  1. *Estandarización del Target:* Convertimos campos dispares como `loan_status` o `seriousdlqin2yrs` a una única bandera binaria universal: `is_default` (1 = Impago, 0 = Pagado).
  2. *Limpieza de Esquema:* Homologamos los nombres de las columnas a minúsculas y sin espacios.
  3. *Regla de Calidad Estricta:* El código escanea millones de filas y **elimina automáticamente** cualquier columna que tenga más del 80% de valores nulos, evitando basura analítica.
  4. *Salida:* Escribimos los datos en formato columnar `Parquet` para máxima compresión y velocidad.

## 6. Fase 3: Descubrimiento Impulsado por IA (PySpark ML)
* **¿Qué hicimos?** En lugar de que un humano intente adivinar cuáles de las cientos de columnas sirven, le delegamos la tarea a la Inteligencia Artificial.
* **Lógica Aplicada:**
  - Un job de Spark ML limpia los nulos restantes (imputando medianas y modas), indexa las cadenas de texto y entrena un **Random Forest Classifier**.
  - Este modelo no predice el futuro aún, sino que analiza qué variables pesan más matemáticamente.
  - El resultado: Exporta el **Top 20** de las características más importantes de cada banco a archivos JSON en S3.

## 7. Fase 4: Orquestación Híbrida (Python + dbt)
* **El Reto:** ¿Cómo pasamos las conclusiones de Machine Learning al equipo de bases de datos?
* **La Innovación:** Creamos un script orquestador (`run_dbt_with_ml_vars.py`) que lee los JSONs desde S3 y los inyecta dinámicamente como variables al motor de **dbt**. dbt ahora sabe exactamente qué columnas le importan a la IA.

## 8. Fase 5: El Destino Final (Capa Gold y Diamond en AWS Athena)
* **Capa Diamond (Feature Store):** dbt usa bucles *Jinja* para crear tablas ultraligeras que contienen únicamente las 20 columnas top de cada banco. Quedan listas para que el equipo de MLOps despliegue modelos a producción.
* **Capa Gold (Business Intelligence):** Implementamos un moderno **Modelo Copo de Nieve (Snowflake Schema)**.
  - *Tabla Central de Hechos (`fact_loan`):* Une los 4 bancos usando métricas maestras blindadas contra datos sucios (usando `try_cast()`).
  - *Dimensión Universal (`dim_customer`):* Atributos demográficos globales (Edad, Género).
  - *Dimensiones Satélite:* Tablas ancladas que preservan el 100% de la información cruda y particular de cada banco por si un analista necesita explorar por qué falló un crédito específico.

## 9. Conclusión y Siguientes Pasos
Logramos una arquitectura de datos moderna, completamente escalable. Si mañana la empresa compra un quinto banco, nuestro DAG de Airflow y los scripts dinámicos en PySpark y dbt lo procesarán, limpiarán, analizarán por IA y lo insertarán en el Copo de Nieve de forma 100% automatizada. El siguiente paso natural es conectar Power BI a Athena para explotar visualmente esta mina de oro.
