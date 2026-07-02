from app.services.execution.packet_executor import PacketRunner
from app.services.execution.flow_stateless_executor import FlowStatelessRunner
from app.services.execution.flow_stateful_executor import FlowStatefulRunner
from app.services.evaluation.report_generator import ReportGenerator
from app.database.db import DuckDBManager

from concurrent.futures import ThreadPoolExecutor
import asyncio
import time
import math


# CHANGED: 3 -> 2
executor = ThreadPoolExecutor(max_workers=2)


def create_db():
    db = DuckDBManager()
    db.connect()
    return db


def run_packet():
    start = time.time()

    db = create_db()

    try:
        results = PacketRunner.run_all(db)
        return results, time.time() - start

    finally:
        db.close()


def run_stateless():
    start = time.time()

    db = create_db()

    try:
        results = FlowStatelessRunner.run_all(db)
        return results, time.time() - start

    finally:
        db.close()


def run_stateful():
    start = time.time()

    db = create_db()

    try:
        results = FlowStatefulRunner.run_all(db)
        return results, time.time() - start

    finally:
        db.close()


class EvaluationController:

    @staticmethod
    async def run_all(db=None):

        overall_start = time.time()

        loop = asyncio.get_running_loop()

        packet_future = loop.run_in_executor(
            executor,
            run_packet
        )

        stateless_future = loop.run_in_executor(
            executor,
            run_stateless
        )

        stateful_future = loop.run_in_executor(
            executor,
            run_stateful
        )

        (
            (packet_results, packet_time),
            (flow_stateless_results, stateless_time),
            (flow_stateful_results, stateful_time),
        ) = await asyncio.gather(
            packet_future,
            stateless_future,
            stateful_future
        )

        packet_report = ReportGenerator.generate(packet_results)
        stateless_report = ReportGenerator.generate(flow_stateless_results)
        statefull_report = ReportGenerator.generate(flow_stateful_results)

        overallRMS = math.sqrt(
            (
                packet_report["overall"]["avg"] ** 2 +
                stateless_report["overall"]["avg"] ** 2 +
                statefull_report["overall"]["avg"] ** 2
            ) / 3
        )

        total_time = time.time() - overall_start

        return {
            "overallRMS": overallRMS,
            "packet_time": packet_time,
            "stateless_time": stateless_time,
            "stateful_time": stateful_time,
            "total_time": total_time,
            "total_queries": (
                len(packet_results)
                + len(flow_stateless_results)
                + len(flow_stateful_results)
            )
        }