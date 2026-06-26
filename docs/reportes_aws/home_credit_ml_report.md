# Reporte de Feature Selection

- **Tiempo de Entrenamiento/Procesamiento:** 65 segundos
- **Total de Filas Originales:** 150000
- **Filas Usadas en Entrenamiento (Muestra 1M):** 150000
- **Columnas Finales Retenidas:** 10

## Top 20 Variables por Importancia (Random Forest)
| Variable | Importancia (Gini) |
|---|---|
| `numberoftimes90dayslate` | 0.4565 |
| `numberoftime60_89dayspastduenotworse` | 0.1970 |
| `revolvingutilizationofunsecuredlines` | 0.1902 |
| `numberoftime30_59dayspastduenotworse` | 0.1251 |
| `age` | 0.0140 |
| `numberofopencreditlinesandloans` | 0.0076 |
| `debtratio` | 0.0056 |
| `numberrealestateloansorlines` | 0.0028 |
| `c0` | 0.0013 |

> **Instrucción para dbt:** Crea el modelo final en dbt (`diamond_risk_features.sql`) seleccionando estas variables exactas. Descarta el resto.
