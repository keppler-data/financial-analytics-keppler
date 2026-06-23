# Guion de Demostración — Caso 5

> **Duración total estimada:** 23 minutos  
> **Público:** Evaluadores / tribunal de sustentación  
> **Preparación previa:** Tener abierta la terminal en el servidor EC2, el navegador con las pestañas de Airflow y Grafana, y los archivos de reporte listos para abrir.

---

## 1. Contexto del Caso (2 min)

### Qué decir

> "Buenos días. Voy a presentar el Caso 5: Descontrol Operacional y Riesgo Crediticio.
>
> El contexto es el siguiente: una entidad financiera digital que ofrece préstamos y microcréditos en Latinoamérica enfrenta una crisis operativa. Tienen **aumento en incumplimientos de pago**, **crecimiento de cartera vencida**, **posibles fraudes de identidad** y lo más preocupante: **están aprobando créditos a clientes de alto riesgo** porque no tienen una visión unificada del cliente.
>
> La información está dispersa: los datos de la solicitud están en un sistema, el historial de pagos en otro, el buró de crédito en un tercero. No hay una fuente única de verdad.
>
> Nuestro objetivo fue construir una **plataforma de datos end-to-end** que centralice esa información, la limpie, la enriquezca con métricas de comportamiento financiero, y genere un modelo de scoring crediticio que segmenta a los clientes en riesgo bajo, medio y alto.
>
> Todo esto orquestado con Airflow, monitoreado con Prometheus y Grafana, y listo para consumir en Power BI."

### Comandos / acciones

- Mostrar el README del proyecto si se necesita referencia rápida.
- **No abrir nada todavía** — esta sección es puramente narrativa.

---

## 2. Arquitectura de la Solución (3 min)

### Qué decir

> "La plataforma sigue la **Medallion Architecture**, un patrón que organiza los datos en capas de madurez progresiva.
>
> Empezamos en **Seed**, que son los 7 CSVs descargados de Kaggle. La primera capa del pipeline es **Bronze**, donde hacemos una copia fiel de los datos crudos con metadata de auditoría: cuándo se ingirió, de qué archivo proviene, y un hash de cada fila para detectar duplicados.
>
> Luego pasa a **Silver**, donde limpiamos los datos: tipado explícito, deduplicación por clave primaria, y corrección de anomalías como el valor centinela de DAYS_EMPLOYED que representa mil años de empleo.
>
> De ahí vamos a **Intermediate**, que es donde está el valor diferenciador del proyecto. Construimos 6 tablas de agregación que responden preguntas de negocio: ¿cómo paga este cliente? ¿cuántos créditos tiene en el buró? ¿cuál es su comportamiento con la tarjeta de crédito?
>
> Todo esto confluye en **Gold Customer 360**: una vista unificada por cliente con 80+ columnas y una segmentación de riesgo.
>
> Sobre Gold corremos un **modelo de scoring** que predice la probabilidad de default y genera predicciones para todos los clientes.
>
> Finalmente, todo se monitorea con **Prometheus y Grafana**, y los resultados se exportan a **Power BI**."

### Arquitectura a mostrar

Mostrar el diagrama de arquitectura del archivo `docs/final/architecture.md` o dibujar en pizarra:

```
SEED → BRONZE → SILVER → INTERMEDIATE → GOLD → QUALITY → SCORING → POWER BI
                                                    ↕
                                              PROMETHEUS + GRAFANA
```

### Comandos / acciones

- Si se proyecta la presentación, tener la diapositiva de arquitectura lista.
- Señalar cada capa y su propósito.

---

## 3. Infraestructura (2 min)

### Qué decir

> "La infraestructura está desplegada en una **instancia EC2 de AWS** usando **Docker Compose**. Tenemos 7 servicios corriendo:
>
> - **PostgreSQL** como base de datos de metadatos de Airflow.
> - **RabbitMQ** como broker de mensajes para el executor Celery.
> - **Airflow Master** con scheduler, API server, DAG processor, triggerer y Flower para monitoreo de workers.
> - **Airflow Worker** que ejecuta las tareas del pipeline.
> - **Spark** en modo standalone, disponible para transformaciones pesadas.
> - **Nginx Proxy Manager** que expone todos los servicios de forma segura con SSL.
> - **Prometheus y Grafana** para monitoreo.
>
> Vamos a verificar que todos los servicios están corriendo:"

