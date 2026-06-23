from pathlib import Path
import tempfile
import shutil


def cleanup_home_credit() -> None:
    """
    Elimina todos los archivos temporales
    generados durante la ingesta.
    """

    temp_path = (
        Path(tempfile.gettempdir())
        / "home_credit"
    )

    if temp_path.exists():

        shutil.rmtree(temp_path)

        print(
            f"Directorio eliminado: "
            f"{temp_path}"
        )

    else:

        print(
            f"No existe: {temp_path}"
        )
