"""
Job metadata store.

WHY THIS EXISTS
----------------
Before this, "does the job exist" meant "does the folder exist" - there was
no status, no timestamps, no way to tell a finished job from an abandoned
one. That made three things impossible to build properly:
  1. Status polling for the frontend (was it created / running / done / failed?)
  2. A storage cleanup policy (cleanup needs to know AGE + STATUS, not just
     "this folder is untouched" - folder mtime is a bad proxy for "is this
     job safe to delete", since a slow upload could look identical to an
     abandoned one).
  3. A job list / admin view for the dashboard.

WHY SQLITE (not Postgres) FOR NOW
----------------------------------
This service processes one benchmark job at a time per phase-set (3
evaluation phases running concurrently, not hundreds of concurrent jobs).
SQLite in WAL mode comfortably handles that concurrency level, needs zero
extra infrastructure to run, and the schema is trivial. If this ever scales
to many concurrent users hammering the API, swapping this module for a
Postgres-backed one is a contained change - every caller goes through the
functions in this file, never raw SQL, so the storage engine is an
implementation detail.

CONCURRENCY NOTE
-----------------
Each function opens and closes its own short-lived connection rather than
holding one open for the app's lifetime. SQLite connections are not
guaranteed thread-safe when shared across threads without care, and job
writes here are infrequent (a handful of status transitions per job) - so
the overhead of open/close per call is negligible and it avoids an entire
class of "which thread owns this connection" bugs.
"""

import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings

# Valid job lifecycle states. Enforced at the Python layer (not a DB CHECK
# constraint) to keep this file dependency-free and easy to read; the set of
# valid transitions is small enough that a shared constant is sufficient.
STATUS_CREATED = "created"        # job dir made, no files uploaded yet
STATUS_UPLOADING = "uploading"    # at least one file uploaded
STATUS_QUEUED = "queued"          # evaluation requested, not yet started
STATUS_RUNNING = "running"        # ingestion + evaluation in progress
STATUS_DONE = "done"              # result.json written successfully
STATUS_FAILED = "failed"          # ingestion or evaluation raised


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
    # WAL mode lets readers (status polling) proceed without blocking on a
    # concurrent writer (a status update from a running job) - important
    # since polling and job execution happen from different threads.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


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
        # Cleanup and job-list queries both filter/sort by status and age -
        # this index keeps those cheap even as the jobs table grows.
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_jobs_status_updated
            ON jobs (status, updated_at)
        """)


def create_job() -> str:
    """Insert a new job row in CREATED state and return its id.

    UUID4 is kept (not swapped for an auto-increment int) because job ids
    are exposed in URLs - sequential ids would let a client enumerate other
    users' jobs by incrementing a number.
    """
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
    """Update a job's status. Pass `error` when transitioning to FAILED.

    completed_at is stamped automatically on DONE/FAILED so cleanup can
    measure "how long has this been sitting finished" without re-deriving
    it from updated_at (which would be wrong if something touched the row
    again after completion, e.g. result_downloaded_at).
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
    """Record the first time a client fetches the result. Used by the
    cleanup policy to optionally delete jobs sooner once the result has
    actually been retrieved, instead of always waiting the full TTL."""
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
    """Return every job eligible for deletion under the cleanup policy.

    Three independent conditions (see cleanup.py for the policy reasoning):
      - FAILED and finished more than `failed_after_seconds` ago
      - DONE and finished more than `done_after_seconds` ago
      - Stuck in CREATED/UPLOADING/QUEUED/RUNNING with no update for more
        than `abandoned_after_seconds` (upload started and never finished,
        or the process died mid-job and never reached DONE/FAILED)
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