### Comandos para ejecutar

```bash
# Ver todos los contenedores Docker corriendo
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Salida esperada:**

```
NAMES                    STATUS              PORTS
airflow-master-1         Up 2 hours          0.0.0.0:8080->8080/tcp
airflow-worker-1         Up 2 hours          ...
db-1                     Up 3 hours          5432/tcp
rabbitmq-1               Up 3 hours          5672/tcp, 15672/tcp
proxy-1                  Up 3 hours          0.0.0.0:80->80/tcp
prometheus-1             Up 3 hours          9090/tcp
grafana-1                Up 3 hours          3000/tcp
spark-master-1           Up 3 hours          8081/tcp
```

### Qué decir al ver la salida

> "Como pueden ver, los 7 servicios están activos. El Airflow Master expone el puerto 8080, Nginx Proxy el 80, Grafana el 3000 y Spark el 8081. Todos comunicados internamente a través de la red Docker."

---

## 4. Demo del Pipeline en Airflow (5 min)

### Qué decir

> "Ahora vamos a la parte central: el pipeline orquestado con Airflow 3.x.
>
> Este es el DAG `case_5_financial_risk_pipeline`. Tiene **7 tareas secuenciales**: ingesta Bronze, transformación Silver, agregaciones Intermediate, consolidación Gold, reporte de calidad, modelo de scoring y un resumen final.
>
> Cada tarea depende de la anterior. Si Bronze falla, Silver no se ejecuta. Esto garantiza la integridad del flujo de datos.
>
> Vamos a hacer un trigger manual para que vean el pipeline en acción:"

### Comandos / acciones

**Paso 1:** Abrir Airflow en el navegador.

```bash
# Abrir Airflow (vía Nginx Proxy si está configurado, o directo)
# http://IP_SERVIDOR/airflow   o   http://IP_SERVIDOR:8080
```

**Paso 2:** Navegar al DAG.

1. En el menú lateral, hacer clic en **DAGs**.
2. Buscar `case_5_financial_risk_pipeline`.
3. Verificar que el estado del último run sea "success" (si ya se ejecutó antes).

**Paso 3:** Trigger manual.

1. Hacer clic en el botón **"Trigger DAG"** (triángulo de play).
2. Cambiar a la vista **"Graph"** para ver el flujo de tareas.
3. Observar cómo las tareas pasan de gris a amarillo (running) a verde (success) secuencialmente.

### Qué decir durante la ejecución

> "Pueden ver las tareas ejecutándose secuencialmente. La primera es `ingest_bronze`, que lee los 7 CSVs y los convierte a Parquet. Ahora está en `transform_silver`, que aplica limpieza y tipado.
>
> Fíjense que cada tarea muestra su duración. `ingest_bronze` tarda aproximadamente X segundos, `transform_silver` unos Y segundos. Los tiempos se registran en los logs y están disponibles en Prometheus."

**Paso 4:** Revisar XCom (intercambio de datos entre tareas).

1. Ir a la pestaña **"XCom"** del último DAG run exitoso.
2. Mostrar los resultados de cada tarea.

### Comandos / acciones (XCom)

```bash
# Ver los XCom del último run (desde la UI de Airflow)
# DAG → case_5_financial_risk_pipeline → último DAG run → XCom

