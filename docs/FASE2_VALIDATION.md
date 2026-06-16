# Fase 2: Validación de elt_pipeline_dag.py

## Paso 2.1 — Validación de elt_pipeline_dag.py

### ✅ Verificación Completada

El archivo `pipelines/dags/elt_pipeline_dag.py` ya existe y está correctamente implementado.

#### Configuración Verificada:

**1. CSV Ingester desde /opt/airflow/dataseed/**
```python
# Línea 25 en elt_pipeline_dag.py
source_path = f"/opt/airflow/data/seed/{filename}"
```
✅ Correcto - Lee desde la ruta especificada

**2. Destino S3: s3://kepler-bronze/financial/<dataset>/year=.../**
```python
# Línea 57 en pipelines/tasks/elt_tasks.py
s3_key = f"financial/{dataset_name}/year={year}/month={month}/day={day}/{dataset_name}_{date}.parquet"
```
✅ Correcto - Escribe al formato de particionamiento especificado

**3. Datasets Configurados:**
- `accounts.csv` → `financial/accounts/`
- `customers.csv` → `financial/customers/`
- API transactions → `financial/transactions/`
- API market_data → `financial/market_data/`
- App logs → `financial/app_logs/`

### Conclusión
No hay cambios necesarios. La implementación actual cumple con los requisitos de:
- ✅ Lectura desde `/opt/airflow/data/seed/`
- ✅ Escritura a `s3://kepler-bronze/financial/<dataset>/year=YYYY/month=MM/day=DD/`
- ✅ Formato Parquet para CSVs
- ✅ Formato JSON para APIs y logs

## Paso 2.2 — Disparar DAG desde Airflow UI

### Instrucciones:

1. **Abrir Airflow UI**
   ```
   http://<IP_AIRFLOW>:8080
   ```

2. **Buscar DAG**
   - Nombre: `kepler_elt_bronze_pipeline`
   - Estado: Debería estar visible en el DAG list

3. **Trigger DAG**
   - Click en el DAG name
   - Click en "Trigger DAG" botón (o icono de play)
   - Esperar a que complete (típicamente 5-10 min)

4. **Verificar resultado**
   ```bash
   # Listar lo que llegó a S3 kepler-bronze
   aws s3 ls s3://kepler-bronze/financial/ --recursive
   
   # Debería ver:
   # financial/application/year=2026/month=06/day=15/application_2026-06-15.parquet
   # financial/bureau/year=2026/month=06/day=15/bureau_2026-06-15.parquet
   # etc.
   ```

### Validación de Éxito
Si ves archivos Parquet en S3 → Fase 2 ✅
