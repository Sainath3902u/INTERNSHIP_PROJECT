import math
import time

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
    # A report can come back with an empty "overall" if every metric in
    # that phase failed - don't let that crash RMS computation.
    return report.get("overall", {}).get("avg")

class EvaluationController:
    """
    Sequential baseline: one connection, one phase after another, one
    query after another. Kept as the safe/legacy path - always correct,
    just not fast. Use ParallelEvaluationController for production.
    """

    @staticmethod
    def run_all(conn):

        start = time.time()
        packet_results = PacketRunner.run_all(conn)
        packet_report = ReportGenerator.generate(packet_results)
        packet_time = time.time() - start

        start = time.time()
        flow_stateless_results = FlowStatelessRunner.run_all(conn)
        stateless_report = ReportGenerator.generate(flow_stateless_results)
        less_time = time.time() - start

        start = time.time()
        flow_stateful_results = FlowStatefulRunner.run_all(conn)
        statefull_report = ReportGenerator.generate(flow_stateful_results)
        full_time = time.time() - start

        overallRMS = rms(
            _overall_avg(packet_report),
            _overall_avg(stateless_report),
            _overall_avg(statefull_report),
        )

        overallTime = packet_time + less_time + full_time

        print(f"Packet Time: {packet_time:.2f} seconds")
        print(f"Flow Stateless Time: {less_time:.2f} seconds")
        print(f"Flow Stateful Time: {full_time:.2f} seconds")
        print(f"Overall Time: {overallTime:.2f} seconds")

        return {
            "mode": "sequential",

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