# O desde la terminal del servidor:
docker exec airflow-master-1 airflow dags list-runs -d case_5_financial_risk_pipeline
```

### Qué decir al ver los XCom

> "Aquí vemos los resultados de cada tarea. `ingest_bronze` retorna la cantidad de filas por dataset. `transform_silver` retorna cuántos duplicados se eliminaron y cuántos nulos se imputaron. `build_gold` retorna la distribución de segmentos de riesgo. Todos estos resultados se consolidan en la tarea `pipeline_summary`."

---

## 5. Resultados: Datos (3 min)

### Qué decir

> "Ahora veamos los resultados concretos. Vamos a revisar los datos generados en cada capa del lakehouse.
>
> Empecemos por Bronze:"

### Comandos para ejecutar

```bash
# Ver la estructura de datos generada
tree data/ -L 2 --du -h
```

**Salida esperada (resumida):**

```
data/
├── bronze/          850M
│   ├── application_train/    → 307,511 filas
│   ├── bureau/               → 1,716,428 filas
│   ├── bureau_balance/       → 27,299,925 filas
│   ├── previous_application/ → 1,670,214 filas
│   ├── installments_payments/→ 13,605,401 filas
│   ├── credit_card_balance/  → 3,840,313 filas
│   └── POS_CASH_balance/     → 10,001,358 filas
├── silver/          720M
│   └── [7 datasets limpiados]
├── intermediate/    45M
│   ├── agg_customer_installment_history/
│   ├── fct_customer_payment_behavior_features/
│   ├── agg_customer_bureau_history/
│   ├── agg_previous_application_history/
│   ├── agg_credit_card_behavior/
│   └── agg_pos_cash_behavior/
└── gold/            180M
    └── gold_customer_360/
```

### Conteo de filas por capa

```bash
# Contar filas en cada capa (usando Python)
python3 -c "
import pandas as pd
import os

for layer in ['bronze', 'silver', 'intermediate', 'gold']:
    path = f'data/{layer}'
    if not os.path.exists(path):
        continue
    print(f'\n=== {layer.upper()} ===')
    for ds in sorted(os.listdir(path)):
        ds_path = os.path.join(path, ds)
        if os.path.isdir(ds_path):
            for f in os.listdir(ds_path):
                if f.endswith('.parquet'):
                    df = pd.read_parquet(os.path.join(ds_path, f))
                    print(f'  {ds}: {len(df):,} filas × {len(df.columns)} columnas')
                    break
"
```

### Qué decir al ver los resultados

> "Bronze tiene ~58 millones de registros en total, almacenados como Parquet con compresión Snappy. Los archivos son 3-5 veces más pequeños que los CSVs originales.
>
> Silver tiene la misma cantidad de filas pero menos columnas nulas y sin duplicados.
>
> Intermediate tiene 6 tablas con una fila por cliente (~305K cada una). Aquí está la inteligencia de negocio: pagos atrasados, consistencia de pago, deudas en el buró.
>
> Gold Customer 360 tiene ~307,511 filas con 80+ columnas. Cada fila es un cliente con su perfil completo."

---

## 6. Resultados: Calidad (2 min)

### Qué decir

> "Un componente clave de la plataforma es el reporte de calidad de datos. Este módulo perfila automáticamente cada dataset en cada capa y genera dos reportes: uno visual en HTML y otro estructurado en JSON.
>
> Vamos a abrir el reporte HTML:"

### Comandos / acciones

```bash
# Abrir el reporte HTML (si hay acceso a navegador en el servidor)
# O copiarlo localmente y abrir:
# scp user@IP_SERVIDOR:/opt/keppler/data-platform/reports/data_quality_report.html ./

# Ver la ruta del reporte
ls -la reports/data_quality_report.html reports/data_quality_summary.json
```

**Paso 2:** Abrir el archivo HTML en el navegador.

### Qué decir al ver el reporte

> "El reporte muestra un score de calidad por dataset. El rango es 0 a 100, donde verde es ≥80, amarillo es 50-79 y rojo es <50.
>
> Pueden ver que la capa Bronze tiene scores altos (~92 para application_train) porque los datos de Kaggle están relativamente limpios. La capa Silver mantiene o mejora el score tras la limpieza. La capa Intermediate tiene scores cercanos a 100 porque los datos agregados no tienen nulos.
>
> Este reporte se genera automáticamente como parte del pipeline y queda disponible para auditoría."

### Comandos adicionales (JSON)

```bash
# Ver el resumen del JSON rápidamente
python3 -c "
import json
with open('reports/data_quality_summary.json') as f:
    r = json.load(f)
