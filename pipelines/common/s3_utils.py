"""Shared S3 helpers used by ingestion tasks."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import boto3


DEFAULT_BUCKET = "kepler-bronze"
_S3_CLIENT: boto3.client | None = None


def get_s3_client() -> boto3.client:
    """Return a module-level reusable S3 client."""
    global _S3_CLIENT
    if _S3_CLIENT is None:
        _S3_CLIENT = boto3.client("s3")
    return _S3_CLIENT


def build_s3_key(
    dataset_name: str,
    date: str,
    extension: str,
    prefix: str = "financial",
) -> str:
    """Build a date-partitioned S3 key.

    >>> build_s3_key("transactions", "2024-06-01", "json")
    'financial/transactions/year=2024/month=06/day=01/transactions_2024-06-01.json'
    """
    year, month, day = date.split("-")
    return (
        f"{prefix}/{dataset_name}"
        f"/year={year}/month={month}/day={day}"
        f"/{dataset_name}_{date}.{extension}"
    )


def upload_to_s3(
    key: str,
    body: str | bytes,
    content_type: str,
    bucket: str = DEFAULT_BUCKET,
    metadata: dict[str, str] | None = None,
) -> None:
    """Put an object into S3 with optional metadata."""
    kwargs: dict[str, Any] = {
        "Bucket": bucket,
        "Key": key,
        "Body": body,
        "ContentType": content_type,
    }
    if metadata:
        kwargs["Metadata"] = metadata
    get_s3_client().put_object(**kwargs)


def build_ingestion_metadata(
    source: str,
    record_count: int,
) -> dict[str, str]:
    """Return standard ingestion metadata attached to every S3 object."""
    return {
        "source": source,
        "ingestion_date": datetime.utcnow().isoformat(),
        "record_count": str(record_count),
    }
