# Architecture Overview

## System Architecture

```
                    ┌─────────────────────┐
                    │   Data Sources      │
                    │  (APIs, DBs, Logs)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  BRONZE LAYER       │ ← Raw data ingestion
                    │  (Parquet + S3)     │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┴────────────────────┐
          │                                         │
    ┌─────▼────────┐                      ┌────────▼─────┐
    │ SILVER LAYER │                      │  ELT via     │
    │ (Cleaning +  │◄────────────────────►│  Spark Jobs  │
    │ Enrichment)  │                      │              │
    └─────┬────────┘                      └────────┬─────┘
          │                                        │
    ┌─────▼──────────────┐                       │
    │ INTERMEDIATE LAYER │◄──────────────────────┘
    │ (Business Logic)   │
    └─────┬──────────────┘
          │
    ┌─────▼──────────────┐
    │ GOLD LAYER         │
    │ (Marts + Analytics)│
    └─────┬──────────────┘
          │
    ┌─────▼──────────────────────────────────┐
    │ DIAMOND LAYER (Convergence)            │
    │ ├─ Unified Risk Profile                │
    │ ├─ Executive Dashboards                │
    │ ├─ Semantic Layer                      │
    │ └─ Federated Query Engine              │
    └────────────────────────────────────────┘
           │
    ┌──────┴──────────────────────────────────┐
    │ Consumption Layer                        │
    │ ├─ Power BI / Dashboards               │
    │ ├─ APIs (Risk, Fraud, Metrics)        │
    │ ├─ ML/Analytics Platforms              │
    │ └─ Exports (CSV, Parquet, Reports)    │
    └──────────────────────────────────────────┘
```

## Components Overview

### 1. Data Ingestion (Bronze Layer)
- **Sources**: CRM, APIs, Financial transactions, Bureau data
- **Technologies**: Python, Pandas, PySpark
- **Storage**: AWS S3, Parquet format
- **Key Features**:
  - Raw data capture with audit trails
  - Schema registry for structure control
  - Data validation at ingestion

### 2. Data Transformation
- **Silver Layer**: Cleaning, deduplication, standardization
  - Remove nulls, handle duplicates
  - Data type standardization
  - Temporal alignment
  - Enrichment with reference data
  
- **Intermediate Layer**: Business logic and features
  - Complex joins and aggregations
  - Risk signal generation
  - Customer journey construction
  - Behavioral feature engineering
  
- **Gold Layer**: Analytics-ready marts
  - Corporate KPIs
  - Financial marts
  - Risk assessment marts
  - Ready for consumption

### 3. Convergence (Diamond Layer)
Unified layer combining ETL and ELT results:
- Consolidated risk profiles
- Executive dashboards
- Semantic views
- Federated query support

### 4. Orchestration & Scheduling
- **Airflow**: Workflow orchestration
  - DAG scheduling
  - Task dependencies
  - Monitoring and alerts
  
- **Celery**: Distributed task queue
  - Worker pool management
  - Queue-based routing
  - Task retry logic

### 5. Processing Engines
- **Spark**: Large-scale distributed processing
  - ELT jobs for massive datasets
  - Interactive analytics
  - Machine learning pipelines
  
- **dbt**: SQL-based transformation
  - Version-controlled SQL
  - Incremental models
  - Data tests and documentation

### 6. Governance & Quality
- **Data Contracts**: Schema validation
- **Great Expectations**: Quality checks
- **Lineage Tracking**: Data provenance
- **Catalog**: Data discovery
- **Policies**: Access control and compliance

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Apache Airflow 2.7 | Workflow scheduling |
| **Task Queue** | Celery | Distributed tasks |
| **Message Broker** | RabbitMQ | Task queueing |
| **Processing** | Apache Spark 3.5 | Distributed computing |
| **Transformation** | dbt 1.7 | SQL transformations |
| **Storage** | AWS S3 | Data lake |
| **Query** | DuckDB, Trino, Athena | Analytics queries |
| **Database** | PostgreSQL 15 | Metadata & OLTP |
| **Containerization** | Docker | Application packaging |
| **IaC** | Terraform | Infrastructure automation |

## Data Flow

### ETL Pipeline (Batch Processing)
```
Source Systems → Airflow DAG
                    ↓
            Python Extract Tasks
                    ↓
            Bronze (Raw Data)
                    ↓
            Silver (Clean Data)
                    ↓
            Intermediate (Business Logic)
                    ↓
            Gold (Analytics)
```

### ELT Pipeline (Distributed Processing)
```
Source Systems → Airflow DAG
                    ↓
            Spark Job Submission
                    ↓
            Bronze (Raw Data)
                    ↓
            Spark Transform
                    ↓
            Silver → Intermediate → Gold
```

## Key Processes

### 1. Daily Data Ingestion
- 6 AM UTC: Bronze layer ingestion
- 8 AM UTC: Spark transformations start
- 10 AM UTC: dbt models execute
- 11 AM UTC: Diamond layer convergence
- 12 PM UTC: Quality checks and SLA validation

### 2. Quality Assurance
- Schema validation on ingestion
- Data completeness checks
- Duplicate detection
- Anomaly detection
- Referential integrity

### 3. Monitoring & Alerting
- Real-time pipeline monitoring
- SLA tracking
- Data freshness validation
- Performance metrics
- Cost tracking

## Scalability Considerations

- **Horizontal Scaling**: Add Spark workers for processing
- **Concurrency**: Multiple DAGs and tasks in parallel
- **Partitioning**: Data partitioned by date and customer
- **Caching**: Materialized views in Gold layer
- **Compression**: Parquet with snappy compression

## Security & Compliance

- IAM-based access control
- Encryption at rest (S3, RDS)
- Encryption in transit (SSL/TLS)
- Audit logging
- Data masking for sensitive fields
- GDPR/regulatory compliance

## Disaster Recovery

- Daily automated backups
- Multi-AZ RDS deployment
- S3 versioning
- Terraform state management
- Documented runbooks

## Performance Optimization

- Adaptive Query Execution (Spark)
- Columnar storage (Parquet)
- Partition pruning
- Cost-based optimization
- Query result caching

---

See related documents:
- [ETL Flow](etl_flow.md)
- [ELT Flow](elt_flow.md)
- [Diamond Layer](diamond_layer.md)
- [Governance Framework](governance.md)
