import json
import time
import traceback

from concurrent.futures import ThreadPoolExecutor

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
    def _ingest(job_id: str) -> str:

        if not JobManager.job_exists(job_id):
            raise FileNotFoundError("Invalid Job ID")

        real_csv = JobManager.get_real_csv(job_id)
        synthetic_csv = JobManager.get_synthetic_csv(job_id)

        if not real_csv.exists():
            raise FileNotFoundError("Real CSV not uploaded")

        if not synthetic_csv.exists():
            raise FileNotFoundError("Synthetic CSV not uploaded")

        print(f"Real file      : {real_csv} "
              f"({real_csv.stat().st_size / (1024 * 1024):.2f} MB)")
        print(f"Synthetic file : {synthetic_csv} "
              f"({synthetic_csv.stat().st_size / (1024 * 1024):.2f} MB)")

        db_path = JobManager.get_database_path(job_id)
        conn = get_connection(db_path)

        try:
            start = time.perf_counter()
            CSVLoader.load_csv_to_table(str(real_csv), "real_packets", conn)
            CSVLoader.load_csv_to_table(str(synthetic_csv), "synthetic_packets", conn)
            print(f"Datasets loaded in {time.perf_counter() - start:.2f}s")


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

            print(f"Stateful tables built in {time.perf_counter() - start:.2f}s")

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

        overall_start = time.perf_counter()
        print(f"\n{'=' * 80}\nStarting evaluation job (sequential): {job_id}\n{'=' * 80}")

        try:
            db_path = cls._ingest(job_id)

            conn = get_connection(db_path)
            try:
                start = time.perf_counter()
                result = EvaluationController.run_all(conn)
                print(f"Evaluation completed in {time.perf_counter() - start:.2f}s")
            finally:
                conn.close()

            cls._save_result(job_id, result)

            print(f"TOTAL JOB TIME: {time.perf_counter() - overall_start:.2f}s\n{'=' * 80}\n")
            return result

        except Exception as e:
            print(f"\n{'=' * 80}\nJOB FAILED\n{'=' * 80}")
            print(f"Error Type: {type(e).__name__}\nError: {e}")
            traceback.print_exc()
            print(f"{'=' * 80}\n")
            raise

  
    # Parallel path - production default. POST /evaluate/parallel/{job_id}
    @classmethod
    def run_parallel(cls, job_id: str):

        overall_start = time.perf_counter()
        print(f"\n{'=' * 80}\nStarting evaluation job (parallel): {job_id}\n{'=' * 80}")

        try:
            db_path = cls._ingest(job_id)

            start = time.perf_counter()
            result = ParallelEvaluationController.run_all(db_path)
            print(f"Evaluation completed in {time.perf_counter() - start:.2f}s")

            cls._save_result(job_id, result)

            print(f"TOTAL JOB TIME: {time.perf_counter() - overall_start:.2f}s\n{'=' * 80}\n")
            return result

        except Exception as e:
            print(f"\n{'=' * 80}\nJOB FAILED\n{'=' * 80}")
            print(f"Error Type: {type(e).__name__}\nError: {e}")
            traceback.print_exc()
            print(f"{'=' * 80}\n")
            raise
