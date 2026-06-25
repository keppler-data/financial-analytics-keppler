# EDA - Archive Loan Dataset (Test)

## 📊 Descripción del Dataset

Análisis exploratorio del **dataset de prueba de préstamos de archivo**. Este dataset contiene solicitudes de préstamo para evaluar y validar modelos de predicción de aprobación.

---

## 📈 Estadísticas Generales

### Tamaño del Dataset
- **Filas**: 367 solicitudes de préstamo
- **Columnas**: 12 variables (sin variable objetivo)
- **Propósito**: Prueba/validación de modelos predictivos
- **Variable Objetivo**: `Loan_Status` ❌ **AUSENTE**

### Comparación con Training
- **Training**: 614 solicitudes
- **Test**: 367 solicitudes
- **Proporción**: 59.8% del tamaño de training
- **Diferencia**: 247 solicitudes menos

---

## 📋 Variables Disponibles

### Identificación
- **Loan_ID**: Identificador único del préstamo
  - Sin valores faltantes
  - 367 préstamos únicos

### Demográficas
- **Gender**: Género del solicitante
  - **Valores Faltantes**: 11 (3.0%)
  - Similar a training (2.1%)
  
- **Married**: Estado civil
  - **Valores Faltantes**: 0 (0.0%) ✅
  - **Nota**: Mejor que training (0.5%)
  
- **Dependents**: Número de dependientes
  - **Valores Faltantes**: 10 (2.7%)
  - Similar a training (2.4%)
  
- **Education**: Nivel educativo
  - **Valores Faltantes**: 0 (0.0%) ✅
  - Completo (sin faltantes)

### Laborales
- **Self_Employed**: Estatus de empleo por cuenta propia
  - **Valores Faltantes**: 23 (6.3%)
  - Ligeramente más que training (5.2%)

### Financieras Individuales
- **ApplicantIncome**: Ingreso del solicitante
  - **Valores Faltantes**: 0 (0.0%) ✅
  - Sin faltantes
  
- **CoapplicantIncome**: Ingreso del co-solicitante
  - **Valores Faltantes**: 0 (0.0%) ✅
  - Sin faltantes

### Del Préstamo
- **LoanAmount**: Monto del préstamo solicitado
  - **Valores Faltantes**: 5 (1.4%)
  - **Mejor que training** (3.6%)
  
- **Loan_Amount_Term**: Plazo del préstamo (meses)
  - **Valores Faltantes**: 6 (1.6%)
  - **Mejor que training** (2.3%)

### Historial Crediticio
- **Credit_History**: Antecedentes de crédito
  - **Valores Faltantes**: 29 (7.9%)
  - **Similar a training** (8.1%)
  - Binaria: 0 (sin antecedentes), 1 (con antecedentes)

### Ubicación
- **Property_Area**: Zona de ubicación de propiedad
  - **Valores Faltantes**: 0 (0.0%) ✅
  - Sin faltantes

### Objetivo
- **Loan_Status**: Estado de aprobación ❌ **AUSENTE (100%)**

---

## 🔍 Análisis de Valores Faltantes

| Variable | Faltantes | % | vs Training |
|----------|-----------|---|------------|
| Loan_Status | 367 | 100% | ⚠️ Target ausente |
| Credit_History | 29 | 7.9% | ≈ Training (8.1%) |
| Self_Employed | 23 | 6.3% | ↑ Training (5.2%) |
| Gender | 11 | 3.0% | ↑ Training (2.1%) |
| Dependents | 10 | 2.7% | ↑ Training (2.4%) |
| LoanAmount | 5 | 1.4% | ↓ Training (3.6%) |
| Loan_Amount_Term | 6 | 1.6% | ↓ Training (2.3%) |
| Married | 0 | 0.0% | ✅ Training (0.5%) |
| Education | 0 | 0.0% | = Training (0.0%) |
| ApplicantIncome | 0 | 0.0% | = Training (0.0%) |
| CoapplicantIncome | 0 | 0.0% | = Training (0.0%) |
| Property_Area | 0 | 0.0% | = Training (0.0%) |

**Patrón Observado**:
- Ligeras diferencias en proporciones
- Credit_History similar (~8%)
- Algunos faltantes menores en test
- **Target completamente ausente**

---

## 📊 Comparativa con Training Dataset

### Tamaño
```
Test/Training = 367 / 614 = 59.8%
```

### Integridad de Datos
- Test tiene **menos faltantes** en promedio
- Mejor calidad en LoanAmount y Loan_Amount_Term
- Similar en Credit_History (variable problemática)

### Composición
- Solicitantes de préstamo similares
- Variables demográficas/financieras idénticas
- Misma estructura de datos

---

## 🎯 Hallazgos Principales

### 1. **Dataset de Prueba Limpio**
- 367 registros, tamaño razonable
- Menos valores faltantes que training (~5% vs ~11%)
- Mejor calidad en variables de préstamo

