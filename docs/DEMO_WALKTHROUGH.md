# Demo Walkthrough - Pipeline Completo

## Paso 8.1 — Ejecutar Pipeline Completo

### Terminal 1: Ver logs de Airflow
```bash
docker logs -f airflow-scheduler
```

### Terminal 2: Disparar elt_pipeline_dag
```bash
# Via API
curl -X POST http://localhost:8080/api/v1/dags/kepler_elt_bronze_pipeline/dagRuns \
  -H 'Content-Type: application/json' \
  -d '{"conf": {}}'

# O via Airflow UI: http://localhost:8080
# Buscar DAG: kepler_elt_bronze_pipeline
# Click en Trigger DAG
```

### Esperar ~5 minutos para que complete ELT

### Terminal 3: Disparar bronze_pipeline_dag
```bash
# Via API
curl -X POST http://localhost:8080/api/v1/dags/bronze_pipeline_dag/dagRuns \
  -H 'Content-Type: application/json' \
  -d '{"conf": {}}'

# O via Airflow UI: http://localhost:8080
# Buscar DAG: bronze_pipeline_dag
# Click en Trigger DAG
```

### Esperar ~10 minutos para procesamiento Spark

## Paso 8.2 — Verificaciones

### Datos llegaron a S3
```bash
# Listar archivos en S3 bronze
aws s3 ls s3://kepler-bronze/financial/ --recursive

# Listar archivos en S3 bronze-curated
aws s3 ls s3://kepler-bronze-curated/bronze/ --recursive

# Debería ver:
# financial/application/year=2026/month=06/day=15/application_2026-06-15.parquet
# financial/bureau/year=2026/month=06/day=15/bureau_2026-06-15.parquet
# bronze-curated/bronze/application/batch_id=.../...
# bronze-curated/bronze/bureau/batch_id=.../...
```

### PostgreSQL se llenó
```bash
# Conectar a PostgreSQL
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Ver logs de ingestión
SELECT * FROM control.ingesta_log ORDER BY ingestion_timestamp DESC LIMIT 5;

# Ver logs de bronze
SELECT * FROM control.bronze_log ORDER BY processing_timestamp DESC LIMIT 5;

# Contar registros por dataset
SELECT dataset_nombre, COUNT(*) as total 
FROM control.bronze_log 
GROUP BY dataset_nombre;
```

### Grafana muestra métricas
1. Ir a: http://localhost:3000
2. Login: admin / ${GRAFANA_PASSWORD}
3. Ver dashboard → panel de Spark jobs
4. Ver métricas de PostgreSQL

### Superset muestra data
1. Ir a: http://localhost:8088
2. Login: admin / ${SUPERSET_PASSWORD}
3. Ver Dashboards → chart de conteos
4. Ver métricas de ingestión y bronze

## Paso 8.3 — Validación Final

### Checklist de Validación
- [ ] elt_pipeline_dag completó exitosamente
- [ ] Archivos Parquet en s3://kepler-bronze/financial/
- [ ] bronze_pipeline_dag completó exitosamente
- [ ] Archivos Parquet en s3://kepler-bronze-curated/bronze/
- [ ] Registros en control.ingesta_log
- [ ] Registros en control.bronze_log
- [ ] Grafana muestra métricas de Spark
- [ ] Superset muestra visualizaciones de datos

## Troubleshooting

### DAG no aparece en Airflow UI
```bash
# Verificar que el archivo está en la carpeta dags
ls -la /path/to/airflow/dags/

# Reiniciar scheduler
docker restart airflow-scheduler
```

### Error de conexión S3
```bash
# Verificar variables de entorno
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
echo $S3_ENDPOINT

# Verificar configuración en Spark
# Revisar logs de Spark master
docker logs financial-risk-spark-master
```

### Error de conexión PostgreSQL
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep postgres

# Verificar credenciales
echo $POSTGRES_USER
echo $POSTGRES_PASSWORD
echo $POSTGRES_DB
```

### Spark job falla
```bash
# Ver logs de Spark master
docker logs financial-risk-spark-master

# Ver logs de Spark worker
docker logs financial-risk-spark-worker

# Verificar que el cluster Spark está accesible
curl http://localhost:8080
```
