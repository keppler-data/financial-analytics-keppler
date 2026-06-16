import os
import re
import json
import requests
import pandas as pd
import boto3
from io import BytesIO
from datetime import datetime

LOG_PATTERN = r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<service>\w+) (?P<message>.+)'

REQUEST_TIMEOUT_SECONDS = 30
_VALID_ENDPOINT_RE = re.compile(r'^[a-zA-Z0-9_]+$')

class APIIngester:
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url or os.getenv("KEPLER_API_URL")
        if not self.base_url:
            raise ValueError("KEPLER_API_URL must be set via argument or environment variable")
        self.api_key = api_key or os.getenv("KEPLER_API_KEY")
        if not self.api_key:
            raise ValueError("KEPLER_API_KEY must be set via argument or environment variable")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.s3 = boto3.client('s3')

    def fetch_and_upload(self, dataset_endpoint: str, date: str, bucket_name: str = 'kepler-bronze'):
        if not _VALID_ENDPOINT_RE.match(dataset_endpoint):
            raise ValueError(f"Invalid dataset_endpoint: {dataset_endpoint!r}")
        endpoint = f"{self.base_url}/{dataset_endpoint}"
        params = {"date": date, "limit": 10000}
        response = requests.get(endpoint, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        records = data.get('items', data if isinstance(data, list) else [])
        record_count = len(records)
        year, month, day = date.split('-')
        s3_key = f"financial/{dataset_endpoint}/year={year}/month={month}/day={day}/{dataset_endpoint}_{date}.json"
        self.s3.put_object(
            Bucket=bucket_name, Key=s3_key, Body=json.dumps(data), ContentType='application/json',
            Metadata={'source': dataset_endpoint, 'ingestion_date': datetime.utcnow().isoformat(), 'record_count': str(record_count)}
        )
        print(f"✅ API Ingestion exitosa: {record_count} registros en s3://{bucket_name}/{s3_key}")
        return record_count

class CSVIngester:
    SUPPORTED_ENCODINGS = ['utf-8', 'latin-1', 'cp1252']
    def __init__(self):
        self.s3 = boto3.client('s3')

    def ingest_csv(self, file_path: str, dataset_name: str, date: str, bucket_name: str = 'kepler-bronze'):
        resolved = os.path.realpath(file_path)
        allowed_prefix = os.path.realpath("/opt/airflow/data")
        if not resolved.startswith(allowed_prefix + os.sep):
            raise ValueError(f"file_path must be under {allowed_prefix}: got {resolved}")
        df = None
        for enc in self.SUPPORTED_ENCODINGS:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise ValueError(f"❌ Error al codificar el archivo {file_path}")
        df['_ingestion_source'] = 'csv'
        df['_ingestion_date'] = date
        df['_file_name'] = os.path.basename(file_path)
        buffer = BytesIO()
        df.to_parquet(buffer, index=False, compression='snappy')
        year, month, day = date.split('-')
        s3_key = f"financial/{dataset_name}/year={year}/month={month}/day={day}/{dataset_name}_{date}.parquet"
        self.s3.put_object(Bucket=bucket_name, Key=s3_key, Body=buffer.getvalue(), ContentType='application/x-parquet')
        print(f"✅ CSV Ingestion exitosa: {len(df)} filas en s3://{bucket_name}/{s3_key}")
        return len(df)

class LogIngester:
    def __init__(self):
        self.s3 = boto3.client('s3')

    def parse_and_upload_logs(self, log_file_path: str, date: str, bucket_name: str = 'kepler-bronze'):
        events = []
        if not os.path.exists(log_file_path):
            print(f"⚠️ Archivo ausente: {log_file_path}")
            return 0
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(LOG_PATTERN, line.strip())
                if match:
                    events.append(match.groupdict())
        if not events:
            return 0
        ndjson_content = "\n".join([json.dumps(e) for e in events])
        year, month, day = date.split('-')
        s3_key = f"financial/app_logs/year={year}/month={month}/day={day}/app_logs_{date}.json"
        self.s3.put_object(
            Bucket=bucket_name, Key=s3_key, Body=ndjson_content, ContentType='application/x-ndjson',
            Metadata={'source': 'app_logs', 'ingestion_date': datetime.utcnow().isoformat(), 'record_count': str(len(events))}
        )
        print(f"✅ Log Ingestion exitosa: {len(events)} eventos en s3://{bucket_name}/{s3_key}")
        return len(events)