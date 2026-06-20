# EDA - GiveMeSomeCredit Training Dataset

## 📊 Descripción del Dataset

Análisis exploratorio detallado del **dataset de entrenamiento** de Give Me Some Credit. Este dataset es utilizado para entrenar modelos predictivos de riesgo crediticio.

---

## 📈 Estadísticas Generales

### Tamaño del Dataset
- **Filas**: 150,000 registros de clientes
- **Columnas**: 11 variables (incluyendo variable objetivo)
- **Propósito**: Entrenamiento de modelos predictivos

### Composición
- **Variables Numéricas**: 11
- **Variables Categóricas**: 0
- **Datos Completos**: ~97%

---

## 📋 Variables Analizadas

### Variable Objetivo
**SeriousDlqin2yrs** (Target):
- **0 (Sin atraso)**: 139,974 (93.3%)
- **1 (Con atraso severo)**: 10,026 (6.7%)

### Variables de Entrada

#### 1. **Demographic Features**
- **age**: Edad del cliente (años)
  - Sin valores faltantes
  - Distribución relativamente uniforme
  - Rango completo de edades adultas

#### 2. **Income & Debt Features**
- **MonthlyIncome**: Ingreso mensual
  - **Valores Faltantes**: 19.8% (29,731)
  - Requiere imputación especial
  
- **DebtRatio**: Relación Deuda/Ingreso
  - Sin valores faltantes
  - Rango: 0 a valores muy altos
  - Indicador importante de riesgo

#### 3. **Credit History Features**
- **RevolvingUtilizationOfUnsecuredLines**: Utilización de crédito rotativo
- **NumberOfOpenCreditLinesAndLoans**: Líneas de crédito abiertas
- **NumberRealEstateLoansOrLines**: Préstamos inmobiliarios
- **NumberOfDependents**: Dependientes del cliente
  - **Valores Faltantes**: 2.6% (3,924)

#### 4. **Delinquency Features**
- **NumberOfTime30-59DaysPastDueNotWorse**: Atrasos 30-59 días
  - Indicador moderado de comportamiento de pago
  
- **NumberOfTime60-89DaysPastDueNotWorse**: Atrasos 60-89 días
  - Predictor más fuerte que atrasos cortos
  
- **NumberOfTimes90DaysLate**: Atrasos 90+ días
  - **Más importante**: Fuertemente correlacionado con variable objetivo
  - Clientes con este antecedente tienen muy alto riesgo

---

## 🔍 Valores Faltantes

| Variable | Faltantes | % |
|----------|-----------|---|
| MonthlyIncome | 29,731 | 19.8% |
| NumberOfDependents | 3,924 | 2.6% |
| Resto | 0 | 0.0% |

**Impacto**: 
- MonthlyIncome es la más problemática
- Aproximadamente 19.8% de registros afectados
- Requiere estrategia de imputación robusta

---

## 📊 Análisis Estadísticos por Variable

### Distribuciones Clave

**Age**:
- Distribución relativamente uniforme
- Edad media ~52 años
- Rango: adultos completamente representados

**Monthly Income** (excluyendo faltantes):
- Distribución log-normal (sesgada a la derecha)
- Muchos valores muy bajos o cero
- Pocos valores muy altos (outliers)

**Debt Ratio**:
- Altamente sesgado (skewed)
- Mayoría cerca de 0
- Valores extremadamente altos presentes

**Payment History**:
- Mayoría de clientes (>85%) sin atrasos
- Minoría con antecedentes de atraso
- Fuerte predictor de riesgo

---

## 🎯 Hallazgos Principales

### 1. **Desbalance de Clases Extremo**
- Proporción 93.3% vs 6.7% (14:1)
- Típico en problemas de riesgo crediticio
- Implicaciones: Métrica de evaluación importante es recall/precision, no accuracy

### 2. **Datos Faltantes Inteligentes**
- MonthlyIncome puede estar ausente por:
  - Clientes sin empleo
  - Datos no reportados
  - Hace 2 años (referencia temporal)
- No es ausencia aleatoria - puede ser significativa

### 3. **Comportamiento Pasado = Mejor Predictor**
- Historial de atrasos anteriores → fuertemente predictivo
- Clientes con atrasos 90+ días: Altísimo riesgo
- Variables de "payment history" más importantes que demográficas

### 4. **Múltiples Líneas de Crédito**
- Promedio ~8 líneas por cliente
- Relacionado con experiencia crediticia
- Puede indicar "búsqueda de crédito" si es muy alto

### 5. **Distribuciones Asimétricas**
- Muchas variables con skewness (sesgo)
- Presencia significativa de outliers
- Modelos sensibles a distribuciones pueden necesitar transformaciones

---

## 🛠️ Análisis Realizados en Notebook

1. ✅ Carga y exploración básica
2. ✅ Análisis completo de valores faltantes
3. ✅ Estadísticas descriptivas detalladas
4. ✅ Visualización de distribuciones
5. ✅ Análisis de variable objetivo
6. ✅ Variables de edad
7. ✅ Variables de ingreso
8. ✅ Variables de deuda
9. ✅ Historial de pagos
10. ✅ Líneas de crédito
11. ✅ Análisis bivariado

---

## 💡 Recomendaciones de Preprocesamiento

### 1. **Manejo de Valores Faltantes**
```
MonthlyIncome:
- Crear bandera binaria (missing/not missing)
- Imputar con media/mediana por grupo
- Considerar KNN imputation

NumberOfDependents:
- Remplazar con 0 o media
- Menor impacto (~2.6%)
```

### 2. **Tratamiento de Desbalance**
- SMOTE para oversample de clase minoritaria
- Undersampling de clase mayoritaria
- Ajustar pesos de clase en modelo

### 3. **Feature Engineering**
- Crear ratios: Debt/Age, Income/Dependents
- Agrupar atrasos: Total past due events
- Edad de líneas de crédito

### 4. **Transformaciones**
- Log de ingresos (si usa regresión)
- Normalización/Estandarización
- Binning para variables ordinales

### 5. **Validación**
- Usar stratified k-fold
- Métricas: Precision, Recall, F1, AUC-ROC
- Matriz de confusión ponderada por clase

---

## 📌 Conclusiones del EDA

Este dataset de entrenamiento presenta:

✅ **Fortalezas**:
- Tamaño suficiente (150K registros)
- Variables relevantes y bien definidas
- Mínima duplicación
- Datos principalmente completos

⚠️ **Desafíos**:
- Desbalance extremo (6.7% vs 93.3%)
- Valores faltantes en ingreso importante (19.8%)
- Distribuciones no-normales
- Presencia de outliers

🎯 **Recomendación**:
Dataset adecuado para modelado con técnicas apropiadas de manejo de desbalance e imputación. Se espera que el modelo tenga buen rendimiento en detección de riesgo.
