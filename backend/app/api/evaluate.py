from fastapi import APIRouter, HTTPException
from app.services.job.job_executor import JobExecutor

router = APIRouter()


@router.post("/evaluate/{job_id}")
def evaluate(job_id: str):

    try:

        return JobExecutor.run(job_id)

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )