# Reporte de Feature Selection (Diamond)

- **Tiempo de Entrenamiento/Procesamiento:** 100 segundos
- **Total de Filas Originales:** 307511
- **Filas Usadas en Entrenamiento (Muestra 1M):** 307511
- **Columnas Finales Retenidas:** 22

## Top 20 Variables por Importancia (Random Forest)
| Variable | Importancia (Gini) |
|---|---|
| `target` | 0.9026 |
| `ext_source_2` | 0.0256 |
| `ext_source_3` | 0.0175 |
| `years_employed` | 0.0140 |
| `avg_bureau_debt` | 0.0104 |
| `ext_source_1` | 0.0053 |
| `own_car_age` | 0.0039 |
| `apartments_mode` | 0.0021 |
| `floorsmax_mode` | 0.0020 |
| `region_rating_client_w_city` | 0.0018 |
| `flag_document_3` | 0.0017 |
| `years_birth` | 0.0016 |
| `flag_emp_phone` | 0.0013 |
| `years_id_publish` | 0.0012 |
| `amt_goods_price` | 0.0011 |
| `livingarea_mode` | 0.0008 |
| `def_30_cnt_social_circle` | 0.0007 |
| `avg_bureau_credit_sum` | 0.0006 |
| `region_rating_client` | 0.0006 |
| `floorsmax_avg` | 0.0006 |

> **Instrucción para dbt:** Crea el modelo final en dbt (`diamond_risk_features.sql`) seleccionando estas variables exactas. Descarta el resto.
