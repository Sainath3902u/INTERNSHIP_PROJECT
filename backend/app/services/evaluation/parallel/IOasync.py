from app.services.execution.packet_executor import PacketRunner
from app.services.execution.flow_stateless_executor import FlowStatelessRunner
from app.services.execution.flow_stateful_executor import FlowStatefulRunner
from app.services.evaluation.report_generator import ReportGenerator
from app.database.db import DuckDBManager

import asyncio
import time
import math


def rms(*values):
    return math.sqrt(sum(x ** 2 for x in values) / len(values))


def create_db():
    db = DuckDBManager()
    db.connect()
    return db


def run_packet():
    start = time.time()
    db = create_db()

    try:
        results = PacketRunner.run_all(db)
        report = ReportGenerator.generate(results)
        elapsed = time.time() - start
        return results, report, elapsed
    finally:
        db.close()


def run_stateless():
    start = time.time()
    db = create_db()

    try:
        results = FlowStatelessRunner.run_all(db)
        report = ReportGenerator.generate(results)
        elapsed = time.time() - start
        return results, report, elapsed
    finally:
        db.close()


def run_stateful():
    start = time.time()
    db = create_db()

    try:
        results = FlowStatefulRunner.run_all(db)
        report = ReportGenerator.generate(results)
        elapsed = time.time() - start
        return results, report, elapsed
    finally:
        db.close()


class EvaluationController:

    @staticmethod
    async def run_all(db=None):
        overall_start = time.time()

        (
            (packet_results, packet_report, packet_time),
            (flow_stateless_results, stateless_report, less_time),
            (flow_stateful_results, statefull_report, full_time),
        ) = await asyncio.gather(
            asyncio.to_thread(run_packet),
            asyncio.to_thread(run_stateless),
            asyncio.to_thread(run_stateful),
        )

        overallRMS = rms(
            packet_report["overall"]["avg"],
            stateless_report["overall"]["avg"],
            statefull_report["overall"]["avg"],
        )

        overallTime = time.time() - overall_start

        print(f"Packet Time: {packet_time:.2f} seconds")
        print(f"Flow Stateless Time: {less_time:.2f} seconds")
        print(f"Flow Stateful Time: {full_time:.2f} seconds")
        print(f"Overall Time: {overallTime:.2f} seconds")

        return {
            "packet": packet_results,
            "packet_report": packet_report,

            "flow_stateless": flow_stateless_results,
            "stateless_report": stateless_report,

            "flow_stateful": flow_stateful_results,
            "statefull_report": statefull_report,

            "overallRMS": overallRMS,

            "packet_time": packet_time,
            "less_time": less_time,
            "full_time": full_time,
            "overallTime": overallTime,
        }