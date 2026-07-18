import json
import time
import traceback

from concurrent.futures import ThreadPoolExecutor

from app.database.db import get_connection
from app.services.ingestion.csv_loader import CSVLoader
from app.services.job.job_manager import JobManager
from app.services.evaluation.evaluation_controller import EvaluationController


class JobExecutor:

    @staticmethod
    def run(job_id: str):

        overall_start = time.perf_counter()

        print(f"\n{'=' * 80}")
        print(f"Starting evaluation job: {job_id}")
        print(f"{'=' * 80}")

        if not JobManager.job_exists(job_id):
            raise FileNotFoundError("Invalid Job ID")

        real_csv = JobManager.get_real_csv(job_id)
        synthetic_csv = JobManager.get_synthetic_csv(job_id)

        if not real_csv.exists():
            raise FileNotFoundError("Real CSV not uploaded")

        if not synthetic_csv.exists():
            raise FileNotFoundError("Synthetic CSV not uploaded")

        print(f"Real file      : {real_csv}")
        print(
            f"Real size      : "
            f"{real_csv.stat().st_size / (1024 * 1024):.2f} MB"
        )

        print(f"Synthetic file : {synthetic_csv}")
        print(
            f"Synthetic size : "
            f"{synthetic_csv.stat().st_size / (1024 * 1024):.2f} MB"
        )

        conn = get_connection(
            JobManager.get_database_path(job_id)
        )

        try:
            # Load Real Dataset
            start = time.perf_counter()

            CSVLoader.load_csv_to_table(
                str(real_csv),
                "real_packets",
                conn
            )

            print(
                f"Real dataset loaded in "
                f"{time.perf_counter() - start:.2f}s"
            )

            # Load Synthetic Dataset
            start = time.perf_counter()

            CSVLoader.load_csv_to_table(
                str(synthetic_csv),
                "synthetic_packets",
                conn
            )

            print(
                f"Synthetic dataset loaded in "
                f"{time.perf_counter() - start:.2f}s"
            )

            # Build Stateful Tables
            start = time.perf_counter()

            db_path = JobManager.get_database_path(job_id)

            real_conn = get_connection(db_path)
            synthetic_conn = get_connection(db_path)

            try:

                with ThreadPoolExecutor(
                    max_workers=2
                ) as executor:

                    real_future = executor.submit(
                        CSVLoader.build_stateful_tables,
                        "real_packets",
                        real_conn
                    )

                    synthetic_future = executor.submit(
                        CSVLoader.build_stateful_tables,
                        "synthetic_packets",
                        synthetic_conn
                    )

                    real_future.result()
                    synthetic_future.result()

            finally:

                real_conn.close()
                synthetic_conn.close()

            print(
                f"Stateful tables built in "
                f"{time.perf_counter() - start:.2f}s"
            )

            # Evaluation
            start = time.perf_counter()

            result = EvaluationController.run_all(conn)

            print(
                f"✅ Evaluation completed in "
                f"{time.perf_counter() - start:.2f}s"
            )

            # Save Result
            start = time.perf_counter()

            result_path = JobManager.get_result_path(job_id)

            with open(result_path, "w") as f:
                json.dump(
                    result,
                    f,
                    indent=4,
                    default=str
                )

            print(
                f"Results saved in "
                f"{time.perf_counter() - start:.2f}s"
            )

            print(
                f"\nTOTAL JOB TIME: "
                f"{time.perf_counter() - overall_start:.2f}s"
            )

            print(f"{'=' * 80}\n")

            return result

        except Exception as e:

            print("\n")
            print("=" * 80)
            print("JOB FAILED")
            print("=" * 80)

            print(f"Error Type: {type(e).__name__}")
            print(f"Error: {e}")

            traceback.print_exc()

            print("=" * 80)
            print("\n")

            raise

        finally:
            conn.close()

    

    @staticmethod
    def run_parallel(job_id: str):
        pass