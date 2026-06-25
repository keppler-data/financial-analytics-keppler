import boto3

from botocore.exceptions import (
    ClientError,
)


def validate_s3_upload(
    bucket_name: str,
    s3_key: str
) -> None:
    """
    Valida que el archivo exista
    y no esté vacío.
    """

    s3_client = boto3.client(
        "s3"
    )

    try:

        response = (
            s3_client.head_object(
                Bucket=bucket_name,
                Key=s3_key
            )
        )

        file_size = response[
            "ContentLength"
        ]

        if file_size == 0:

            raise ValueError(
                "Archivo vacío."
            )

        print(
            f"Validado: "
            f"s3://{bucket_name}/{s3_key}"
        )

    except ClientError as error:

        raise FileNotFoundError(
            f"No existe: "
            f"s3://{bucket_name}/{s3_key}"
        ) from error