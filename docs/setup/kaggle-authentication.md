# Kaggle Authentication Strategy

## Current Implementation

Actualmente, durante el desarrollo local, la autenticación con Kaggle utiliza el archivo:

```text
~/.kaggle/kaggle.json
```

Este enfoque simplifica las pruebas locales y permite descargar datasets directamente desde la API de Kaggle.

## Limitation

La dependencia de un archivo local presenta varios inconvenientes:

* No es portable entre entornos.
* Requiere configuración manual en cada máquina.
* No es adecuada para contenedores Docker.
* Dificulta la ejecución distribuida en Airflow Workers.

## Target Architecture

Para entornos de integración y producción, la autenticación será gestionada mediante variables de entorno.

```env
KAGGLE_USERNAME=
KAGGLE_KEY=
```

Las credenciales serán inyectadas a los contenedores de Airflow mediante archivos `.env` o servicios de gestión de secretos.

## Benefits

* Desacopla la aplicación de archivos locales.
* Facilita despliegues en EC2.
* Compatible con Docker y Airflow Workers.
* Permite futuras integraciones con AWS Secrets Manager.

## Planned Flow

```text
AWS Secrets Manager / .env
            ↓
      Airflow Worker
            ↓
      Kaggle API
            ↓
      Dataset Download
```

## Status

* [x] Autenticación local mediante `kaggle.json`
* [ ] Migración a variables de entorno
* [ ] Integración con AWS Secrets Manager

```
```