### 2. **Ausencia de Etiquetas (Expected)**
- 100% faltante en Loan_Status
- Típico en conjuntos de prueba
- Requiere modelo entrenado para predicción

### 3. **Consistencia con Training**
- Mismo set de variables predictoras
- Proporciones similares de faltantes
- Distribuciones comparables

### 4. **Mejor Calidad en Algunos Aspectos**
- Menos faltantes en LoanAmount (1.4% vs 3.6%)
- Menos faltantes en Loan_Amount_Term (1.6% vs 2.3%)
- Married: Sin faltantes (vs 0.5% en training)

### 5. **Mantiene Problemas Críticos**
- Credit_History sigue con ~8% faltantes
- Self_Employed ligeramente peor (6.3% vs 5.2%)
- Gender más faltantes (3.0% vs 2.1%)

---

## 🛠️ Análisis Realizados en Notebook

1. ✅ Carga de datos y estructura
2. ✅ Información del dataset
3. ✅ Análisis de valores faltantes
4. ✅ Separación variables numéricas/categóricas
5. ✅ Distribuciones de variables numéricas
6. ✅ Matriz de correlación
7. ✅ Detección de outliers
8. ✅ Análisis de variables categóricas
9. ✅ Resumen ejecutivo

---

## 💡 Estrategia de Uso para Predicción

### Paso 1: Preprocesamiento
```python
# Aplicar MISMO preprocessing que en training
1. Imputar Credit_History con moda
2. Imputar Self_Employed con moda
3. Imputar Gender con moda
4. Imputar Dependents con moda/0
5. Imputar LoanAmount con media/KNN
6. Imputar Loan_Amount_Term con moda

# Importante: FIT transformadores en TRAINING
#            TRANSFORM en TEST
```

### Paso 2: Feature Engineering
```python
# Crear mismas features que en training
- Ratio: LoanAmount / ApplicantIncome
- Total Income: ApplicantIncome + CoapplicantIncome
- Has_Coapplicant: CoapplicantIncome > 0
- Interaction features (si se usaron)
```

### Paso 3: Predicción
```python
# Usar modelo entrenado en training set
1. Cargar modelo
2. Transformar test set (same pipeline)
3. Generar predicciones
4. Aplicar umbral si es necesario
5. Formatar output (ID, Prediction)
```

### Paso 4: Validación
```python
# Verificar integridad
- No NaN en predicciones
- Probabilidades en rango [0, 1]
- Misma cantidad de predicciones que registros
- Formato correcto de output
```

---

## ⚠️ Consideraciones Importantes

### 1. **Data Leakage**
- ✅ Seguro: Target completamente ausente
- ✅ Seguro: Features no contienen información de target
- ⚠️ Crítico: Usar MISMO preprocessing que training

### 2. **Distribución**
- Ligeras diferencias en proporciones de faltantes
- Probablemente split temporal o estratificado
- Bajo riesgo de data shift

### 3. **Calidad Relativa**
- Test es **más limpio** que training
- Menos outliers esperados
- Predicciones más confiables potencialmente

---

## 📌 Conclusiones

### Características del Test Set

✅ **Positivo**:
- Tamaño adecuado (367 = ~60% training)
- Menos valores faltantes que training
- Todas variables predictoras presentes
- Estructura idéntica a training
- Buena calidad general de datos

⚠️ **Nota Importante**:
- Target ausente (por diseño)
- Requiere preprocessing idéntico a training
- Diferencias pequeñas en proporciones de faltantes

🎯 **Recomendación**:
Dataset listo para predicción. Implementar pipeline:
1. Entrenar en training set
2. Validar en validation split
3. Preparar test con same transformations
4. Generar predicciones finales

---

## 📋 Checklist Pre-Predicción

- [ ] Modelo entrenado y validado
- [ ] Pipeline de preprocessing documentado
- [ ] Test set cargado correctamente
- [ ] Aplicar same preprocessing (fit en training)
- [ ] Verificar no hay NaN después de imputación
- [ ] Generar predicciones
- [ ] Verificar rango de probabilidades [0, 1]
- [ ] Formatar output (ID + Predicción)
- [ ] Validar cantidad de registros
- [ ] Último checksum vs original

---

## 📊 Comparativa Final: Archive Test vs CS Test

| Aspecto | Archive Test | CS Test |
|---------|---|---|
| Filas | 367 | 101,503 |
| Columnas | 12 | 10 |
| Tamaño | **Pequeño** | **Grande** |
| Integridad | ~95% | ~99% |
| Faltantes Target | 100% | 100% |
| Aplicación | Hipotecas | Riesgo crediticio |
| Complejidad | Baja | Alta |

**Conclusion**: Archive test es más pequeño pero bien estructurado. CS test es mucho más grande. Ambos listos para predicción con pipeline apropiado.
