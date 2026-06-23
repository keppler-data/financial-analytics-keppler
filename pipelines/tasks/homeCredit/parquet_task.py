from pathlib import Path 
import pandas as pd 

HOME_CREDITS_DATASETS = {
    "application_train.csv",
    "bureau.csv",
    "bureau_balance.csv",
    "previous_application.csv",
    "POS_CASH_balance.csv", 
    "installments_payments.csv", 
    "credit_card_balance.csv"
}

def convert_home_credit_to_parquet(extracted_path: str) -> str: 

    """
    Convierte los datasets de Home Credit desde CSV a Parquet. 

    Parameters 
    --------------
    Extracted_path :  str
        Ruta donde se encuentran los archivos CSV extraídos. 

    Returns 
    --------------
    str 
        Ruta donde quedaron almacenados los archivos parquet. 
    """

    extracted_path = Path(extracted_path)

    parquet_path = extracted_path.parent / "parquet"

    parquet_path.mkdir(
        parents=True, 
        exist_ok=True
    )

    for csv_file in extracted_path.glob("*.csv"): 

        if csv_file.name not in HOME_CREDITS_DATASETS:
            print(f"Archivo ignorado: {csv_file.name}")
            continue

        print(f"Procesado: {csv_file.name}")

        df = pd.read_csv(csv_file)

        print(
            f"Filas: {len(df):,} | "
            f"Columnas: {len(df.columns)}"
        )

        parquet_file = (
            parquet_path /
            f"{csv_file.stem}.parquet"
        )

        df.to_parquet(
            parquet_file,
            engine="pyarrow",
            index=False,
        )

        print(
            f"Parquet generado: "
            f"{parquet_file.name}"
        )

        del df 

    return str(parquet_path)




