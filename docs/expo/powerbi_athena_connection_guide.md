# Guía: Conectar Power BI (Desktop Gratuito) a AWS Athena

Esta guía te explicará paso a paso cómo conectar la capa **Gold** (nuestro modelo Copo de Nieve) alojada en AWS Athena con la versión gratuita de **Power BI Desktop**, para que puedas mostrar tableros analíticos impresionantes durante tu exposición.

---

## 1. Requisitos Previos

Antes de abrir Power BI, necesitas tener a la mano lo siguiente desde tu entorno de AWS:
1. **AWS Region:** La región donde está desplegado tu Athena (ejemplo: `us-east-1`).
2. **Access Key ID y Secret Access Key:** Credenciales de un usuario IAM que tenga permisos de lectura en S3 (sobre el bucket `keppler-data-architecture`) y permisos para ejecutar consultas en Athena.
3. **Controlador ODBC de Simba Athena (A veces requerido):** Aunque las versiones recientes de Power BI ya traen un conector nativo para Athena, internamente utilizan este controlador. Si Power BI te lanza un error de "driver faltante", debes descargar el "Simba Athena ODBC Driver" desde la página oficial de Amazon e instalarlo en Windows.

---

## 2. Conectando Power BI a Athena

1. Abre **Power BI Desktop**.
2. En la pantalla de inicio, haz clic en **Obtener datos** (Get Data) y selecciona **Más...** (More...).
3. En la barra de búsqueda escribe **Athena**.
4. Selecciona el conector **Amazon Athena** y haz clic en **Conectar**.

### 3. Configuración del Conector

Aparecerá una ventana de configuración de conexión. Llena los datos de la siguiente forma:

- **DSN (Opcional):** Déjalo en blanco si usas el conector directo.
- **Región:** Escribe la región de tu entorno AWS (ej. `us-east-1`).
- **DirectQuery o Importar:** 
  - **Importar (Recomendado para la Expo):** Descarga una copia de los datos a tu computadora. Es muchísimo más rápido para armar los gráficos y no te cobrará en AWS por cada clic que des en el dashboard.
  - **DirectQuery:** Consulta en tiempo real. Útil solo si los datos cambian cada minuto (no es nuestro caso) y puede generar costos adicionales en AWS Athena.

Haz clic en **Aceptar**.

### 4. Autenticación (Credenciales de AWS)

La siguiente ventana te pedirá cómo quieres autenticarte:
1. Selecciona la pestaña que dice **Access Key** o **Usuario IAM**.
2. **Nombre de usuario:** Pega tu `Access Key ID`.
3. **Contraseña:** Pega tu `Secret Access Key`.
4. Dale a **Conectar**.

---

## 5. Seleccionando el Modelo Copo de Nieve (Gold Layer)

Una vez conectado exitosamente, Power BI abrirá la ventana de **Navegador**. Verás el catálogo de bases de datos de AWS Glue.

1. Despliega `awsdatacatalog`.
2. Busca la base de datos `keppler_gold`.
3. Selecciona las casillas de las tablas maestras que creamos:
   - `fact_loan`
   - `dim_customer`
   - `dim_hc_details` (Opcional, si quieres analizar datos específicos de Home Credit)
   - `dim_lc_details` (Opcional, para Lending Club)
   - `dim_gmsc_details` (Opcional, para Give Me Some Credit)
   - `dim_lp_details` (Opcional, para Loan Prediction)
4. Haz clic en **Cargar**. (Esto tomará unos minutos mientras descarga los archivos Parquet desde S3).

---

## 6. Configurando el Modelo Relacional (El Copo de Nieve)

Para que Power BI entienda cómo cruzar la información de los bancos, debemos armar las relaciones:

1. Ve a la vista de **Modelo** (el ícono de los tres cuadritos conectados en la barra lateral izquierda).
2. Arrastra la columna **`customer_key`** de la tabla `dim_customer` hacia la columna **`customer_key`** de la tabla `fact_loan`. Esto creará una relación **1 a Muchos (1:*)**.
3. Arrastra la columna **`loan_key`** de `dim_hc_details` hacia el **`loan_key`** de `fact_loan` (relación 1:1 o 1:* dependiendo de la granularidad).
4. Repite el paso 3 para las otras tablas satélite (`dim_lc_details`, etc.).

---

## 7. ¡A Graficar! (Ideas para la Exposición)

Ahora ve a la vista de **Informe** (el ícono de gráfico de barras) y empieza a arrastrar variables:

- **Total de Préstamos por Banco:** Crea un *Gráfico de anillos*. Arrastra `source_system` de `fact_loan` a Leyenda, y haz un recuento de `loan_key` en Valores.
- **Tasa de Default por Género:** Usa un *Gráfico de columnas apiladas*. Arrastra `gender` de `dim_customer` al Eje X, y el promedio de `target` de `fact_loan` al Eje Y. ¡Aquí se demuestra la magia de cruzar la tabla de hechos con la dimensión universal!
- **Ingreso Anual vs Monto del Préstamo:** Crea un *Gráfico de dispersión*. Eje X: `annual_income`, Eje Y: `loan_amount`, desglosado por `source_system` en Leyenda.

¡Listo! Con esto tendrás un dashboard profesional conectado directamente a un Data Lake Serverless en AWS, orquestado con lo último en ingeniería de datos.