print('Datasets evaluados:', r['summary']['total_datasets'])
print('Score promedio:', r['summary']['avg_quality_score'])
print('Score mínimo:', r['summary']['min_quality_score'])
print('Score máximo:', r['summary']['max_quality_score'])
"
```

---

## 7. Resultados: Scoring (3 min)

### Qué decir

> "Llegamos al corazón del proyecto: el modelo de scoring crediticio.
>
> Entrenamos dos modelos — Logistic Regression y Random Forest — sobre la tabla Gold Customer 360 usando 29 features numéricas. Seleccionamos el mejor modelo según AUC-ROC.
>
> Veamos las métricas:"

### Comandos para ejecutar

```bash
# Ver métricas del modelo
python3 -c "
import json
with open('reports/model_metrics.json') as f:
    m = json.load(f)
print(f'Mejor modelo: {m[\"best_model\"]}')
print(f'AUC-ROC: {m[\"best_auc\"]}')
print(f'Features usadas: {m[\"features_used\"]}')
print(f'Filas train: {m[\"training_rows\"]:,}')
print(f'Filas test: {m[\"test_rows\"]:,}')
print()
for name, metrics in m['models'].items():
    print(f'{name}:')
    print(f'  AUC: {metrics[\"auc_roc\"]} | Acc: {metrics[\"accuracy\"]} | F1: {metrics[\"f1_score\"]}')
    print(f'  Precision: {metrics[\"precision\"]} | Recall: {metrics[\"recall\"]}')
print()
print('Segmentación de riesgo:')
for seg, count in m['risk_segmentation'].items():
    print(f'  {seg}: {count:,} clientes ({count/sum(m[\"risk_segmentation\"].values())*100:.1f}%)')
