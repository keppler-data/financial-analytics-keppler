from pathlib import Path

import pandas as pd


def convert_lending_rejected_to_parquet(
    dataset_path: str
) -> str:
    """
    Convierte Rejected Loans a Parquet.
    """

    dataset_path = Path(
        dataset_path
    )

    csv_file = (
        dataset_path
        / "rejected_2007_to_2018Q4.csv.gz"
    )

    if not csv_file.exists():

        raise FileNotFoundError(
            f"No existe: {csv_file}"
        )

    parquet_dir = (
        dataset_path
        / "parquet"
    )

    parquet_dir.mkdir(
        exist_ok=True
    )

    parquet_file = (
        parquet_dir
        / "rejected_2007_to_2018Q4.parquet"
    )

    print(
        "Leyendo Rejected Loans..."
    )

    df = pd.read_csv(
        csv_file,
        compression="gzip",
        low_memory=False
    )

    df.to_parquet(
        parquet_file,
        index=False
    )

    print(
        f"Parquet generado: "
        f"{parquet_file}"
    )

    return str(
        parquet_dir
    )