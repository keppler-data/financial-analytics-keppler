# EDA - Give Me Some Credit (Análisis Principal)

## 📊 Descripción del Dataset

Este es el análisis exploratorio principal del dataset **Give Me Some Credit**, que contiene información crediticia de clientes. El objetivo es **predecir si un cliente incurrirá en un atraso grave (90+ días) en los próximos 2 años**.

---

## 📈 Estadísticas Generales

### Tamaño del Dataset
- **Filas**: 150,000 clientes
- **Columnas**: 11 variables
- **Variable Objetivo**: `SeriousDlqin2yrs` (Atraso severo en 2 años)

### Distribución de la Variable Objetivo
| Clase | Cantidad | Porcentaje |
|-------|----------|-----------|
| Sin Atraso (0) | 139,974 | 93.3% |
| Con Atraso (1) | 10,026 | 6.7% |

**⚠️ Hallazgo importante**: Dataset **altamente desbalanceado** con una proporción 13.9:1

---

## 🔍 Análisis de Valores Faltantes

| Variable | Valores Faltantes | Porcentaje |
|----------|------------------|-----------|
| MonthlyIncome | 29,731 | 19.8% |
| NumberOfDependents | 3,924 | 2.6% |
| Resto | 0 | 0% |

**Recomendación**: Las variables con valores faltantes requieren imputación o tratamiento especial antes del modelado.

---

## 📋 Variables del Dataset

### 1. **Demográficas**
- **age**: Edad del cliente
  - Media: ~52 años
  - Rango: Edad mínima a máxima
  - Distribución: Relativamente uniforme

### 2. **Financieras Individuales**
- **MonthlyIncome**: Ingreso mensual
  - Media (sin ceros): Variable
  - Aproximadamente 19.8% de valores faltantes
  - Presencia de ingresos cero (sin empleo)

- **DebtRatio**: Ratio de deuda/ingresos
  - Rango: 0 a valores muy altos
  - Indicador de carga financiera

### 3. **Historial de Pagos**
- **NumberOfTime30-59DaysPastDueNotWorse**: Atrasos de 30-59 días
  - Mayoría sin atrasos
  - Proporción pequeña con antecedentes

- **NumberOfTime60-89DaysPastDueNotWorse**: Atrasos de 60-89 días
  - Menos frecuentes que anteriores

- **NumberOfTimes90DaysLate**: Atrasos de 90+ días
  - Indicador crítico de riesgo
  - Altamente correlacionado con variable objetivo

### 4. **Líneas de Crédito**
- **NumberOfOpenCreditLinesAndLoans**: Líneas de crédito abiertas
  - Media: ~8 líneas por cliente
  - Indica experiencia crediticia

- **NumberRealEstateLoansOrLines**: Préstamos de bienes raíces
  - Indicador de propiedades hipotecadas

### 5. **Utilización de Crédito**
- **RevolvingUtilizationOfUnsecuredLines**: Utilización de líneas rotativas
  - Indica qué porcentaje del crédito disponible está siendo usado
  - Valores entre 0 y 1 (0-100%)

### 6. **Cargas Familiares**
- **NumberOfDependents**: Número de dependientes
  - 2.6% de valores faltantes
  - Influye en capacidad de pago

---

## 🎯 Hallazgos Principales

### 1. **Desbalance Significativo**
- Solo 6.7% de los clientes tiene atrasos severos
- Esto es típico en problemas de detección de fraude/riesgo
- Requiere técnicas especiales: SMOTE, ajuste de pesos, umbral personalizado

### 2. **Datos Incompletos**
- Casi 20% de datos de ingreso mensual faltantes
- ~2.6% de dependientes faltantes
- Necesario aplicar imputación inteligente

### 3. **Distribuciones No-Normales**
- Muchas variables con distribuciones sesgadas (skewed)
- Presencia de outliers en ingresos y ratios de deuda
- Puede requerir transformaciones (log, Box-Cox)

### 4. **Comportamiento Predictivo**
- **Historial de pagos** es el predictor más fuerte
- Clientes con atrasos previos tienen mayor probabilidad de atrasos futuros
- Edad, ingreso y ratio de deuda también son relevantes

### 5. **Patrones de Riesgo**
- Mayor número de líneas de crédito puede indicar búsqueda de crédito (posible riesgo)
- Ratios de deuda muy altos predicen atrasos
- Ingresos bajos o ausentes aumentan riesgo

---

## 🛠️ Análisis Realizados

1. ✅ Exploración de estructura básica
2. ✅ Análisis de valores faltantes
3. ✅ Estadísticas descriptivas detalladas
4. ✅ Distribución de la variable objetivo
5. ✅ Análisis univariado de variables clave
6. ✅ Análisis de correlaciones
7. ✅ Detección de outliers
8. ✅ Análisis bivariado (target vs. predictores)

---

## 💡 Recomendaciones para Modelado

1. **Manejo del Desbalance**: Usar técnicas como SMOTE o ajustar pesos de clase
2. **Imputación**: Usar KNN o media condicional para ingresos faltantes
3. **Feature Engineering**: Crear ratios adicionales (deuda/edad, ingresos combinados)
4. **Escalado**: Normalizar variables para modelos sensibles a escala
5. **Selección**: Remover colinealidad entre variables
6. **Validación**: Usar stratified k-fold para mantener proporciones de clase

---

## 📝 Conclusión

Este dataset presenta un **desafío interesante de clasificación desbalanceada** para predicción de riesgo crediticio. Con el tratamiento apropiado de datos faltantes y técnicas de balanceo, es posible desarrollar un modelo predictivo robusto para identificar clientes en riesgo de atraso severo.