"
```

### Qué decir al ver las métricas

> "El mejor modelo obtiene un AUC-ROC de X.XX. Esto significa que el modelo puede distinguir entre clientes que pagan y que no pagan en el X% de los casos. Para un baseline sin optimización de hiperparámetros, es un resultado razonable.
>
> La segmentación de riesgo muestra que el Y% de los clientes son de bajo riesgo, Z% son de riesgo medio y W% son de alto riesgo. Estos segmentos alimentan directamente las decisiones de aprobación de créditos."

### Comandos: Importancia de features

```bash
# Ver top 10 features más importantes
head -11 reports/model_feature_importance.csv
```

### Qué decir al ver la importancia

> "Las features más importantes son las fuentes externas `EXT_SOURCE_1/2/3`, que son scores de riesgo pre-calculados por agencias externas. Les siguen el score de consistencia de pago y los días de atraso máximo, que son métricas que construimos en la capa Intermediate.
>
> Esto valida que nuestra ingeniería de características aporta valor predictivo real."

### Comandos: CSV para Power BI

```bash
# Ver el CSV exportado para Power BI
head -3 reports/gold_customer_360_for_powerbi.csv
wc -l reports/gold_customer_360_for_powerbi.csv
```

### Qué decir

> "Finalmente, generamos este CSV listo para Power BI con las columnas clave: ID del cliente, variable objetivo, segmentos de riesgo, probabilidad de default, ingresos, crédito, score de consistencia. Este archivo se conecta directamente al connector de archivos de Power BI."

---

## 8. Monitoreo (2 min)

### Qué decir

> "La última pieza de la plataforma es el monitoreo. Usamos Prometheus y Grafana para observar el estado del pipeline en tiempo real.
>
> Prometheus se conecta al endpoint de métricas de Airflow cada 15 segundos y almacena series temporales. Grafana consume esas métricas y las presenta en dashboards."

### Comandos / acciones

**Paso 1:** Abrir Grafana en el navegador.

```bash
# Acceder a Grafana
# http://IP_SERVIDOR/grafana   o   http://IP_SERVIDOR:3000
# Credenciales: admin / admin
```

**Paso 2:** Navegar al dashboard del pipeline.

1. Hacer clic en **Dashboards** → seleccionar el dashboard "Pipeline Health" o "Airflow".
2. Mostrar los paneles: estado del DAG, duración de tareas, cola Celery.

### Comandos adicionales (Prometheus)

```bash
# Verificar que Prometheus está scrapeando Airflow
# Acceder a: http://IP_SERVIDOR:9090
# Query: airflow_dag_run_duration_seconds
```

### Qué decir al ver los dashboards

> "Aquí podemos ver el estado del último DAG run (éxito/fallo), la duración de cada tarea para identificar cuellos de botella, y la cola de tareas de Celery que indica si hay trabajos acumulados.
>
> En un escenario de producción, configuraríamos alertas automáticas: por ejemplo, si el AUC del modelo cae por debajo de 0.65, o si una tarea falla 3 veces consecutivas, se envía una notificación a Slack o correo."

---

## 9. Power BI (2 min)

### Qué decir

> "El consumidor final de los datos es Power BI, donde los analistas de negocio construyen dashboards interactivos para la toma de decisiones.
>
> Nuestra plataforma genera un CSV optimizado con las columnas necesarias. La conexión a Power BI es directa:"

### Cómo se conectaría Power BI

1. **Power BI Desktop → Obtener datos → Archivo de texto/CSV.**
2. Seleccionar `gold_customer_360_for_powerbi.csv`.
3. Power BI detecta automáticamente los tipos de columnas.
4. Construir visualizaciones:
   - **Mapa de dispersión:** probabilidad de default vs ingreso, coloreado por segmento de riesgo.
   - **Gráfico de barras:** distribución de segmentos de riesgo.
   - **Tabla:** top 10 clientes de mayor riesgo con sus métricas.
   - **KPIs:** total de clientes, porcentaje de alto riesgo, AUC del modelo.

### Qué decir

> "Con este CSV, un analista puede construir un dashboard que muestre la distribución de riesgo de la cartera, identificar los clientes más riesgosos y tomar decisiones de aprobación informadas. El CSV se actualiza cada vez que el pipeline se ejecuta, por lo que el dashboard siempre refleja los datos más recientes."

---

## 10. Cierre (2 min)

### Qué decir

> "Para cerrar, les presento un resumen de lo que logramos y lo que queda por hacer.
>
> **Logros principales:**
> - Pipeline end-to-end funcional con 6 capas de datos (Bronze, Silver, Intermediate, Gold, Quality, Scoring).
> - Orquestación con Airflow 3.x y ejecución distribuida con Celery + RabbitMQ.
> - 6 tablas de agregación de comportamiento financiero que enriquecen significativamente el perfil del cliente.
> - Modelo baseline de scoring con AUC competitivo y segmentación de riesgo en tres niveles.
> - Infraestructura monitoreada con Prometheus y Grafana.
> - Datos listos para consumo en Power BI.
>
> **Limitaciones reconocidas:**
> - Transformaciones en Pandas en lugar de Spark (adecuado para el volumen actual, pero no escalable a cientos de millones de filas).
> - Modelo baseline sin optimización de hiperparámetros (hay margen de mejora con XGBoost y búsqueda de hiperparámetros).
> - Ingesta manual de datos (sin conectores a APIs o bases de datos operativas).
>
> **Próximos pasos:**
> - Migrar a XGBoost/LightGBM con optimización bayesiana de hiperparámetros (Optuna).
> - Implementar Feature Store con Feast para gestión centralizada de features.
> - Integrar dbt para transformaciones SQL declarativas.
> - Automatizar la ingesta desde APIs de la entidad financiera.
> - Configurar alertas en Grafana para monitoreo proactivo.
>
> Muchas gracias. Quedo a disposición para preguntas."

---

## Checklist de Preparación (antes de la demo)

- [ ] Todos los servicios Docker corriendo (`docker ps`)
- [ ] DAG `case_5_financial_risk_pipeline` visible en Airflow UI
- [ ] Último DAG run exitoso (o listo para trigger)
- [ ] Archivos Parquet generados en `data/bronze`, `data/silver`, `data/intermediate`, `data/gold`
- [ ] Reporte HTML de calidad accesible (`reports/data_quality_report.html`)
- [ ] Métricas del modelo generadas (`reports/model_metrics.json`)
- [ ] CSV para Power BI generado (`reports/gold_customer_360_for_powerbi.csv`)
- [ ] Grafana accesible y dashboard configurado
- [ ] Terminal abierta con `cd /opt/keppler/data-platform`
- [ ] Navegador con pestañas de Airflow y Grafana listas
- [ ] Los 7 CSVs en `data/seed/` (verificar que no se borraron)
