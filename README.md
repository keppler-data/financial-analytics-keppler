# Financial Risk Data Platform

## Overview

Financial Risk Data Platform is a modern Data Engineering, Analytics Engineering, and Machine Learning platform designed to support credit risk analysis, decision intelligence, and analytical reporting.

The platform follows a layered architecture that separates data ingestion, transformation, analytical modeling, and machine learning workloads while maintaining scalability, maintainability, and clear ownership across teams.

This repository contains only data processing logic.

Infrastructure components such as PostgreSQL, RabbitMQ, Spark deployment, Airflow deployment, networking, and monitoring are managed in a separate infrastructure repository.

---

# Platform Architecture

```text
Data Sources
      │
      ▼
  Ingestion
      │
      ▼
   Staging
      │
      ▼
 Intermediate
      │
      ▼
    Marts
      │
      ▼
   Diamond
      │
      ├── Feature Store
      ├── Risk Scoring
      ├── Analytics
      └── Serving Layer
      │
      ▼
 Machine Learning
```

---

# Repository Structure

```text
financial-risk-data-platform
│
├── airflow/
├── common/
├── diamond/
├── docs/
├── governance/
├── ingestion/
├── integrations/
├── intermediate/
├── marts/
├── ml/
├── quality/
├── staging/
└── tests/
```

---

# Layer Responsibilities

## Airflow

Responsible for workflow orchestration.

Contains:

* DAGs
* Tasks
* Operators
* Hooks
* Sensors

Airflow coordinates ingestion, transformation, validation, and machine learning workflows.

---

## Ingestion

Responsible for acquiring data from source systems.

Examples:

* Home Credit Risk datasets
* External APIs
* Batch files
* Third-party providers

Responsibilities:

* Data extraction
* Schema validation
* Landing zone loading
* Metadata registration

---

## Staging

Represents the initial processing layers of the platform.

### Bronze Layer

Stores raw source data with minimal modifications.

Responsibilities:

* Raw data persistence
* Historical retention
* Source traceability

### Silver Layer

Stores standardized and cleaned datasets.

Responsibilities:

* Data cleansing
* Data typing
* Standardization
* Deduplication

---

## Intermediate

Business transformation layer.

Responsibilities:

* Business rules implementation
* Data enrichment
* Aggregations
* Derived calculations
* Cross-domain joins

Examples:

* Customer financial profiles
* Payment behavior indicators
* Credit risk attributes

---

## Marts

Analytics Engineering layer.

Contains dimensional models and business-oriented analytical assets.

Responsibilities:

* Star schema implementation
* Fact tables
* Dimension tables
* Subject-oriented data marts

### Finance Mart

Examples:

* Fact Loans
* Fact Payments
* Dim Customer
* Dim Time

### Risk Mart

Examples:

* Fact Risk Assessment
* Dim Credit
* Dim Geography

---

## Diamond

Highest-value analytical layer.

Contains curated business products and machine-learning-ready datasets.

Responsibilities:

* Feature Store
* Risk Scoring Assets
* Serving Views
* Decision Intelligence Datasets
* Analytical Products

Examples:

* Customer Risk Features
* Credit Default Datasets
* Portfolio Risk Indicators
* Risk Scoring Views

![Dashboard Financial Risks](dashboard/financial_risks.png)

## Quality

Responsible for validating data across all platform layers.

Validation categories:

* Completeness
* Consistency
* Uniqueness
* Accuracy
* Referential Integrity
* Timeliness

Quality validations are automatically executed through orchestration pipelines.

---

## Governance

Provides governance capabilities for data products and datasets.

Includes:

* Metadata Management
* Data Contracts
* Data Lineage
* Policies
* Ownership Definition

---

## Integrations

Contains integrations between platform components and external systems.

Examples:

* External APIs
* Third-Party Providers
* Service Connectors
* Data Exchange Interfaces

---

## Common

Contains reusable platform assets.

Examples:

* Schemas
* Contracts
* Exceptions
* Utilities

This directory must not contain infrastructure configuration.

---

## Tests

Testing strategy includes:

### Unit Tests

Validate isolated functions and transformations.

### Integration Tests

Validate interactions between platform components.

### End-to-End Tests

Validate complete pipeline execution.

---

# Development Principles

## Do

* Keep transformations modular
* Reuse business logic
* Validate data quality
* Document business rules
* Write automated tests
* Follow layer responsibilities

## Do Not

* Store infrastructure code in this repository
* Hardcode credentials
* Duplicate business logic
* Bypass quality validations
* Mix infrastructure and processing concerns

---

# Technology Stack

Core technologies used by the platform:

* Python
* Apache Spark
* Apache Airflow
* PostgreSQL
* dbt
* Pandas
* PyArrow
* Great Expectations
* Scikit-Learn

---

# Project Goal

Build a scalable and maintainable Financial Risk Data Platform capable of supporting:

* Data Engineering
* Analytics Engineering
* Credit Risk Analytics
* Dimensional Modeling
* Machine Learning
* Data Governance
* Decision Intelligence

through a modern layered architecture designed for enterprise-grade analytical workloads.
