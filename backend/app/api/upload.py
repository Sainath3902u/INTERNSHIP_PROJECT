from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.job.job_manager import JobManager
from app.services.job.file_manager import FileManager

router = APIRouter()


@router.post("/create-job")
def create_job():

    job_id = JobManager.create_job()

    return {
        "job_id": job_id
    }


@router.post("/upload-real/{job_id}")
async def upload_real(
    job_id: str,
    file: UploadFile = File(...)
):

    if not JobManager.job_exists(job_id):
        raise HTTPException(
            status_code=404,
            detail="Invalid Job ID"
        )

    FileManager.save_upload(
        file,
        JobManager.get_real_csv(job_id)
    )

    return {
        "message": "Real CSV uploaded"
    }


@router.post("/upload-synthetic/{job_id}")
async def upload_synthetic(
    job_id: str,
    file: UploadFile = File(...)
):

    if not JobManager.job_exists(job_id):
        raise HTTPException(
            status_code=404,
            detail="Invalid Job ID"
        )

    FileManager.save_upload(
        file,
        JobManager.get_synthetic_csv(job_id)
    )

    return {
        "message": "Synthetic CSV uploaded"
    }