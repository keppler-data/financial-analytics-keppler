# EDA - GiveMeSomeCredit Test Dataset

## 📊 Descripción del Dataset

Análisis exploratorio del **dataset de prueba** de Give Me Some Credit. Este dataset es utilizado para evaluar y validar modelos predictivos entrenados en el dataset de entrenamiento.

---

## 📈 Estadísticas Generales

### Tamaño del Dataset
- **Filas**: 101,503 registros de clientes
- **Columnas**: 11 variables (10 predictoras, 1 objetivo ausente)
- **Propósito**: Prueba/validación de modelos

### Comparación con Training
- **Training**: 150,000 registros
- **Test**: 101,503 registros
- **Proporción**: 67.3% del tamaño de training
- **Diferencia**: ~48,500 registros menos

### Nota Importante
❌ **Variable Objetivo Ausente**: `SeriousDlqin2yrs` contiene 101,503 valores faltantes (100%)
- No tenemos etiquetas verdaderas en test
- Dataset usado para predicciones en competencia

---

## 📋 Variables Disponibles

### 1. **Demographic Features**
- **age**: Edad del cliente
  - Sin valores faltantes
  - Análisis consistente con training

### 2. **Income & Debt Features**
- **MonthlyIncome**: Ingreso mensual
  - **Valores Faltantes**: 19.8% (20,103)
  - Similar a training
  - Requiere mismo tratamiento
  
- **DebtRatio**: Relación Deuda/Ingreso
  - Sin valores faltantes
  - Distribución similar a training

### 3. **Credit & Loan Features**
- **RevolvingUtilizationOfUnsecuredLines**: Utilización de crédito rotativo
  - Sin valores faltantes
  
- **NumberOfOpenCreditLinesAndLoans**: Líneas de crédito abiertas
  - Sin valores faltantes
  
- **NumberRealEstateLoansOrLines**: Préstamos inmobiliarios
  - Sin valores faltantes
  
- **NumberOfDependents**: Dependientes
  - **Valores Faltantes**: 2.6% (2,626)
  - Similar proporción a training

### 4. **Delinquency History Features**
- **NumberOfTime30-59DaysPastDueNotWorse**: Atrasos 30-59 días
- **NumberOfTime60-89DaysPastDueNotWorse**: Atrasos 60-89 días
- **NumberOfTimes90DaysLate**: Atrasos 90+ días
  - Sin valores faltantes
  - Predictores más importantes

---

## 🔍 Análisis de Valores Faltantes

| Variable | Faltantes | % | Comparación |
|----------|-----------|---|------------|
| MonthlyIncome | 20,103 | 19.8% | = Training |
| NumberOfDependents | 2,626 | 2.6% | = Training |
| SeriousDlqin2yrs | 101,503 | 100% | ⚠️ Target ausente |
| Resto | 0 | 0.0% | = Training |

**Patrón**: Los porcentajes de valores faltantes son **idénticos** a training, lo que indica:
- Datasets homogéneos
- Mismo proceso de colección
- Métodos de imputación pueden ser consistentes

---

## 📊 Estadísticas Comparativas con Training

### Tamaño Relativo
```
Test/Training = 101,503 / 150,000 = 67.3%
```

### Perfil de Clientes Similar
- Edad: Distribución comparable
- Ingresos: Patrones similares
- Deuda: Ratios comparables
- Historial: Proporción similar de atrasos

### Consistencia de Datos
- Variables tienen rangos similares
- Distribuciones parecidas
- Proporciones de valores faltantes idénticas

---

## 🎯 Hallazgos Principales

### 1. **Test Set Representativo**
- Tamaño razonable para validación (101K)
- Proporciones de valores faltantes idénticas
- Distribuciones comparables a training

### 2. **Ausencia de Etiquetas**
- Es conjunto de prueba para predicción
- Típico en competencias (Kaggle)
- Predicciones generadas por modelo entrenado

### 3. **Mismos Desafíos que Training**
- 19.8% de ingresos faltantes
- 2.6% de dependientes faltantes
- Mismo preprocesamiento aplicable

### 4. **Presencia de Todas las Variables Predictoras**
- Todas 10 variables de entrada presentes
- Sin variables adicionales
- Estructura idéntica a training

### 5. **Homogeneidad de Datos**
- Valores faltantes en **exactamente** las mismas proporciones
- Sugiere división estratificada del dataset original
- Reduce preocupación por data shift

---

## 🛠️ Análisis Realizados en Notebook

1. ✅ Carga y exploración básica
2. ✅ Información del dataset (shape, dtypes)
3. ✅ Análisis de valores faltantes
4. ✅ Separación de variables numéricas/categóricas
5. ✅ Distribuciones de variables numéricas
6. ✅ Matriz de correlaciones
7. ✅ Detección de outliers (box plots)
8. ✅ Análisis de variables categóricas
9. ✅ Resumen ejecutivo

---

## 💡 Estrategia de Uso para Predicción

### Preprocesamiento
```
1. Aplicar MISMO preprocesamiento que en training:
   - Imputación de MonthlyIncome (media/KNN)
   - Imputación de NumberOfDependents
   - Escalado (si fue usado en training)
   - Feature engineering (si aplica)

2. Orden CRÍTICO:
   - Fit imputadores en training
   - Transform en test (nunca fit en test)
```

### Predicción
```
1. Usar modelo entrenado en training
2. Generar probabilidades para cada cliente
3. Aplicar umbral óptimo encontrado en validation
4. Formato: ID, Probabilidad_Default
```

### Evaluación
```
- Sin etiquetas verdaderas en test
- Usar validation set de training para tuning
- Test es para predicción final
```

---

## ⚠️ Consideraciones Importantes

### 1. **Data Leakage**
- ✅ Seguro: Target no está disponible
- ✅ Seguro: Features no vienen de target
- ⚠️ Verificar: Preprocesamiento no usa información de test

### 2. **Temporal Consistency**
- Dataset parece colectado en mismo período
- Sin indicios de cambio de distribución
- Seguro usar modelo de training

### 3. **Distribución**
- Proporciones de faltantes idénticas
- Sugiere división temporal o estratificada
- Buena representatividad

---

## 📌 Conclusiones

### Características del Test Set

✅ **Positivo**:
- Tamaño adecuado para validación
- Estructura idéntica a training
- Proporciones de faltantes consistentes
- Todas variables predictoras presentes
- Baja probabilidad de data shift

⚠️ **Nota**:
- Target ausente (diseño normal de competencia)
- Requiere modelo entrenado para predicción
- Debe aplicarse identical preprocessing

🎯 **Recomendación**:
Dataset listo para evaluación de modelo. Aplicar same pipeline de preprocesamiento usado en training y generar predicciones para cada cliente.

---

## 📋 Checklist para Predicción

- [ ] Entrenar modelo en dataset de training
- [ ] Crear pipeline de preprocesamiento
- [ ] Validar en validation set
- [ ] Cargar test set
- [ ] Aplicar MISMO preprocesamiento
- [ ] Generar predicciones
- [ ] Formatar output requerido
- [ ] Verificar no hay NaN en predicciones
- [ ] Revisar estadísticas de probabilidades
