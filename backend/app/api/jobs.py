"""
Job management API endpoints.

Provide endpoints for checking job status, retrieving completed results,
and listing benchmark jobs.
"""

import json
import math

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.database import job_store
from app.services.job.job_manager import JobManager

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _json_safe(value):
    """Recursively replace NaN/Infinity with None."""
    if isinstance(value, float):
        return None if (math.isnan(value) or math.isinf(value)) else value
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


@router.get("/{job_id}/status")
def get_status(job_id: str):
    record = job_store.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Invalid Job ID")

    return {
        "job_id": record.job_id,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "completed_at": record.completed_at,
        "error": record.error,
    }


@router.get("/{job_id}/result")
def get_result(job_id: str):
    record = job_store.get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Invalid Job ID")

    if record.status == job_store.STATUS_FAILED:
        raise HTTPException(status_code=422, detail=f"Job failed: {record.error}")

    if record.status != job_store.STATUS_DONE:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not finished yet (status: {record.status})",
        )

    result_path = JobManager.get_result_path(job_id)
    if not result_path.exists():
        # Job is marked as complete, but the result file is missing.
        # This indicates an inconsistent job state.
        raise HTTPException(status_code=500, detail="Result file missing for a completed job")

    job_store.mark_result_downloaded(job_id)

    with open(result_path) as f:
        result = json.load(f)

    return JSONResponse(content=_json_safe(result))


@router.get("")
def list_jobs(status: str | None = None, limit: int = 100):
    """List benchmark jobs for the dashboard."""
    records = job_store.list_jobs(status=status, limit=limit)
    return [
        {
            "job_id": r.job_id,
            "status": r.status,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in records
    ]