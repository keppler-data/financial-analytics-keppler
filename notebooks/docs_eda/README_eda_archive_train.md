# EDA - Archive Loan Dataset (Training)

## 📊 Descripción del Dataset

Análisis exploratorio del **dataset de entrenamiento de préstamos de archivo**. Este dataset contiene información de solicitudes de préstamos con variables demográficas, financieras y de historial crediticio.

---

## 📈 Estadísticas Generales

### Tamaño del Dataset
- **Filas**: 614 solicitudes de préstamo
- **Columnas**: 13 variables
- **Propósito**: Predicción de aprobación de préstamo
- **Variable Objetivo**: `Loan_Status` (Aprobado/Rechazado)

### Tipo de Problema
- **Clasificación Binaria**: Predicción de aprobación de préstamo
- **Escala**: Pequeño dataset (N=614)
- **Aplicación**: Predicción de eligibilidad para préstamo hipotecario

---

## 📋 Variables Analizadas

### Identificación
- **Loan_ID**: Identificador único del préstamo
  - Sin valores faltantes
  - 614 préstamos únicos

### Demográficas
- **Gender**: Género del solicitante
  - **Valores Faltantes**: 13 (2.1%)
  - Categorías: Male, Female
  
- **Married**: Estado civil
  - **Valores Faltantes**: 3 (0.5%)
  - Categorías: Yes, No
  
- **Dependents**: Número de dependientes
  - **Valores Faltantes**: 15 (2.4%)
  - Valores: 0, 1, 2, 3+
  
- **Education**: Nivel educativo
  - **Valores Faltantes**: 0 (0.0%)
  - Categorías: Graduate, Not Graduate

### Laborales
- **Self_Employed**: Estatus de empleo por cuenta propia
  - **Valores Faltantes**: 32 (5.2%)
  - Categorías: Yes, No

### Financieras Individuales
- **ApplicantIncome**: Ingreso del solicitante
  - **Valores Faltantes**: 0 (0.0%)
  - Rango variable
  
- **CoapplicantIncome**: Ingreso del co-solicitante (si aplica)
  - **Valores Faltantes**: 0 (0.0%)
  - Muchos valores en 0

### Del Préstamo
- **LoanAmount**: Monto del préstamo solicitado
  - **Valores Faltantes**: 22 (3.6%)
  - Variable importante
  
- **Loan_Amount_Term**: Plazo del préstamo (meses)
  - **Valores Faltantes**: 14 (2.3%)
  - Típicamente 360 meses (30 años)

### Historial Crediticio
- **Credit_History**: Antecedentes de crédito
  - **Valores Faltantes**: 50 (8.1%)
  - Binaria: 0 (sin antecedentes), 1 (con antecedentes)
  - **Hallazgo**: Mayor proporción de faltantes aquí

### Ubicación
- **Property_Area**: Zona de ubicación de propiedad
  - **Valores Faltantes**: 0 (0.0%)
  - Categorías: Urban, Rural, Semiurban

### Objetivo
- **Loan_Status**: Estado de aprobación del préstamo
  - **Valores Faltantes**: 0 (0.0%)
  - Categorías: Y (Aprobado), N (Rechazado)

---

## 🔍 Análisis de Valores Faltantes

| Variable | Faltantes | % | Severidad |
|----------|-----------|---|-----------|
| Credit_History | 50 | 8.1% | ⚠️ Alta |
| Self_Employed | 32 | 5.2% | Moderada |
| LoanAmount | 22 | 3.6% | Moderada |
| Dependents | 15 | 2.4% | Baja |
| Loan_Amount_Term | 14 | 2.3% | Baja |
| Gender | 13 | 2.1% | Baja |
| Married | 3 | 0.5% | Muy Baja |
| Resto | 0 | 0.0% | ✅ Completo |

**Impacto Total**:
- Al menos una variable faltante: ~11% de registros
- Múltiples faltantes: Pequeño porcentaje

---

## 📊 Perfil de Solicitantes

### Demográfico
- **Predominio**: Probablemente mayoría casados
- **Educación**: Mezcla de graduados y no-graduados
- **Género**: Distribución de hombres/mujeres

### Laboral
- **Self-Employed**: Minoría (~5%)
- **Dependientes**: Variado (0-3+)
- Típicamente familias con 1-2 dependientes

### Financiero
- **Ingresos**: Rango variable
- **Co-solicitante**: Muchos préstamos individuales (coapplicant=0)
- **Monto Préstamo**: Variable según necesidad
- **Plazo**: Mayormente 30 años (360 meses)

### Crediticio
- **Antecedentes**: 8.1% sin información
- Probablemente mixta (algunos con, algunos sin)

### Ubicación
- **Urbana/Rural/Semi-urbana**: Distribución a determinar

---

## 🎯 Hallazgos Principales

### 1. **Dataset Pequeño pero Íntegro**
- 614 registros es relativamente pequeño
- Mínimos valores faltantes en variables clave
- Buena calidad general de datos

### 2. **Credit History es Crítica**
- 8.1% de faltantes (mayor proporción)
- Probablemente variable predictora importante
- Imputación debe ser cuidadosa

### 3. **Ingresos Completos**
- ApplicantIncome: 0% faltantes ✅
- CoapplicantIncome: 0% faltantes ✅
- Buena calidad para análisis financiero

### 4. **Problema de Préstamo Hipotecario**
- Plazo uniforme (~360 meses)
- Monto variable según solicitud
- Típico de hipotecas residenciales

### 5. **Características Equilibradas**
- Múltiples dimensiones (demográfica, financiera, crediticia)
- Información suficiente para modelado
- Variables correlacionadas pero distintas

---

## 💡 Insights Específicos

### Variables Más Importantes Esperadas
1. **Credit_History** - Antecedentes de crédito
2. **ApplicantIncome + CoapplicantIncome** - Capacidad de pago
3. **LoanAmount** - Relación deuda/ingresos
4. **Property_Area** - Indicador socioeconómico
5. **Education** - Proxy de estabilidad laboral

### Relaciones Probables
- Mayor ingreso → Mayor tasa de aprobación
- Más dependientes → Menor aprobación (obligaciones)
- Crédito previo → Mayor aprobación
- Préstamo muy grande → Menor aprobación

### Patrones Esperados
- Categorías binarias o pocos niveles
- Datos estructurados y limpios
- Sesgos posibles en aprobación por género/área

---

## 🛠️ Análisis Realizados en Notebook

1. ✅ Carga de datos
2. ✅ Exploración estructural (shape, dtypes)
3. ✅ Análisis detallado de valores faltantes
4. ✅ Separación de variables numéricas/categóricas
5. ✅ Distribuciones numéricas
6. ✅ Matriz de correlación
7. ✅ Detección de outliers
8. ✅ Análisis de variables categóricas
9. ✅ Resumen ejecutivo

---

## 💡 Recomendaciones de Modelado

### 1. **Manejo de Faltantes**
```
Credit_History (8.1%): 
  - Opción 1: Crear categoría "Unknown"
  - Opción 2: Predecir valor basado en otras variables
  
Self_Employed (5.2%):
  - Imputar con moda (mayoría No)
  - O crear categoría "Unknown"

LoanAmount (3.6%):
  - Imputar con media/mediana por grupo
  - O usar modelo para predecir

Resto: Imputación directa
```

### 2. **Feature Engineering**
- Ratio: LoanAmount / ApplicantIncome
- Total Income: ApplicantIncome + CoapplicantIncome
- Has_Coapplicant: Binaria (CoApp > 0)
- Total_Dependents: Incluir co-solicitante
- Income_per_Dependent

### 3. **Encoding**
- One-hot encoding para categóricas
- Ordinal para variables ordenadas
- Target encoding si cardinales altas

### 4. **Selección de Modelo**
- Logistic Regression (baseline)
- Random Forest (maneja categorías bien)
- Gradient Boosting (XGBoost, LightGBM)
- Neural Networks (si necesita regularización)

### 5. **Validación**
- Stratified K-fold (balancear clases)
- Métricas: Accuracy, Precision, Recall, AUC-ROC
- Matriz de confusión

---

## 📌 Conclusiones

### Perfil del Dataset

✅ **Fortalezas**:
- Datos limpios y estructurados
- Mínimos valores faltantes en variables críticas
- Problema bien definido (hipoteca/préstamo)
- Variables relevantes y diversas

⚠️ **Limitaciones**:
- Tamaño pequeño (614 registros)
- 8% de faltantes en predictor potencialmente importante
- Puede haber desbalance de clases
- Capacidad predictiva limitada por N pequeño

🎯 **Aplicabilidad**:
Dataset adecuado para:
- Ejercicios de modelado
- Prueba de pipelines de ML
- Problemas educativos
- Prototipos antes de escalar

**No ideal para**:
- Modelos de producción (N muy pequeño)
- Deep learning (insuficientes datos)
- Validación en 3+ conjuntos

---

## 📊 Comparativa: Archive Training vs CS Training

| Aspecto | Archive Train | CS Train |
|---------|---|---|
| Filas | 614 | 150,000 |
| Columnas | 13 | 11 |
| Aplicación | Hipotecas | Riesgo crediticio |
| Variables Faltantes | ~11% filas | ~20% en cols |
| Tamaño | **Pequeño** | **Grande** |
| Complejidad | Baja | Alta |
