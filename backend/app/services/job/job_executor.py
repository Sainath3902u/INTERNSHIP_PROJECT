"""
JobExecutor runs ingestion and evaluation for a benchmark job.

It updates the job's status, logs execution progress, and coordinates the
ingestion and evaluation workflow.
"""

import json
import time
import traceback

from concurrent.futures import ThreadPoolExecutor

from app.core.logging_config import get_job_logger
from app.database import job_store
from app.database.db import get_connection
from app.services.ingestion.csv_loader import CSVLoader
from app.services.job.job_manager import JobManager
from app.services.evaluation.evaluation_controller import EvaluationController
from app.services.evaluation.evaluation_controller_parallel import ParallelEvaluationController

class JobExecutor:

    # Shared ingestion: validate uploads, load CSVs, build gap tables.
    # Used by both the sequential and parallel evaluation paths so the
    # two endpoints can never drift out of sync with each other.
    @staticmethod
    def _ingest(job_id: str, log) -> str:

        if not JobManager.job_exists(job_id):
            raise FileNotFoundError("Invalid Job ID")

        real_csv = JobManager.get_real_csv(job_id)
        synthetic_csv = JobManager.get_synthetic_csv(job_id)

        if not real_csv.exists():
            raise FileNotFoundError("Real CSV not uploaded")

        if not synthetic_csv.exists():
            raise FileNotFoundError("Synthetic CSV not uploaded")

        log.info(
            "ingestion inputs",
            extra={
                "real_csv_mb": round(real_csv.stat().st_size / (1024 * 1024), 2),
                "synthetic_csv_mb": round(synthetic_csv.stat().st_size / (1024 * 1024), 2),
            },
        )

        db_path = JobManager.get_database_path(job_id)
        conn = get_connection(db_path)

        try:
            start = time.perf_counter()
            CSVLoader.load_csv_to_table(str(real_csv), "real_packets", conn)
            CSVLoader.load_csv_to_table(str(synthetic_csv), "synthetic_packets", conn)
            log.info("datasets loaded", extra={"duration_sec": round(time.perf_counter() - start, 2)})

            # Build real and synthetic gap tables in parallel.
            # Use separate cursors on the same database connection instead of
            # multiple write connections, since DuckDB does not guarantee that
            # concurrent schema changes from different connections are safe.
            start = time.perf_counter()

            real_cursor = conn.cursor()
            synthetic_cursor = conn.cursor()

            try:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    real_future = executor.submit(
                        CSVLoader.build_stateful_tables, "real_packets", real_cursor
                    )
                    synthetic_future = executor.submit(
                        CSVLoader.build_stateful_tables, "synthetic_packets", synthetic_cursor
                    )
                    real_future.result()
                    synthetic_future.result()
            finally:
                real_cursor.close()
                synthetic_cursor.close()

            log.info("stateful tables built", extra={"duration_sec": round(time.perf_counter() - start, 2)})

        finally:
            conn.close()

        return db_path

    @staticmethod
    def _save_result(job_id: str, result: dict):
        result_path = JobManager.get_result_path(job_id)
        with open(result_path, "w") as f:
            json.dump(result, f, indent=4, default=str)

    # Sequential path - safe fallback. POST /evaluate/{job_id}
    @classmethod
    def run(cls, job_id: str):

        log = get_job_logger(job_id)
        overall_start = time.perf_counter()
        job_store.set_status(job_id, job_store.STATUS_RUNNING)
        log.info("evaluation started", extra={"mode": "sequential"})

        try:
            db_path = cls._ingest(job_id, log)

            conn = get_connection(db_path)
            try:
                start = time.perf_counter()
                result = EvaluationController.run_all(conn)
                log.info("evaluation phase complete", extra={"duration_sec": round(time.perf_counter() - start, 2)})
            finally:
                conn.close()

            cls._save_result(job_id, result)
            job_store.set_status(job_id, job_store.STATUS_DONE)

            log.info("job complete", extra={"total_duration_sec": round(time.perf_counter() - overall_start, 2)})
            return result

        except Exception as e:
            log.error(
                "job failed",
                exc_info=True,
                extra={"error_type": type(e).__name__},
            )
            job_store.set_status(job_id, job_store.STATUS_FAILED, error=f"{type(e).__name__}: {e}")
            raise

    # Parallel path - production default. POST /evaluate/parallel/{job_id}
    @classmethod
    def run_parallel(cls, job_id: str):

        log = get_job_logger(job_id)
        overall_start = time.perf_counter()
        job_store.set_status(job_id, job_store.STATUS_RUNNING)
        log.info("evaluation started", extra={"mode": "parallel"})

        try:
            db_path = cls._ingest(job_id, log)

            start = time.perf_counter()
            result = ParallelEvaluationController.run_all(db_path)
            log.info("evaluation phase complete", extra={"duration_sec": round(time.perf_counter() - start, 2)})

            cls._save_result(job_id, result)
            job_store.set_status(job_id, job_store.STATUS_DONE)

            log.info("job complete", extra={"total_duration_sec": round(time.perf_counter() - overall_start, 2)})
            return result

        except Exception as e:
            log.error(
                "job failed",
                exc_info=True,
                extra={"error_type": type(e).__name__},
            )
            job_store.set_status(job_id, job_store.STATUS_FAILED, error=f"{type(e).__name__}: {e}")
            raise