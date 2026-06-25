# Ingestion

This folder contains utilities for ingesting local credit-risk datasets into a
Bronze S3 layout.

## Source datasets

The current ingestion script reads these local folders:

* `data/archive`
* `data/GiveMeSomeCredit`

## Script

Use:

```bash
python ingestion/ingest_local_datasets_to_s3.py --bucket your-bucket-name --mode local
```

The script supports three modes:

* `dry-run`: discovers files and writes a manifest only.
* `local`: copies files into a local S3-like mirror under `data/local_s3_mirror/`.
* `s3`: uploads the same files to a real AWS S3 bucket with `boto3`.

## 1. Validate locally

Run:

```bash
python ingestion/ingest_local_datasets_to_s3.py \
  --bucket your-bucket-name \
  --mode local
```

This creates a local mirror like:

```text
data/local_s3_mirror/your-bucket-name/financial-analytics/bronze/raw/
```

It also writes an ingestion manifest:

```text
data/local_s3_mirror/ingestion_manifest.json
```

Review the manifest before uploading to AWS. It includes the discovered files,
their sizes, content types, and target S3 destinations.

## 2. Upload to AWS S3

Configure AWS credentials using one of the standard AWS methods:

```bash
aws configure
```

or environment variables:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

Then run:

```bash
python ingestion/ingest_local_datasets_to_s3.py \
  --bucket your-bucket-name \
  --mode s3
```

By default, objects are written with this key pattern:

```text
financial-analytics/bronze/raw/<dataset_name>/ingestion_date=YYYY-MM-DD/<file_name>
```

Use `--prefix` to change the S3 prefix if your bucket uses a different layout:

```bash
python ingestion/ingest_local_datasets_to_s3.py \
  --bucket your-bucket-name \
  --prefix custom/prefix \
  --mode s3
```
