"""
Upload API endpoints.
Handle file uploads for benchmark jobs and update the job status during
the upload process.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.database import job_store
from app.services.job.job_manager import JobManager
from app.services.job.file_manager import FileManager

router = APIRouter()

ALLOWED_EXTENSIONS = {".csv"}


def _validate_csv(file: UploadFile):
    name = (file.filename or "").lower()
    if not any(name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted"
        )


@router.post("/create-job")
def create_job():
    job_id = JobManager.create_job()
    return {"job_id": job_id}


@router.post("/upload-real/{job_id}")
async def upload_real(job_id: str, file: UploadFile = File(...)):

    if not JobManager.job_exists(job_id):
        raise HTTPException(status_code=404, detail="Invalid Job ID")

    _validate_csv(file)

    try:
        # save_upload does blocking disk I/O - run it off the event loop
        # so a large upload doesn't stall every other concurrent request.
        await run_in_threadpool(
            FileManager.save_upload, file, JobManager.get_real_csv(job_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    job_store.set_status(job_id, job_store.STATUS_UPLOADING)
    return {"message": "Real CSV uploaded"}


@router.post("/upload-synthetic/{job_id}")
async def upload_synthetic(job_id: str, file: UploadFile = File(...)):

    if not JobManager.job_exists(job_id):
        raise HTTPException(status_code=404, detail="Invalid Job ID")

    _validate_csv(file)

    try:
        await run_in_threadpool(
            FileManager.save_upload, file, JobManager.get_synthetic_csv(job_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    job_store.set_status(job_id, job_store.STATUS_UPLOADING)
    return {"message": "Synthetic CSV uploaded"}