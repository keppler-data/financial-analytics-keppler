from pathlib import Path
import tempfile
import shutil


def cleanup_lending_club() -> None:

    temp_path = (
        Path(tempfile.gettempdir())
        / "lending_club"
    )

    if temp_path.exists():

        shutil.rmtree(
            temp_path
        )

        print(
            f"Eliminado: {temp_path}"
        )