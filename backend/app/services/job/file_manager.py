from pathlib import Path
import shutil
import time


class FileManager:

    @staticmethod
    def save_upload(file, destination: Path):
        start = time.perf_counter()

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(destination, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        print(
            f"SERVER SAVE: "
            f"{time.perf_counter() - start:.2f}s"
        )