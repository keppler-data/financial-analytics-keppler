import sys
import re

with open('docs/INFRASTRUCTURE_PROPOSAL_V2_ODS.md', 'rb') as f:
    text = f.read().decode('utf-8')

# Mod 1: Resumen Ejecutivo
old_resumen = r"\| Ingestión de datos \| Python puro en workers Airflow \| Aprovecha cluster existente, sin costos adicionales \|"
new_resumen = """| Identidad y Estado en Tiempo Real | **ODS/MDM en PostgreSQL vía API Central** | Actúa como Golden Record de usuarios entre bancos, permitiendo actualizar y consultar estados operacionales en tiempo real. |
| Ingestión de datos | Python puro en workers Airflow | Aprovecha cluster existente. Extrae del ODS y fuentes Kaggle (bancos) |"""
text = re.sub(old_resumen, new_resumen, text)

# Mod 2: Flujo General
old_flujo = r"    subgraph SRC\[\"📦 Fuentes de Datos — CASO 5\"\]\s+direction LR\s+KG1\[\"🏠 Home Credit\\nDefault Risk\\nKaggle API\"\]\s+KG2\[\"💳 Give Me Some\\nCredit\\nKaggle API\"\]\s+KG3\[\"🏦 Lending Club\\nLoan Data\\nKaggle API\"\]\s+KG4\[\"📊 Loan Prediction\\nDataset\\nKaggle API\"\]\s+end"
new_flujo = """    subgraph OPERACIONAL["🔄 Capa Operacional — Master Data"]
        API["API Central\\n(Identidad y Estados)"]
        ODS[("DB OLTP (ODS)\\nPostgreSQL\\nGolden Record")]
        API <--> ODS
    end

    subgraph SRC["📦 Fuentes de Datos / Bancos — CASO 5"]
        direction LR
        KG1["🏠 Banco A\\n(Home Credit)"]
        KG2["💳 Banco B\\n(Give Me Some Credit)"]
        KG3["🏦 Banco C\\n(Lending Club)"]
        KG4["📊 Institución D\\n(Loan Prediction)"]
    end
    
    SRC <-->|"Consulta y actualiza\\nestados en tiempo real"| API
    API -->|"Ingesta periódica\\n(Reverse ETL / CDC)"| DAG_B"""
text = re.sub(old_flujo, new_flujo, text)

# Mod 3: Agregar explicación de Partner ID
old_unificacion = r"## 13\. Cronograma de 2 Semanas"
new_unificacion = """## 13. Estrategia de Unificación de Identidades (MDM)

Para resolver el problema de unificación de las múltiples fuentes de Kaggle sin corromper la integridad de los datos para los modelos de Machine Learning (Diamond Layer), se aplicará la siguiente estrategia:

1. **Simulación de Múltiples Socios (Bancos):**
   - Cada dataset de Kaggle (Home Credit, Lending Club, Give Me Some Credit) será tratado lógicamente como un socio comercial o banco distinto que pertenece al mismo ecosistema.
   - En la capa Bronze y Silver, se añadirá una columna `partner_id` (ej. `partner_id = 'HOME_CREDIT'`).
   
2. **Sin Falsificación de IDs:**
   - No se alterarán los IDs originales ni se forzarán cruces artificiales entre los datasets históricos. 
   - El sistema estará preparado arquitectónicamente a través del ODS para manejar colisiones reales en el futuro, pero respetará la distribución original de los datos para garantizar el correcto entrenamiento de los modelos de PD y LGD.

3. **Esquema Sugerido para ODS (PostgreSQL):**
   ```sql
   CREATE TABLE global_users (
       global_user_id UUID PRIMARY KEY,
       national_id_hash VARCHAR(255) UNIQUE,
       identity_score FLOAT,
       global_risk_status VARCHAR(50),
       last_interaction_timestamp TIMESTAMP
   );

   CREATE TABLE user_tenant_status (
       global_user_id UUID REFERENCES global_users(global_user_id),
       partner_id VARCHAR(50),
       local_partner_user_id VARCHAR(255),
       process_status VARCHAR(50),
       PRIMARY KEY (global_user_id, partner_id)
   );
   ```

---

## 14. Cronograma de 2 Semanas"""
text = re.sub(old_unificacion, new_unificacion, text)


# Guardar
with open('docs/INFRASTRUCTURE_PROPOSAL_V2_ODS.md', 'wb') as f:
    f.write(text.encode('utf-8'))
print("Modificaciones realizadas con éxito.")
