from pathlib import Path

import boto3


def upload_to_s3(
    local_path: str,
    bucket_name: str,
    s3_prefix: str,
) -> list[tuple[str, str]]:
    """
    Carga uno o varios parquet a S3.

    Returns
    -------
    list[tuple[str, str]]
    """

    s3_client = boto3.client(
        "s3"
    )

    local_path = Path(
        local_path
    )

    uploaded_files = []

    for parquet_file in local_path.glob(
        "*.parquet"
    ):

        s3_key = (
            f"{s3_prefix}/"
            f"{parquet_file.name}"
        )

        s3_client.upload_file(
            str(parquet_file),
            bucket_name,
            s3_key
        )

        uploaded_files.append(
            (
                bucket_name,
                s3_key
            )
        )

        print(
            f"Subido: "
            f"s3://{bucket_name}/{s3_key}"
        )

    return uploaded_files