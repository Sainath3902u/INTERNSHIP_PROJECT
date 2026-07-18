"""
Evaluation API endpoints.
Start benchmark evaluation jobs in the background and provide an
immediate response to the client.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.database import job_store
from app.services.job.job_executor import JobExecutor
from app.services.job.job_manager import JobManager

router = APIRouter()


def _validate_ready_for_evaluation(job_id: str):
    if not JobManager.job_exists(job_id):
        raise HTTPException(status_code=404, detail="Invalid Job ID")

    if not JobManager.get_real_csv(job_id).exists():
        raise HTTPException(status_code=400, detail="Real CSV not uploaded")

    if not JobManager.get_synthetic_csv(job_id).exists():
        raise HTTPException(status_code=400, detail="Synthetic CSV not uploaded")

    # Prevent double-submission: if a job is already queued/running, a second
    # POST here should not kick off a second concurrent evaluation writing
    # to the same DuckDB file (which would violate the single-writer
    # assumption ingestion relies on).
    record = job_store.get_job(job_id)
    if record.status in (job_store.STATUS_QUEUED, job_store.STATUS_RUNNING):
        raise HTTPException(
            status_code=409,
            detail=f"Job is already {record.status}",
        )


@router.post("/evaluate/{job_id}")
def evaluate(job_id: str, background_tasks: BackgroundTasks):
    """Sequential evaluation - safe fallback. Runs in the background."""
    _validate_ready_for_evaluation(job_id)

    job_store.set_status(job_id, job_store.STATUS_QUEUED)
    background_tasks.add_task(JobExecutor.run, job_id)

    return {"job_id": job_id, "status": job_store.STATUS_QUEUED}


@router.post("/evaluate/parallel/{job_id}")
def evaluate_parallel(job_id: str, background_tasks: BackgroundTasks):
    """Parallel evaluation - production default. Runs in the background."""
    _validate_ready_for_evaluation(job_id)

    job_store.set_status(job_id, job_store.STATUS_QUEUED)
    background_tasks.add_task(JobExecutor.run_parallel, job_id)

    return {"job_id": job_id, "status": job_store.STATUS_QUEUED}