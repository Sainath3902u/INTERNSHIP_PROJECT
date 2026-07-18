"""
Job metadata store.

WHY SQLITE (not Postgres) 
-------------------------
Uses SQLite because it is lightweight, requires no extra setup, and
handles the application's current workload well. If the application
needs to support much higher concurrency in the future, this module
can be replaced with a Postgres implementation without affecting the
rest of the code.

CONCURRENCY NOTE
-----------------
Each function opens and closes its own short-lived connection rather than
holding one open for the app's lifetime. SQLite connections are not
guaranteed thread-safe when shared across threads without care, and job
writes here are infrequent (a handful of status transitions per job) - so
the overhead of open/close per call is negligible.
"""

import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings

# Valid job lifecycle states used throughout the application.
STATUS_CREATED = "created"        # Job created, no files uploaded yet
STATUS_UPLOADING = "uploading"    # Upload in progress
STATUS_QUEUED = "queued"          # Waiting to be evaluated
STATUS_RUNNING = "running"        # Evaluation in progress
STATUS_DONE = "done"              # Evaluation completed successfully
STATUS_FAILED = "failed"          # Evaluation failed


@dataclass
class JobRecord:
    job_id: str
    status: str
    created_at: float
    updated_at: float
    completed_at: Optional[float]
    error: Optional[str]
    result_downloaded_at: Optional[float]


def _connect() -> sqlite3.Connection:
    settings.job_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.job_db_path, timeout=30)
    # Enable WAL mode so reads and writes can happen at the same time.
    # This lets status checks continue while another thread updates a job.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


"""
Provide a database cursor and automatically handle
commit and connection cleanup.
"""
@contextmanager
def _cursor():
    conn = _connect()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the jobs table if it doesn't exist. Call once at app startup."""
    with _cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id                 TEXT PRIMARY KEY,
                status                 TEXT NOT NULL,
                created_at             REAL NOT NULL,
                updated_at             REAL NOT NULL,
                completed_at           REAL,
                error                  TEXT,
                result_downloaded_at   REAL
            )
        """)
        # Speed up queries that filter or sort jobs by status and update time.
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_status_updated
            ON jobs (status, updated_at)
        """)


def create_job() -> str:
    """"Create a new job, store it in the database, and return its ID."""
    job_id = uuid.uuid4().hex
    now = time.time()
    with _cursor() as cur:
        cur.execute(
            """
            INSERT INTO jobs (job_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (job_id, STATUS_CREATED, now, now),
        )
    return job_id


def job_exists(job_id: str) -> bool:
    with _cursor() as cur:
        cur.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
        return cur.fetchone() is not None


def get_job(job_id: str) -> Optional[JobRecord]:
    with _cursor() as cur:
        cur.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cur.fetchone()
        return _row_to_record(row) if row else None


def set_status(job_id: str, status: str, error: Optional[str] = None) -> None:
    """Update a job's status.

    Records the completion time automatically when a job finishes or
    fails, so completed jobs can be tracked and cleaned up later.
    """
    now = time.time()
    completed_at = now if status in (STATUS_DONE, STATUS_FAILED) else None

    with _cursor() as cur:
        if completed_at is not None:
            cur.execute(
                """
                UPDATE jobs
                SET status = ?, updated_at = ?, completed_at = ?, error = ?
                WHERE job_id = ?
                """,
                (status, now, completed_at, error, job_id),
            )
        else:
            cur.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, now, job_id),
            )


def mark_result_downloaded(job_id: str) -> None:
    """Record when a job's result is first downloaded.
    Used by the cleanup process to identify jobs whose results have already
    been retrieved.
    """
    with _cursor() as cur:
        cur.execute(
            """
            UPDATE jobs
            SET result_downloaded_at = COALESCE(result_downloaded_at, ?)
            WHERE job_id = ?
            """,
            (time.time(), job_id),
        )


def list_jobs(status: Optional[str] = None, limit: int = 200) -> list[JobRecord]:
    with _cursor() as cur:
        if status:
            cur.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        return [_row_to_record(row) for row in cur.fetchall()]


def find_cleanup_candidates(
    failed_after_seconds: float,
    done_after_seconds: float,
    abandoned_after_seconds: float,
) -> list[JobRecord]:
    """Return jobs that are eligible for cleanup.
    Includes completed, failed, and abandoned jobs that have exceeded the
    configured cleanup time.
    """
    now = time.time()
    with _cursor() as cur:
        cur.execute(
            """
            SELECT * FROM jobs
            WHERE
                (status = ? AND completed_at IS NOT NULL AND ? - completed_at > ?)
                OR
                (status = ? AND completed_at IS NOT NULL AND ? - completed_at > ?)
                OR
                (status IN (?, ?, ?, ?) AND ? - updated_at > ?)
            """,
            (
                STATUS_FAILED, now, failed_after_seconds,
                STATUS_DONE, now, done_after_seconds,
                STATUS_CREATED, STATUS_UPLOADING, STATUS_QUEUED, STATUS_RUNNING,
                now, abandoned_after_seconds,
            ),
        )
        return [_row_to_record(row) for row in cur.fetchall()]


def delete_job(job_id: str) -> None:
    with _cursor() as cur:
        cur.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))


def _row_to_record(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        job_id=row["job_id"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        completed_at=row["completed_at"],
        error=row["error"],
        result_downloaded_at=row["result_downloaded_at"],
    )