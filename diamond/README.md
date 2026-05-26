# Diamond Layer

## Overview

The Diamond layer represents the convergence point of ETL and ELT processes in the financial risk lakehouse. It combines unified data contracts, consolidated KPIs, and semantic layers to provide a single source of truth for business decisions.

## Architecture

```
Diamond Layer
├── Unified Models (ETL + ELT convergence)
├── Corporate KPIs (aggregated metrics)
├── Semantic Layer (executive views)
└── Query Engine (federated query support)
```

## Key Components

### 1. Contracts (`contracts/`)
- **unified_risk.yml** - Unified risk assessment contract
- **unified_customer.yml** - Customer profile contract
- **unified_portfolio.yml** - Portfolio management contract
- **unified_collections.yml** - Collections data contract

### 2. Models (`models/`)

#### Unified Models
- `unified_client_risk.sql` - Consolidated client risk profile
- `unified_portfolio.sql` - Complete portfolio view
- `unified_collections.sql` - Collections management unified view
- `unified_fraud_profile.sql` - Fraud risk assessment

#### Corporate KPIs
- `kpi_default_rate.sql` - Default rate metrics
- `kpi_fraud_index.sql` - Fraud index calculations
- `kpi_collection_efficiency.sql` - Collection efficiency metrics
- `kpi_approval_quality.sql` - Approval quality KPIs
- `kpi_segment_loss.sql` - Segment loss analysis

#### Semantic Layer
- `executive_views.sql` - Executive dashboards
- `finance_views.sql` - Financial analytics
- `risk_views.sql` - Risk assessment views
- `operational_views.sql` - Operational metrics

### 3. Query Engine (`query_engine/`)

Supports multiple query engines:
- **DuckDB** - Local analytics
- **Trino** - Distributed queries
- **AWS Athena** - Serverless queries
- **Federated Queries** - Cross-data source

### 4. Lineage Tracking (`lineage/`)

Tracks data lineage from:
- Bronze → Silver → Intermediate → Gold
- ETL processes (Python)
- ELT processes (Spark)
- Convergence in Diamond

### 5. Monitoring (`monitoring/`)

- Data freshness
- Quality metrics
- SLA compliance
- Anomaly detection

### 6. Tests (`tests/`)

- `test_unified_risk.sql` - Risk model validation
- `test_kpi_consistency.sql` - KPI consistency checks
- `test_referential_integrity.sql` - Referential integrity

## Development Guide

### Creating a New Unified Model

```sql
-- models/unified/new_unified_model.sql
{{ config(
    materialized='table',
    indexes=[
        {'columns': ['client_id'], 'unique': False},
    ],
    contract={
        "enforced": true,
    }
) }}

WITH etl_source AS (
    SELECT * FROM {{ ref('gold_etl_source') }}
),

elt_source AS (
    SELECT * FROM {{ ref('gold_elt_source') }}
),

unified AS (
    SELECT 
        COALESCE(etl_source.id, elt_source.id) as id,
        -- Unified columns here
    FROM etl_source
    FULL OUTER JOIN elt_source 
        ON etl_source.id = elt_source.id
)

SELECT * FROM unified
```

### Data Contract Example

```yaml
# contracts/unified_custom_contract.yml
version: 2

models:
  - name: unified_model
    contract:
      enforced: true
    columns:
      - name: id
        data_type: string
        constraints:
          - type: not_null
          - type: unique
      - name: value
        data_type: decimal(18,2)
        constraints:
          - type: not_null
```

## Performance Considerations

- Use appropriate materialization (table vs. incremental)
- Create indexes on frequently filtered columns
- Leverage partitioning for large tables
- Consider federated query pushdown

## SLA Requirements

- **Data Freshness**: Daily updates by 6 AM
- **Query Performance**: < 5 seconds for 99th percentile
- **Availability**: 99.9% uptime
- **Data Completeness**: 100% for critical metrics

## Related Documentation

- [Architecture Overview](../docs/architecture/overview.md)
- [Data Contracts](../docs/architecture/governance.md)
- [Query Engine Guide](query_engine/README.md)

## Support

For issues or questions, contact the Data Platform team.
