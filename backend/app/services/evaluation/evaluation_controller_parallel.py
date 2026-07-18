import math
import time
from concurrent.futures import ThreadPoolExecutor

from app.database.db import get_read_connection
from app.services.execution.packet_executor import PacketRunner
from app.services.execution.flow_stateless_executor import FlowStatelessRunner
from app.services.execution.flow_stateful_executor import FlowStatefulRunner
from app.services.evaluation.report_generator import ReportGenerator


def rms(*values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return math.sqrt(sum(x ** 2 for x in values) / len(values))


def _overall_avg(report):
    return report.get("overall", {}).get("avg")


# Maximum number of SQL queries to run in parallel within a phase.
# Each phase has many independent queries, and DuckDB releases the GIL (Global Interpreter Lock),
# so using multiple threads provides a real performance boost.
QUERY_WORKERS = 8

class ParallelEvaluationController:
    """
    Production evaluation path.

    Uses three workers, one for each independent evaluation phase:
    packet, flow stateless, and flow stateful.

    Each worker:
      1. Opens a read-only connection to the job's database.
      2. Evaluates its assigned phase.
      3. Runs the phase's independent queries in parallel via BaseRunner.run_all(max_workers=...).

    Evaluation is read-only once ingestion has finished, so multiple
    read-only DuckDB connections can safely access the same database
    concurrently.

    This combines phase-level parallelism (3 workers) with query-level
    parallelism (up to QUERY_WORKERS per phase) to significantly reduce
    overall evaluation time.
    """

    @staticmethod
    def _run_phase(runner_cls, db_path):
        start = time.perf_counter()

        conn = get_read_connection(db_path)
        try:
            results = runner_cls.run_all(conn, max_workers=QUERY_WORKERS)
            report = ReportGenerator.generate(results)
        finally:
            conn.close()

        elapsed = time.perf_counter() - start
        return results, report, elapsed

    @classmethod
    def run_all(cls, db_path: str):

        overall_start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=3) as executor:
            packet_future = executor.submit(
                cls._run_phase, PacketRunner, db_path
            )
            stateless_future = executor.submit(
                cls._run_phase, FlowStatelessRunner, db_path
            )
            stateful_future = executor.submit(
                cls._run_phase, FlowStatefulRunner, db_path
            )

            packet_results, packet_report, packet_time = packet_future.result()
            flow_stateless_results, stateless_report, less_time = stateless_future.result()
            flow_stateful_results, statefull_report, full_time = stateful_future.result()

        overallRMS = rms(
            _overall_avg(packet_report),
            _overall_avg(stateless_report),
            _overall_avg(statefull_report),
        )

        overallTime = time.perf_counter() - overall_start

        print(f"[parallel] Packet Time: {packet_time:.2f}s (phase, {QUERY_WORKERS} query workers)")
        print(f"[parallel] Flow Stateless Time: {less_time:.2f}s")
        print(f"[parallel] Flow Stateful Time: {full_time:.2f}s")
        print(f"[parallel] Overall Time: {overallTime:.2f}s "
              f"(vs {packet_time + less_time + full_time:.2f}s if phases were sequential)")

        return {
            "mode": "parallel",

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