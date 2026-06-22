from pipelines.tasks.homeCredit.download_task import (
    download_home_credit,
)
from pipelines.tasks.homeCredit.extract_task import (
    extract_home_credit,
)
from pipelines.tasks.homeCredit.parquet_task import (
    convert_home_credit_to_parquet,
)
from pipelines.utils.s3.upload import (
    upload_to_s3,
)

from pipelines.utils.s3.validate import (
    validate_s3_upload,
)
from pipelines.tasks.homeCredit.cleanup_task import (
    cleanup_home_credit,
)


def ingest_home_credit(
) -> list[tuple[str, str]]:
    """
    Ejecuta el flujo completo
    de Home Credit.
    """

    print(
        "Iniciando ingesta Home Credit"
    )

    zip_path = (
        download_home_credit()
    )

    print(
        f"ZIP PATH: {zip_path}"
    )

    extracted_path = (
        extract_home_credit(
            zip_path
        )
    )

    print(
        f"EXTRACT PATH: "
        f"{extracted_path}"
    )

    parquet_path = (
        convert_home_credit_to_parquet(
            extracted_path
        )
    )

    uploaded_files = (
    upload_to_s3(
        local_path=parquet_path,
        bucket_name="layer-keppler",
        s3_prefix="bronze/home_credit",
        )
    )

    for (
        bucket_name,
        s3_key
    ) in uploaded_files:

        validate_s3_upload(
            bucket_name,
            s3_key
        )

    cleanup_home_credit()

    print(
        "Ingesta Home Credit finalizada"
    )

    return uploaded_files

if __name__ == "__main__":
    result = ingest_home_credit()

    print(result)