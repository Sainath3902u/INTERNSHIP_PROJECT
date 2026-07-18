from fastapi import APIRouter, HTTPException
from app.services.job.job_executor import JobExecutor

router = APIRouter()


@router.post("/evaluate/{job_id}")
def evaluate(job_id: str):
    """Sequential evaluation - safe fallback"""
    try:
        return JobExecutor.run(job_id)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/evaluate/parallel/{job_id}")
def evaluate_parallel(job_id: str):
    """Parallel evaluation - production default. Same ingestion pipeline
    as /evaluate/{job_id}, but the 3 evaluation phases (packet, flow
    stateless, flow stateful) and the queries within each phase run
    concurrently against read-only connections."""
    try:
        return JobExecutor.run_parallel(job_id)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))