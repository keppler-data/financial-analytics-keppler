# Plan Estratégico: Escenario C (Enfoque Híbrido Orientado a ML)

Este documento define la arquitectura, el flujo de datos y los pasos de ejecución para resolver el Caso 5 integrando 4 fuentes bancarias heterogéneas mediante un Data Warehouse corporativo (Esquema Estrella) impulsado por el descubrimiento de variables con Machine Learning.

## 1. El Reto y La Solución (Por qué el Escenario C)

Teníamos 4 bancos con columnas totalmente diferentes (ej. Home Credit con 122 columnas, Give Me Some Credit con 10). Construir un Data Warehouse ciegamente uniendo todas las columnas generaría una tabla llena de valores nulos (basura) que arruinaría cualquier modelo predictivo y confundiría a los analistas de BI.

**La Solución (Escenario C):** 
Utilizamos el banco más complejo (Home Credit) como "conejillo de indias" para entrenar un modelo de Machine Learning y descubrir cuáles son las **20 columnas que realmente predicen si un cliente va a entrar en mora**.
Una vez que conocemos el "secreto" de la morosidad (ese Top 20), ignoramos las otras 100 columnas basura, y vamos a los otros 3 bancos a extraer **únicamente esos 20 conceptos**. Esto nos permite construir un Esquema Estrella altamente estandarizado, limpio y con un inmenso poder predictivo.

## 2. Diagrama de Flujo y Arquitectura Mejorado

A continuación, el flujo de vida del dato desde los bancos hasta la API transaccional, destacando el "Bucle de Descubrimiento" de ML y la fase de consolidación.

```mermaid
flowchart TD
    classDef source fill:#f9f9f9,stroke:#333,stroke-width:1px
    classDef bronze fill:#cd7f32,stroke:#333,color:#fff
    classDef silver fill:#c0c0c0,stroke:#333
    classDef gold fill:#ffd700,stroke:#333,color:#000
    classDef diamond fill:#b9f2ff,stroke:#333,color:#000
    classDef ml fill:#8a2be2,stroke:#333,color:#fff
    classDef app fill:#4CAF50,stroke:#333,color:#fff
    classDef bi fill:#f2c811,stroke:#333,color:#000

    subgraph Fuentes ["Bancos (Fuentes Heterogéneas)"]
        HC[Home Credit]:::source
        LClub[Lending Club]:::source
        GMSC[Give Me Some Credit]:::source
        LP[Loan Prediction]:::source
    end

    subgraph DataLake ["AWS S3 / Data Lake"]
        B[(Bronze)]:::bronze
        S[(Silver)]:::silver
        I[(Intermediate)]:::silver
        G[(Gold: Star Schema)]:::gold
        DW[(Diamond: Feature Store)]:::diamond
    end

    subgraph Procesamiento ["Motor Analítico (Airflow)"]
        SparkELT[Spark ELT: Limpieza Genérica]:::silver
        dbtInt[dbt: Consolidación por Banco (Paralelo)]:::silver
        SparkML_HC[Spark ML: RF Home Credit]:::ml
        SparkML_LC[Spark ML: RF Lending Club]:::ml
        SparkML_GMSC[Spark ML: RF Give Me Some Credit]:::ml
        SparkML_LP[Spark ML: RF Loan Prediction]:::ml
        dbtGold[dbt: Estandarización a Esquema Estrella]:::gold
    end

    subgraph MLOps ["Archivos de Reporte"]
        JSONs[Reportes Top Variables .json y .md]
    end

    subgraph Consumo ["Capa de Negocio y Operación"]
        Athena[AWS Athena]:::diamond
        PBI[Power BI]:::bi
        PG[(PostgreSQL)]:::app
        API[API REST]:::app
    end

    HC & LClub & GMSC & LP --> B
    B --> SparkELT
    SparkELT --> S
    
    S --> dbtInt
    dbtInt --> I
    
    I --> SparkML_HC & SparkML_LC & SparkML_GMSC & SparkML_LP
    SparkML_HC & SparkML_LC & SparkML_GMSC & SparkML_LP --> JSONs
    JSONs -.-> |"Macros de dbt leen el JSON"| dbtGold
    
    I --> dbtGold
    dbtGold --> G
    
    G --> DW
    DW -.-> Athena
    Athena --> PBI
    G --> PG
    PG --> API
```

## 3. ¿Alcanzaremos el "Modelo Esperado" (Esquema Estrella)?

**¡Sí, y de una forma mucho más inteligente!**

El diagrama que tus compañeros plantearon (`modelo_esperado.webp`) propone una estructura clásica con `FACT_LOAN`, `FACT_PAYMENT`, `DIM_CUSTOMER`, `DIM_PRODUCT`, etc.

*   **Sin el Escenario C:** Intentar llenar `DIM_CUSTOMER` habría sido una pesadilla intentando adivinar qué columnas servían de las 300 disponibles entre todos los bancos.
*   **Con el Escenario C:** Nuestro `DIM_CUSTOMER` tendrá exactamente las columnas demográficas que Spark ML demostró matemáticamente que importan (ej. `age`, `debt_ratio`, `income`). Nuestro `FACT_LOAN` tendrá los montos y el historial de pagos. Habremos cumplido su diseño arquitectónico, pero basándonos en Ciencia de Datos, no en adivinanzas.

## 4. El Flujo hacia la API (El Mundo Transaccional)

El Data Warehouse (Diamond en S3) es perfecto para Power BI porque puede escanear miles de millones de registros para hacer promedios y gráficas. Pero S3 es pésimo para consultar *un solo cliente* en tiempo real. 

Por eso la arquitectura define el paso final: **PostgreSQL**.
1. Cada noche, Airflow tomará la versión final de `DIM_CUSTOMER` y `FACT_LOAN` (que ya tienen a todos los clientes de todos los bancos perfilados y con su probabilidad de impago) y hará un volcado (UPSERT) a nuestra base de datos PostgreSQL.
2. Construiremos una **API REST (con FastAPI o Supabase)** que se conecte a PostgreSQL.
3. Cuando el Banco A quiera prestarle dinero a "Juan Pérez", su sistema consultará nuestra API. La API buscará a "Juan Pérez" en Postgres (lo cual toma 5 milisegundos) y le responderá: *"Juan Pérez ya tiene un crédito activo en el Banco B y tiene un 80% de probabilidad de impago. Denegado."*

---

## 5. Hoja de Ruta (Roadmap Ejecutivo)

### Fase 1: Descubrimiento (COMPLETADA ✅)
*   [x] Ingesta y limpieza en Silver.
*   [x] Construcción de la Tabla Gorda de Home Credit (Capa Gold).
*   [x] Entrenamiento de Spark ML y generación del reporte del Top 20.

### Fase 2: Consolidación Analítica (DW - ACTUAL ⏳)
*   [ ] Leer el reporte Markdown de Spark y extraer el Top 20 de variables.
*   [ ] Crear modelos dbt (`intermediate/`) que tomen a cada banco y mapeen sus columnas al estándar del Top 20.
*   [ ] Crear los modelos dbt de Esquema Estrella (`marts/dim_customer`, `marts/fact_loan`) en la capa Diamond, uniendo los 4 bancos estandarizados.

### Fase 3: Activación y Operación (FUTURO 🚀)
*   [ ] Desplegar la base de datos PostgreSQL (OLTP).
*   [ ] Crear script en Airflow (`diamond_to_postgres.py`) para sincronizar datos a PostgreSQL.
*   [ ] Desarrollar la API REST en FastAPI.
*   [ ] Documentar Swagger para que los "Bancos" se integren.
