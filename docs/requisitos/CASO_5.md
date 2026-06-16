# Descontrol Operacional y Riesgo Crediticio en una Entidad de Préstamos y Microcréditos

---

## Contexto del Negocio

Una entidad financiera especializada en **préstamos digitales y microcréditos** opera en múltiples países de Latinoamérica ofreciendo servicios a personas naturales, pequeños comercios y trabajadores independientes. La compañía ha tenido un crecimiento acelerado gracias a la aprobación rápida de créditos mediante canales digitales y aplicaciones móviles.

### Productos y Servicios Actuales

- Préstamos personales
- Microcréditos
- Créditos para pequeñas empresas
- Líneas de crédito rotativas
- Financiamiento para comercios
- Pagos diferidos
- Billeteras digitales
- Scoring crediticio automatizado

La operación funciona completamente de manera digital y procesa **millones de solicitudes, pagos y eventos financieros diariamente**.

### Canales de Interacción con Usuarios

- Aplicaciones móviles
- Portales web
- Comercios aliados
- APIs externas
- Plataformas financieras
- Canales de recaudo

### Tipos de Información Generada

- Solicitudes de crédito
- Pagos
- Historial financiero
- Comportamiento de usuarios
- Navegación digital
- Validaciones de identidad
- Eventos transaccionales
- Interacciones comerciales
- Cobranza y recaudos
- Historial de mora
- Comportamiento de dispositivos

---

## Problemática Actual

Durante el último año la organización comenzó a enfrentar **problemas críticos** relacionados con:

- Aumento en incumplimientos de pago
- Crecimiento acelerado de cartera vencida
- Fraudes relacionados con identidad
- Créditos aprobados a clientes de alto riesgo
- Inconsistencias entre plataformas financieras
- Errores en conciliaciones
- Diferencias entre reportes operacionales y financieros
- Demoras en procesos de cobranza
- Pérdida de trazabilidad de operaciones

### Perspectivas por Área

| Área | Problema Reportado |
|------|-------------------|
| **Riesgo** | Los modelos actuales no reflejan correctamente el comportamiento real de los clientes |
| **Comercial** | Se están rechazando demasiados clientes potencialmente rentables |
| **Financiera** | Inconsistencias entre pagos registrados y recaudos reales |

### Problemas de Calidad de Datos

- Diferentes sistemas manejan información distinta
- Algunos clientes aparecen duplicados
- Existen historiales incompletos
- Muchos eventos llegan con retrasos
- Algunas fuentes contienen datos corruptos
- Los reportes históricos tardan demasiado tiempo en generarse

### Falta de Visibilidad Sobre

- Qué perfiles representan mayor riesgo
- Qué factores están afectando la mora
- Qué segmentos generan mayores pérdidas
- Cómo se comportan realmente los clientes a lo largo del tiempo

---

## Situación Tecnológica

### Fuentes de Datos Actuales

La empresa recibe información desde múltiples fuentes:

- Aplicaciones móviles
- Plataformas web
- APIs financieras
- Sistemas de pagos
- Plataformas KYC
- Operadores de recaudo
- Sistemas de cobranza
- Logs de aplicaciones
- Eventos de navegación
- Historiales crediticios
- Archivos históricos
- Plataformas externas de validación financiera

### Desafíos con los Datos

- Millones de eventos diarios
- Grandes históricos financieros
- Múltiples formatos
- Cambios frecuentes en estructuras
- Registros duplicados
- Datos faltantes
- Inconsistencias temporales
- Errores de calidad
- Información semiestructurada
- Crecimiento continuo de volumen

La organización necesita capacidades de **análisis histórico y operacional** para soportar el crecimiento del negocio y mejorar la toma de decisiones financieras.

---

## Lo que la Empresa Necesita

La alta dirección busca construir una solución que permita:

### Objetivos Estratégicos

- Centralizar toda la información financiera y operacional
- Mejorar trazabilidad de créditos
- Comprender el comportamiento de clientes
- Identificar patrones de mora
- Detectar anomalías
- Analizar riesgo crediticio
- Entender causas de incumplimiento
- Mejorar procesos de cobranza
- Optimizar aprobaciones de crédito
- Construir métricas corporativas confiables
- Mejorar monitoreo operacional
- Reducir pérdidas financieras

### Capacidades Analíticas Requeridas

- Análisis históricos escalables
- Monitoreo continuo de operaciones
- Consolidación de información
- Integración de múltiples fuentes
- Análisis temporal de clientes
- Capacidades analíticas para crecimiento futuro
- Trazabilidad de eventos financieros

### Escenarios que la Solución Debe Contemplar

- Crecimiento masivo de usuarios
- Grandes volúmenes de transacciones
- Eventos continuos
- Inconsistencias entre sistemas
- Cambios operacionales frecuentes
- Información incompleta
- Integración de múltiples fuentes heterogéneas

---

## Fuentes de Información (Datasets)

### Dataset Principal

- **[Home Credit Default Risk](https://www.kaggle.com/c/home-credit-default-risk)** — Dataset principal con historial crediticio complejo y múltiples tablas relacionadas

### Datasets Complementarios

- **[Give Me Some Credit](https://www.kaggle.com/c/GiveMeSomeCredit)** — Historial de crédito con indicadores de mora
- **[Loan Prediction Dataset](https://www.kaggle.com/datasets/altruistdelhite04/loan-prediction-problem-dataset)** — Dataset de predicción de aprobación de préstamos
- **[Lending Club Loan Data](https://www.kaggle.com/datasets/wordsforthewise/lending-club)** — Datos reales de una plataforma de préstamos P2P

### Información Disponible en los Datasets

Los datasets contienen millones de registros relacionados con:

- Clientes
- Solicitudes de crédito
- Historial financiero
- Pagos y mora
- Endeudamiento e ingresos
- Comportamiento crediticio
- Historial de préstamos
- Eventos financieros
- Validaciones y recaudos
- Información temporal
- Comportamiento de pago

> La información incluye **datos estructurados y semiestructurados** con relaciones complejas entre clientes, créditos, pagos y comportamiento financiero histórico.

---

## Escenario Esperado

La organización espera que el equipo sea capaz de:

- Comprender el negocio financiero
- Analizar grandes volúmenes de información
- Detectar problemas de calidad de datos
- Identificar patrones de comportamiento
- Consolidar información histórica
- Construir métricas confiables
- Facilitar análisis de riesgo
- Mejorar trazabilidad operativa
- Generar análisis escalables

### La Solución Debe Considerar Escenarios Reales Como

- Crecimiento continuo
- Grandes históricos financieros
- Eventos masivos diarios
- Datos corruptos y registros duplicados
- Información faltante
- Retrasos en sincronización
- Cambios en estructuras de datos
- Múltiples fuentes heterogéneas
- Análisis complejos de comportamiento temporal