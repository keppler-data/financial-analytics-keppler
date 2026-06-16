import os
import re
import json
import logging
import requests
import pandas as pd
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from io import BytesIO
from datetime import datetime

logger = logging.getLogger(__name__)

LOG_PATTERN = r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<service>\w+) (?P<message>.+)"


def _validate_date_format(date: str) -> tuple[str, str, str]:
    """Validate and parse a date string in YYYY-MM-DD format."""
    parts = date.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date format '{date}': expected YYYY-MM-DD")
    year, month, day = parts
    if not (len(year) == 4 and len(month) == 2 and len(day) == 2):
        raise ValueError(f"Invalid date format '{date}': expected YYYY-MM-DD")
    return year, month, day


class APIIngester:
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url or os.getenv(
            "KEPLER_API_URL", "https://api.keplerfintech.local/v1"
        )
        self.api_key = api_key or os.getenv("KEPLER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required: provide via constructor argument or KEPLER_API_KEY env var"
            )
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            self.s3 = boto3.client("s3")
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                "Failed to initialize S3 client; check AWS credentials"
            ) from exc

    def fetch_and_upload(
        self, dataset_endpoint: str, date: str, bucket_name: str = "kepler-bronze"
    ):
        year, month, day = _validate_date_format(date)
        endpoint = f"{self.base_url}/{dataset_endpoint}"
        params = {"date": date, "limit": 10000}

        try:
            response = requests.get(
                endpoint, headers=self.headers, params=params, timeout=30
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"API request failed for endpoint '{dataset_endpoint}' on date {date}: {exc}"
            ) from exc

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"API returned HTTP {response.status_code} for endpoint '{dataset_endpoint}' "
                f"on date {date}: {response.text[:200]}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid JSON response from endpoint '{dataset_endpoint}' on date {date}"
            ) from exc

        records = data.get("items", data if isinstance(data, list) else [])
        record_count = len(records)
        s3_key = f"financial/{dataset_endpoint}/year={year}/month={month}/day={day}/{dataset_endpoint}_{date}.json"

        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=json.dumps(data),
                ContentType="application/json",
                Metadata={
                    "source": dataset_endpoint,
                    "ingestion_date": datetime.utcnow().isoformat(),
                    "record_count": str(record_count),
                },
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                f"S3 upload failed for s3://{bucket_name}/{s3_key}: {exc}"
            ) from exc

        logger.info(
            "API ingestion succeeded: %d records uploaded to s3://%s/%s",
            record_count,
            bucket_name,
            s3_key,
        )
        return record_count


class CSVIngester:
    SUPPORTED_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

    def __init__(self):
        try:
            self.s3 = boto3.client("s3")
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                "Failed to initialize S3 client; check AWS credentials"
            ) from exc

    def ingest_csv(
        self,
        file_path: str,
        dataset_name: str,
        date: str,
        bucket_name: str = "kepler-bronze",
    ):
        year, month, day = _validate_date_format(date)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        df = None
        encoding_errors: list[str] = []
        for enc in self.SUPPORTED_ENCODINGS:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                break
            except UnicodeDecodeError as exc:
                encoding_errors.append(f"{enc}: {exc}")
                continue
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to read CSV file '{file_path}' with encoding '{enc}': {exc}"
                ) from exc

        if df is None:
            raise ValueError(
                f"Unable to decode CSV file '{file_path}' with any supported encoding. "
                f"Tried: {', '.join(self.SUPPORTED_ENCODINGS)}. "
                f"Errors: {'; '.join(encoding_errors)}"
            )

        df["_ingestion_source"] = "csv"
        df["_ingestion_date"] = date
        df["_file_name"] = os.path.basename(file_path)

        buffer = BytesIO()
        try:
            df.to_parquet(buffer, index=False, compression="snappy")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to convert CSV data to Parquet for '{file_path}': {exc}"
            ) from exc

        s3_key = f"financial/{dataset_name}/year={year}/month={month}/day={day}/{dataset_name}_{date}.parquet"

        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=buffer.getvalue(),
                ContentType="application/x-parquet",
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                f"S3 upload failed for s3://{bucket_name}/{s3_key}: {exc}"
            ) from exc

        logger.info(
            "CSV ingestion succeeded: %d rows uploaded to s3://%s/%s",
            len(df),
            bucket_name,
            s3_key,
        )
        return len(df)


class LogIngester:
    def __init__(self):
        try:
            self.s3 = boto3.client("s3")
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                "Failed to initialize S3 client; check AWS credentials"
            ) from exc

    def parse_and_upload_logs(
        self, log_file_path: str, date: str, bucket_name: str = "kepler-bronze"
    ):
        year, month, day = _validate_date_format(date)

        if not os.path.exists(log_file_path):
            raise FileNotFoundError(f"Log file not found: {log_file_path}")

        events = []
        skipped_lines = 0
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    match = re.match(LOG_PATTERN, stripped)
                    if match:
                        events.append(match.groupdict())
                    else:
                        skipped_lines += 1
        except IOError as exc:
            raise RuntimeError(
                f"Failed to read log file '{log_file_path}': {exc}"
            ) from exc

        if skipped_lines > 0:
            logger.warning(
                "Skipped %d lines that did not match expected log format in '%s'",
                skipped_lines,
                log_file_path,
            )

        if not events:
            logger.warning(
                "No parseable log events found in '%s'; nothing uploaded",
                log_file_path,
            )
            return 0

        ndjson_content = "\n".join([json.dumps(e) for e in events])
        s3_key = f"financial/app_logs/year={year}/month={month}/day={day}/app_logs_{date}.json"

        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=ndjson_content,
                ContentType="application/x-ndjson",
                Metadata={
                    "source": "app_logs",
                    "ingestion_date": datetime.utcnow().isoformat(),
                    "record_count": str(len(events)),
                },
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError(
                f"S3 upload failed for s3://{bucket_name}/{s3_key}: {exc}"
            ) from exc

        logger.info(
            "Log ingestion succeeded: %d events uploaded to s3://%s/%s",
            len(events),
            bucket_name,
            s3_key,
        )
        return len(events)
