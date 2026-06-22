from pathlib import Path
import tempfile

from kaggle.api.kaggle_api_extended import KaggleApi


def download_home_credit() -> str:
    """
    Descarga Home Credit desde Kaggle y
    retorna la ruta del archivo ZIP.
    """

    download_path = (
        Path(tempfile.gettempdir())
        / "home_credit"
    )

    download_path.mkdir(
        parents=True,
        exist_ok=True
    )

    api = KaggleApi()

    api.authenticate()

    api.competition_download_files(
        competition="home-credit-default-risk",
        path=str(download_path)
    )

    zip_files = list(
        download_path.glob("*.zip")
    )

    if not zip_files:

        raise FileNotFoundError(
            f"No se encontró ningún ZIP en: "
            f"{download_path}"
        )

    zip_file = zip_files[0]

    print(
        f"ZIP encontrado: {zip_file}"
    )

    return str(zip_file)