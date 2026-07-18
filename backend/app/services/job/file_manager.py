"""
FileManager handles uploaded files.

It saves uploaded files to disk in chunks, enforces the configured upload
size limit, and logs upload details.
"""

import logging
import time
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

class FileManager:

    @staticmethod
    def save_upload(file, destination: Path):
        """
        Synchronous, blocking file copy. Call this via a threadpool
        (see api/upload.py) - never call directly from an `async def`
        route, or it will block the event loop for the whole upload.
        """
        start = time.perf_counter()
        max_bytes = settings.max_upload_bytes

        destination.parent.mkdir(parents=True, exist_ok=True)

        written = 0
        with open(destination, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    buffer.close()
                    destination.unlink(missing_ok=True)
                    raise ValueError(
                        f"Upload exceeds max allowed size "
                        f"({max_bytes / (1024**3):.0f} GB)"
                    )
                buffer.write(chunk)

        logger.info(
            "upload saved",
            extra={
                "destination": str(destination),
                "size_mb": round(written / (1024 * 1024), 2),
                "duration_sec": round(time.perf_counter() - start, 2),
            },
        )