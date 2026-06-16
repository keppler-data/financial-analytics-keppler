# Apache Superset Setup Guide

## Paso 7.1 — Levantar Superset

```bash
# Ejecutar contenedor de Superset
docker run -d \
  --name superset \
  -p 8088:8088 \
  -e SUPERSET_LOAD_EXAMPLES=yes \
  apache/superset:latest

# Esperar a que inicie (aprox 2-3 minutos)
# Crear admin user
docker exec superset superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@superset.local \
  --password ${SUPERSET_PASSWORD}

# Inicializar Superset
docker exec superset superset init
```

## Paso 7.2 — Conectar a PostgreSQL

1. Abrir http://localhost:8088
2. Login con: admin / ${SUPERSET_PASSWORD}
3. Ir a: Settings → Database Connections → Add
4. Configurar:
   - **Engine**: postgresql
   - **Connection String**: `postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}`
5. Test Connection → Save

## Paso 7.3 — Crear Chart

1. Ir a: Datasets → New Dataset
2. Seleccionar: `control.bronze_log` table
3. Create Chart → Bar Chart
4. Configurar:
   - **Dimensions**: dataset_nombre
   - **Metrics**: COUNT(*) (registros procesados)
5. Save Dashboard

## Paso 7.4 — Crear Dashboard Adicional

### Métricas de Ingesta
1. Dataset: `control.ingesta_log`
2. Chart Type: Line Chart
3. Dimensions: ingestion_timestamp
4. Metrics: SUM(registro_count)
5. Time range: Last 7 days

### Métricas de Bronze
1. Dataset: `control.bronze_log`
2. Chart Type: Table
3. Columns: batch_id, dataset_nombre, input_count, output_count, status
4. Sort by: processing_timestamp DESC
