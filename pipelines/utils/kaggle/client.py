# pipelines/utils/kaggle/client.py

import os

from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import (
    KaggleApi,
)


def get_kaggle_client() -> KaggleApi:

    load_dotenv()

    username = os.getenv(
        "KAGGLE_USERNAME"
    )

    key = os.getenv(
        "KAGGLE_KEY"
    )

    if not username:
        raise ValueError(
            "KAGGLE_USERNAME no encontrado"
        )

    if not key:
        raise ValueError(
            "KAGGLE_KEY no encontrado"
        )

    os.environ[
        "KAGGLE_USERNAME"
    ] = username

    os.environ[
        "KAGGLE_KEY"
    ] = key

    api = KaggleApi()

    api.authenticate()

    return api