========================================================================================================================
                                     KEPLER LAKEHOUSE - DATA LINEAGE MAP
========================================================================================================================

 [ Capa BRONZE ] (Ingesta RAW / S3 Landing)
    ├── transactional_db.customers_raw ────────────────┐
    ├── transactional_db.loans_raw ────────────────────┼┐ (Ingesta CDC / Batch Diaria)
    └── external_bureau_api.bureau_data_raw ───────────┼┼┐
                                                       │││
 [ Capa SILVER ETL ] (Limpieza, Tipado y Dimensionamiento) │││
    ├── dim_customers (S3 Parquet / Delta) <────────────┘││
    └── fct_loans (S3 Parquet / Delta) <─────────────────┘│
                                                          │
 [ Capa SILVER ELT ] (Históricos estructurados de eventos)│
    └── installment_history (S3 Delta) <──────────────────┘
            │
            ▼
 [ Capa INTERMEDIATE ELT ] (Agregaciones Temporales e Ingeniería de Variables - PySpark)
    ├── agg_customer_installment_history (Partitioned by customer_id & period) ──┐
    ├── fct_customer_payment_behavior_features (Métricas móviles 3M, 6M, 12M) ────┼─┐ (Window Functions)
    └── agg_customer_bureau_history (Tendencias de Score Externo) ──────────────┼─┼┐
                                                                                  │││
                                                                                  ▼▼▼
 [ Capa GOLD ] (Modelado dbt / Consolidación de Negocio - PostgreSQL & S3 Athena)
    └── gold_customer_360 (Vista Unificada de Verdad Financiera)
========================================================================================================================

# 📘 Gobierno de Datos y Catálogo de Linaje - Kepler Lakehouse

Este directorio contiene los artefactos estructurales generados bajo la tarea **SCRUM-92** por Hugo Pérez (ELT P2), enfocados en documentar la trazabilidad completa del flujo de datos de la Fintech.

## 🔗 dbt Docs como Referencia Suplementaria
Para consultar de forma interactiva el grafo de dependencias dirigidas (DAG), descripciones de columnas secundarias y los metadatos de compilación del motor dbt, ejecute los siguientes comandos locales en su entorno:

```bash
# Generar el catálogo dinámico basado en los archivos manifest.json y catalog.json
uv run dbt docs generate

# Levantar el servidor web local interactivo de documentación de datos
uv run dbt docs serve --port 8080