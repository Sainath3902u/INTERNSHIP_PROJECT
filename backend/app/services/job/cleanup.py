"""
POLICY (all three are independent; a job matching ANY is deleted)
---------------------------------------------------------------------
  - FAILED, completed > cleanup_failed_after_hours ago
  - DONE, completed > cleanup_done_after_days ago
  - CREATED/UPLOADING/QUEUED/RUNNING, no status update for > cleanup_abandoned_after_hours

Deletion removes BOTH the job's directory tree AND its metadata row in
the same pass - the metadata row does not outlive the files it describes,
so job_store never accumulates permanent history of every job ever run.
"""

import logging
import shutil

from app.core.config import settings
from app.database import job_store
from app.services.job.job_manager import JobManager

logger = logging.getLogger(__name__)


def run_cleanup() -> dict:
    """Delete every job eligible under the policy. Returns a summary dict
    (used by the scheduler log line and available for a manual /admin
    trigger if one is ever added)."""

    candidates = job_store.find_cleanup_candidates(
        failed_after_seconds=settings.cleanup_failed_after_hours * 3600,
        done_after_seconds=settings.cleanup_done_after_days * 86400,
        abandoned_after_seconds=settings.cleanup_abandoned_after_hours * 3600,
    )

    deleted, errors = [], []

    for record in candidates:
        job_dir = JobManager.get_job_dir(record.job_id)
        try:
            # Delete the files first, metadata row second: if the process
            # dies between the two, the job is a re-runnable "abandoned"
            # candidate again next pass rather than orphaned files with no
            # corresponding record at all, which no cleanup query could
            # ever discover again.
            if job_dir.exists():
                shutil.rmtree(job_dir)
            job_store.delete_job(record.job_id)
            deleted.append(record.job_id)

        except Exception as e:
            # One bad delete (e.g. a locked file) should not stop cleanup
            # from processing the rest of the batch - same "don't let one
            # failure take down the whole run" principle used throughout
            # the evaluation pipeline.
            logger.error(
                "cleanup failed for job",
                exc_info=True,
                extra={"job_id": record.job_id, "error_type": type(e).__name__},
            )
            errors.append(record.job_id)

    logger.info(
        "cleanup pass complete",
        extra={
            "candidates": len(candidates),
            "deleted": len(deleted),
            "errors": len(errors),
        },
    )

    return {"candidates": len(candidates), "deleted": deleted, "errors": errors}