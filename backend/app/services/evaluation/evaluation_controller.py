from app.services.execution.packet_executor import PacketRunner
from app.services.execution.flow_stateless_executor import FlowStatelessRunner
from app.services.execution.flow_stateful_executor import FlowStatefulRunner
from app.services.evaluation.report_generator import ReportGenerator

import math
import time
import json
import uuid
import os
from datetime import datetime


def rms(*values):
    return math.sqrt(sum(x**2 for x in values) / len(values))


def save_json(data, prefix, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    filename = f"{prefix}_{timestamp}_{unique_id}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    size_bytes = os.path.getsize(filepath)
    size_mb = size_bytes / (1024 * 1024)

    print(
        f"Saved {prefix}: {filepath} "
        f"({size_bytes:,} bytes / {size_mb:.2f} MB)"
    )

    return filepath, size_bytes


class EvaluationController:

    @staticmethod
    def run_all(db):
        start = time.time()

        packet_results = PacketRunner.run_all(db)
        packet_report = ReportGenerator.generate(packet_results)

        save_json(packet_results, "packet_results")
        save_json(packet_report, "packet_report")

        packet_time = time.time() - start

        start = time.time()

        flow_stateless_results = FlowStatelessRunner.run_all(db)
        stateless_report = ReportGenerator.generate(flow_stateless_results)

        save_json(flow_stateless_results, "flow_stateless_results")
        save_json(stateless_report, "stateless_report")

        less_time = time.time() - start

        start = time.time()

        flow_stateful_results = FlowStatefulRunner.run_all(db)
        statefull_report = ReportGenerator.generate(flow_stateful_results)

        save_json(flow_stateful_results, "flow_stateful_results")
        save_json(statefull_report, "statefull_report")

        full_time = time.time() - start

        overallRMS = rms(
            packet_report["overall"]["avg"],
            stateless_report["overall"]["avg"],
            statefull_report["overall"]["avg"]
        )

        overallTime = packet_time + less_time + full_time

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
            "overallTime": overallTime
        }