from pathlib import Path
import shutil
import time


MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB safety cap


class FileManager:

    @staticmethod
    def save_upload(file, destination: Path):
        """
        Synchronous, blocking file copy. Call this via a threadpool
        (see api/upload.py) - never call directly from an `async def`
        route, or it will block the event loop for the whole upload.
        """
        start = time.perf_counter()

        destination.parent.mkdir(parents=True, exist_ok=True)

        written = 0
        with open(destination, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    buffer.close()
                    destination.unlink(missing_ok=True)
                    raise ValueError(
                        f"Upload exceeds max allowed size "
                        f"({MAX_UPLOAD_BYTES / (1024**3):.0f} GB)"
                    )
                buffer.write(chunk)

        print(f"SERVER SAVE: {written / (1024*1024):.2f} MB in "
              f"{time.perf_counter() - start:.2f}s")
