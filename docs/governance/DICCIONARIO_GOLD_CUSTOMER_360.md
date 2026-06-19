# 📘 Diccionario de Datos Maestro - Capa Gold

Este documento contiene la especificación técnica y las reglas de negocio del 100% de los campos que componen la tabla analítica unificada `gold_customer_360`. Esta tabla consolida la información operacional de los créditos (ETL) con las variables de comportamiento móvil e historial externo (ELT).

## 📊 Especificación de la Tabla `gold_customer_360`

* **Esquema:** `gold`
* **Tipo de Estructura:** Tabla dbt Materializada
* **Llave Primaria:** `customer_id`

| Nombre del Campo | Tipo de Dato | Origen Técnico | Regla de Negocio / Significado Analítico |
| :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(50)` | `dim_customers` | Clave primaria única y distintiva del cliente dentro del ecosistema Kepler. No admite nulos. |
| `first_name` | `VARCHAR(100)` | `dim_customers` | Primer nombre del cliente (Datos operacionales validados). |
| `last_name` | `VARCHAR(100)` | `dim_customers` | Apellido(s) del cliente. |
| `email` | `VARCHAR(150)` | `dim_customers` | Correo electrónico principal verificado del usuario. |
| `customer_onboarding_date` | `TIMESTAMP` | `dim_customers` | Fecha oficial en la que el cliente completó su registro e ingreso a la Fintech. |
| `total_active_loans` | `INTEGER` | `fct_loans` | Cantidad total de productos crediticios vigentes y en estado activo que posee el cliente. |
| `total_outstanding_balance` | `NUMERIC(18,2)` | `fct_loans` | Saldo insoluto total (lo que debe actualmente a capital) acumulado entre todos sus créditos. |
| `total_allocated_credit` | `NUMERIC(18,2)` | `fct_loans` | Monto original total del cupo de crédito otorgado e inicialmente desembolsado. |
| `historical_installments_count` | `INTEGER` | `agg_customer_installment_history` | Sumatoria histórica del total de cuotas que han sido facturadas y agendadas para el cliente. |
| `total_amount_due_historic` | `NUMERIC(18,2)` | `agg_customer_installment_history` | Monto total acumulado que el cliente debió pagar históricamente según sus cronogramas de amortización. |
| `total_amount_paid_historic` | `NUMERIC(18,2)` | `agg_customer_installment_history` | Capital e intereses efectivamente cobrados y recuperados por la Fintech asociados a este cliente. |
| `historical_max_days_mora` | `INTEGER` | `agg_customer_installment_history` | El peor registro histórico (pico máximo) de días de retraso continuos que el cliente ha tenido en una cuota. |
| `avg_payment_delay_3m` | `NUMERIC(5,2)` | `fct_customer_payment_behavior_features` | Promedio móvil de días de retraso observados en los pagos del último trimestre activo. |
| `avg_payment_delay_6m` | `NUMERIC(5,2)` | `fct_customer_payment_behavior_features` | Promedio móvil de días de retraso observados en los pagos de los últimos 6 meses continuos. |
| `avg_payment_delay_12m` | `NUMERIC(5,2)` | `fct_customer_payment_behavior_features` | Promedio móvil de días de retraso observados en los pagos de los últimos 12 meses (ventana macro anual). |
| `missed_payment_count_90d` | `INTEGER` | `fct_customer_payment_behavior_features` | Cantidad de cuotas que vencieron y quedaron completamente impagadas durante los últimos 90 días de corte. |
| `payment_consistency_score` | `NUMERIC(5,2)` | `fct_customer_payment_behavior_features` | Puntaje interno ponderado $[0.0 - 100.0]$ que mide la disciplina del cliente. A mayor score, menor riesgo. |
| `current_bureau_score` | `INTEGER` | `agg_customer_bureau_history` | Último puntaje e índice de solvencia reportado de forma oficial por la entidad crediticia externa. |
| `bureau_score_trend_3m` | `INTEGER` | `agg_customer_bureau_history` | Variación neta del puntaje externo en los últimos 3 meses. Valores negativos indican deterioro crediticio afuera. |
| `bureau_score_trend_12m` | `INTEGER` | `agg_customer_bureau_history` | Variación neta del puntaje externo en el último año, capturando ciclos largos de endeudamiento. |
| `bureau_inquiries_last_period` | `INTEGER` | `agg_customer_bureau_history` | Número de consultas de historial que otras entidades financieras hicieron sobre este cliente en el último mes. |
| `dbt_updated_at` | `TIMESTAMP` | `Ejecución dbt` | Marca de tiempo que registra el momento exacto en que dbt actualizó la fila en la capa Gold. |

---
*Documentación generada automáticamente bajo los estándares de gobernanza de datos para el proyecto Kepler.*