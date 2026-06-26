# Data Warehouse Design Specification

## 1. Introducción

El presente documento describe el diseño del Data Warehouse desarrollado para una entidad financiera enfocada en la gestión de préstamos y microcréditos. Su objetivo es proporcionar un modelo analítico capaz de integrar información proveniente de múltiples fuentes de datos bajo una estructura unificada, facilitando el análisis histórico, la generación de indicadores y la toma de decisiones.

El modelo fue diseñado siguiendo la metodología de Ralph Kimball, utilizando un esquema estrella (Star Schema), dimensiones conformadas y tablas de hechos que representan los principales procesos del negocio.

---

# 2. Objetivos del Data Warehouse

El Data Warehouse tiene como finalidad consolidar la información financiera y operacional para responder preguntas relacionadas con:

* Riesgo crediticio.
* Desempeño del portafolio.
* Comportamiento de los clientes.
* Aprobación y rechazo de solicitudes.
* Evolución de la cartera.
* Mora e incumplimiento.
* Recuperación de pagos.

El modelo está diseñado para soportar análisis históricos y facilitar la incorporación de nuevas fuentes de información sin modificar su estructura principal.

---

# 3. Modelo Dimensional

El modelo dimensional se organiza alrededor de tres procesos de negocio que representan el ciclo de vida de un crédito.

* Originación del crédito.
* Otorgamiento del crédito.
* Gestión de pagos.

Cada proceso se representa mediante una tabla de hechos y comparte un conjunto de dimensiones conformadas que proporcionan el contexto necesario para el análisis.

## Componentes del modelo

### Dimensiones

| Dimensión         | Propósito                             |
| ----------------- | ------------------------------------- |
| DIM_CUSTOMER      | Información del cliente.              |
| DIM_TIME          | Contexto temporal de los eventos.     |
| DIM_PRODUCT       | Catálogo de productos financieros.    |
| DIM_RISK_SEGMENT  | Clasificación corporativa del riesgo. |
| DIM_SOURCE_SYSTEM | Trazabilidad del origen de los datos. |

### Tablas de hechos

| Tabla            | Proceso representado                 |
| ---------------- | ------------------------------------ |
| FACT_APPLICATION | Solicitudes de crédito.              |
| FACT_LOAN        | Créditos desembolsados.              |
| FACT_PAYMENT     | Pagos realizados sobre los créditos. |

---

# 4. Dimensiones del Modelo

Las dimensiones almacenan información descriptiva utilizada para contextualizar los procesos del negocio.

## DIM_CUSTOMER

Representa la visión corporativa del cliente y centraliza sus principales características demográficas y financieras. Se implementa como una dimensión de cambio lento (SCD Tipo 2) para conservar el historial de cambios relevantes.

**Relaciones**

* FACT_APPLICATION
* FACT_LOAN
* FACT_PAYMENT

---

## DIM_TIME

Permite analizar el comportamiento del negocio desde una perspectiva temporal, facilitando comparaciones entre días, meses, trimestres y años.

**Relaciones**

* FACT_APPLICATION
* FACT_LOAN
* FACT_PAYMENT

---

## DIM_PRODUCT

Contiene el catálogo de productos financieros ofrecidos por la entidad y permite comparar el desempeño de cada línea de negocio.

**Relaciones**

* FACT_APPLICATION
* FACT_LOAN
* FACT_PAYMENT

---

## DIM_RISK_SEGMENT

Agrupa la clasificación de riesgo utilizada por la organización para segmentar clientes y créditos, permitiendo analizar el comportamiento del portafolio según el nivel de riesgo.

**Relaciones**

* FACT_APPLICATION
* FACT_LOAN
* FACT_PAYMENT

---

## DIM_SOURCE_SYSTEM

Identifica el origen de los datos integrados en el Data Warehouse, garantizando la trazabilidad y el control sobre las diferentes fuentes de información.

**Relaciones**

* FACT_APPLICATION
* FACT_LOAN
* FACT_PAYMENT

---

# 5. Tablas de Hechos

Las tablas de hechos representan los procesos principales del negocio y almacenan las métricas utilizadas para el análisis.

## FACT_APPLICATION

Representa las solicitudes de crédito realizadas por los clientes.

**Granularidad**

Una fila corresponde a una solicitud de crédito.

**Principales métricas**

* Monto solicitado.
* Monto aprobado.
* Resultado de la solicitud.

---

## FACT_LOAN

Representa los créditos aprobados y desembolsados.

**Granularidad**

Una fila corresponde a un crédito otorgado.

**Principales métricas**

* Monto del crédito.
* Tasa de interés.
* Plazo.
* Saldo pendiente.

---

## FACT_PAYMENT

Representa los pagos registrados durante la vida del crédito.

**Granularidad**

Una fila corresponde a un pago realizado.

**Principales métricas**

* Valor pagado.
* Capital abonado.
* Intereses pagados.
* Días de mora.

---

# 6. Relaciones del Modelo

El modelo sigue un esquema estrella donde las dimensiones proporcionan contexto a las tablas de hechos mediante relaciones uno a muchos (1:N).

* Un cliente puede realizar múltiples solicitudes.
* Un cliente puede obtener múltiples créditos.
* Un crédito puede registrar múltiples pagos.
* Todas las tablas de hechos comparten las mismas dimensiones para mantener consistencia analítica.

Este enfoque permite reutilizar la información descriptiva y simplifica las consultas realizadas por herramientas de inteligencia de negocio.

---

# 7. Decisiones de Diseño

Durante el diseño del Data Warehouse se adoptaron las siguientes decisiones arquitectónicas:

* Implementar un **Star Schema** para optimizar el rendimiento analítico.
* Utilizar **dimensiones conformadas** para garantizar una única definición de cliente, producto, tiempo y riesgo.
* Emplear **claves sustitutas** para desacoplar el modelo de los sistemas fuente.
* Conservar el historial del cliente mediante **SCD Tipo 2** en `DIM_CUSTOMER`.
* Modelar los procesos de negocio mediante tres tablas de hechos independientes, respetando la granularidad de cada evento.

---

# 8. Beneficios del Modelo

El modelo dimensional permite:

* Integrar múltiples fuentes de información bajo una estructura común.
* Analizar el ciclo de vida completo del crédito.
* Construir indicadores financieros consistentes.
* Facilitar el análisis histórico del comportamiento de clientes y portafolios.
* Escalar el Data Warehouse incorporando nuevos procesos de negocio sin modificar el diseño existente.

---

# 9. Conclusión

El modelo dimensional propuesto constituye la base analítica del proyecto, proporcionando una estructura organizada y escalable para el análisis de información financiera. La separación entre dimensiones y tablas de hechos, junto con el uso de dimensiones conformadas, garantiza consistencia en los indicadores y facilita la generación de reportes estratégicos orientados a la toma de decisiones.

Su diseño permite representar el ciclo de vida del crédito desde la solicitud hasta el pago, ofreciendo una visión integrada del negocio y una base sólida para futuras iniciativas de analítica y Business Intelligence.
