from pipelines.tasks.caso_5.eda.lendingClub.download_task import (
    download_lending_club,
)

from pipelines.tasks.caso_5.eda.lendingClub.accepted.parquet_task import (
    convert_lending_accepted_to_parquet,
)

from pipelines.utils.s3.upload import (
    upload_to_s3
)

from pipelines.utils.s3.validate import (
    validate_s3_upload,
)

from pipelines.tasks.caso_5.eda.lendingClub.cleanup_task import (
    cleanup_lending_club,
)


def ingest_lending_accepted() -> str:

    print(
        "Iniciando ingesta Lending Accepted"
    )

    dataset_path = (
        download_lending_club()
    )

    parquet_dir = (
        convert_lending_accepted_to_parquet(
            dataset_path
        )
    )

    uploaded_files = (
    upload_to_s3(
        local_path=parquet_dir,
        bucket_name="layer-keppler",
        s3_prefix="bronze/lending-club",
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

    cleanup_lending_club()

    print(
        "Ingesta completada."
    )

    return uploaded_files

if __name__ == "__main__":
    result = ingest_lending_accepted()

    print(result)