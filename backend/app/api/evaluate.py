# from fastapi import APIRouter
# from app.database.db import get_connection

# from app.services.evaluation.evaluation_controller import (
#     EvaluationController as SEQ
# )
# from app.services.evaluation.parallel.IOasync import (
#     EvaluationController as ASync
# )
# from app.services.evaluation.parallel.thread3 import (
#     EvaluationController as Par3
# )
# from app.services.evaluation.parallel.thread2 import (
#     EvaluationController as Par2
# )

# router = APIRouter()

# DATABASE_PATH = "benchmark.db"

# @router.post("/evaluate/{job_id}")
# def evaluate(job_id: str):
#     return JobExecutor.run(job_id)

# @router.get("/evaluate-seq")
# def evaluate_packet_query():

#     conn = get_connection(DATABASE_PATH)

#     try:
#         return SEQ.run_all(conn)

#     finally:
#         conn.close()

# @router.get("/evaluate-iosync")
# async def evaluate_seq_same_config():

#     conn = get_connection(DATABASE_PATH)

#     try:
#         return await ASync.run_all(conn)

#     finally:
#         conn.close()


# @router.get("/evaluate-parallel-3")
# async def evaluate_parallel_3():

#     conn = get_connection(DATABASE_PATH)

#     try:
#         return await Par3.run_all(conn)

#     finally:
#         conn.close()


# @router.get("/evaluate-parallel-2")
# async def evaluate_parallel_2():

#     conn = get_connection(DATABASE_PATH)

#     try:
#         return await Par2.run_all(conn)

#     finally:
#         conn.close()


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