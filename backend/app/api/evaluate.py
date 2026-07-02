from fastapi import APIRouter
from app.services.evaluation.evaluation_controller import EvaluationController as SEQ
from app.services.evaluation.parallel.IOasync import EvaluationController as ASync
from app.services.evaluation.parallel.thread3 import EvaluationController as Par3
from app.services.evaluation.parallel.thread2 import EvaluationController as Par2
from app.database.db import db

router = APIRouter()

@router.get("/evaluate-seq")
def evaluate_packet_query():
    return SEQ.run_all(db)

@router.get("/evaluate-iosync")
async def evaluate_seq_same_config(): 
    return await ASync.run_all()

@router.get("/evaluate-parallel-3")
async def evaluate_parallel_3():
    return await Par3.run_all()

@router.get("/evaluate-parallel-2")
async def evaluate_parallel_2():
    return await Par2.run_all()