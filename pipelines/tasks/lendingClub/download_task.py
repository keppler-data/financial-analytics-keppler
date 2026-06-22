from pathlib import Path
import tempfile

from kaggle.api.kaggle_api_extended import KaggleApi


def download_lending_club() -> str:
    """
    Descarga Lending Club desde Kaggle y
    retorna la ruta del archivo descargado.
    """

    download_path = (
        Path(tempfile.gettempdir())
        / "lending_club"
    )

    download_path.mkdir(
        parents=True,
        exist_ok=True
    )

    api = KaggleApi()

    api.authenticate()

    api.dataset_download_files(
        dataset="wordsforthewise/lending-club",
        path=str(download_path),
        unzip=True
    )

    print(
        f"Dataset descargado en: {download_path}"
    )

    return str(download_path)