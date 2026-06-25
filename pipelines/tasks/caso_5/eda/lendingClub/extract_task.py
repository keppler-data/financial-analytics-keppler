from pathlib import Path
import zipfile


def extract_lending_club(
    zip_path: str
) -> str:

    zip_path = Path(zip_path)

    if not zip_path.exists():

        raise FileNotFoundError(
            f"No existe el archivo: {zip_path}"
        )

    if not zip_path.is_file():

        raise ValueError(
            f"No es un archivo ZIP: {zip_path}"
        )

    extract_path = (
        zip_path.parent
        / "extracted"
    )

    extract_path.mkdir(
        parents=True,
        exist_ok=True
    )

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as zip_ref:

        zip_ref.extractall(
            extract_path
        )

    print(
        f"Archivos extraídos en: "
        f"{extract_path}"
    )

    return str(extract_path)