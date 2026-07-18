"""
Application logging configuration.

Configures structured logging for the application. Modules can create a
logger with `logging.getLogger(__name__)` and log messages with
additional context using the `extra` parameter.

Use `get_job_logger(job_id)` to automatically include the job ID in all
log messages for a specific job.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    # Standard LogRecord attributes. Any other attributes are treated as
    # caller-provided `extra` fields and included in the JSON output.
    _RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in self._RESERVED and key != "message":
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Call once at app startup (see main.py)."""
    root = logging.getLogger()
    root.setLevel(level)

    # Replace existing handlers so all application and framework logs use
    # the same JSON formatter.
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def get_job_logger(job_id: str) -> logging.LoggerAdapter:
    """Return a job-specific logger."""
    base = logging.getLogger("app.job")
    return logging.LoggerAdapter(base, {"job_id": job_id})