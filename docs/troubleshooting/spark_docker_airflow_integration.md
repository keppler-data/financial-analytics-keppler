# Desafíos de Integración: Spark, Docker y Airflow

Este documento recopila los problemas técnicos encontrados al intentar orquestar trabajos de Apache Spark desde Apache Airflow utilizando `SSHOperator` hacia un clúster de Spark desplegado en Docker, así como las soluciones definitivas implementadas.

## 1. La Inconsistencia del `user.home` en Java y la Caché de Ivy (Crash Fatal)

### Desafío
Al enviar trabajos con dependencias externas usando la bandera `--packages` (ej. `org.apache.hadoop:hadoop-aws:3.4.0`), `spark-submit` utiliza internamente Ivy para descargar los paquetes antes de contactar al Spark Master. 

En la infraestructura, el contenedor de Spark (basado en `apache/spark`) corría forzando el usuario `1000:0` (mapeado al usuario `ubuntu` de la EC2), cuyo `HOME` a nivel de variables de entorno de Docker era `/opt/spark/work`. Sin embargo, la Máquina Virtual de Java (JVM) resolvía el `user.home` de forma estricta según el estándar de Linux (`/home/ubuntu`). 

Como la carpeta `/home/ubuntu` no existía dentro del contenedor, el manejador de Ivy crasheaba silenciosamente con un `java.io.FileNotFoundException`, causando que el `spark-submit` fallara con `exit status 1` sin que la tarea siquiera llegara a registrarse en la UI de Spark.

### Solución Implementada (Opción Recomendada)
En lugar de forzar a Java a cambiar su resolución de usuarios inyectando variables (`SPARK_SUBMIT_OPTS`), lo cual causaba efectos colaterales, **se forzó explícitamente la ubicación de la caché de Ivy**.

Se agregó la siguiente bandera al comando del DAG:
```bash
--conf spark.jars.ivy=/opt/spark/work/.ivy
```
Esto anula la dependencia de Ivy respecto a la resolución de directorios personales de Java, garantizando que escriba en el volumen persistente correcto donde el contenedor tiene plenos permisos.

---

## 2. El Falso Positivo de `UserGroupInformation` (WARNING de Hadoop)

### Desafío
Los logs de Airflow mostraban repetidamente una traza inmensa de advertencias (Warnings) de la clase de Java `org.apache.hadoop.security.UserGroupInformation`, indicando fallas en `doSubjectLogin`. Esto nos llevó a pensar erróneamente que el proceso abortaba porque Java no encontraba el UID 1000 en el archivo `/etc/passwd` del contenedor.

### Diagnóstico Real
Tras pruebas directas en la consola (`whoami` retornando `ubuntu`), descubrimos que el usuario sí existía y los permisos de las carpetas eran los correctos (`drwxrwxr-x 4 ubuntu 1000`). La traza de `UserGroupInformation` era simplemente el ruido clásico (WARNING) que imprime Hadoop al intentar inicializar protocolos de seguridad (como Kerberos) antes de hacer fallback exitoso a autenticación simple (Simple Auth). El verdadero causante de la muerte del proceso era el error de Ivy detallado en el punto 1.

---

## 3. Retención de Puertos Estáticos (`TIME_WAIT` / `BindException`)

### Desafío
Por requisitos de seguridad de AWS (Security Groups para la escritura en S3), el DAG estaba obligado a usar puertos estáticos para el Driver y el BlockManager:
```bash
--conf spark.driver.port=7078
--conf spark.driver.blockManager.port=7079
--conf spark.blockManager.port=37000
```
Cuando las tareas en Airflow se ejecutaban demasiado rápido, el sistema operativo (Linux) mantenía los puertos retenidos en estado `TIME_WAIT` durante 60 segundos tras finalizar un proceso. Si la siguiente tarea intentaba arrancar de inmediato, Spark crasheaba con `java.net.BindException: Address already in use`.

### Solución
- Se configuró el DAG con `max_active_tasks=1` para forzar ejecución secuencial.
- (Próximos pasos si la latencia es crítica): Agregar pausas lógicas (Time Sleeps) entre tareas en Airflow, o implementar liberación forzada de sockets (SO_REUSEADDR) si Spark lo permite, para evitar las colisiones en Security Groups altamente restrictivos.

---

## Recomendaciones a Largo Plazo

Si se tiene control total sobre el proceso de construcción de las imágenes Docker (es decir, creando un `Dockerfile` propio basado en la imagen de Apache Spark), la recomendación absoluta es **corregir al usuario dentro de la imagen** para que `user.home` (de Java) y `HOME` (de Docker) coincidan de forma natural. 

Esto se puede lograr modificando el home real con:
```dockerfile
RUN usermod -d /opt/spark/work ubuntu
```
Al hacer esto, todas las herramientas nativas del ecosistema Hadoop/Java resolverán las rutas de caché, temporales y logs sin requerir banderas explícitas ni hacks en la línea de comandos, entregando la arquitectura más limpia y mantenible a futuro.
