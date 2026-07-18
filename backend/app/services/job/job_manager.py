"""
JobManager manages the on-disk files for a benchmark job.

It provides helper methods for creating job directories and resolving
paths to uploaded files and generated results. Job metadata (status,
timestamps, etc.) is managed separately by the job metadata store.
"""

from pathlib import Path

from app.core.config import settings
from app.database import job_store

class JobManager:

    BASE_DIR: Path = settings.storage_base_dir

    @staticmethod
    def create_job() -> str:
        # Create a new job and store its metadata.
        job_id = job_store.create_job()

        job_dir = JobManager.get_job_dir(job_id)

        (job_dir / "uploads").mkdir(parents=True, exist_ok=True)
        (job_dir / "database").mkdir(exist_ok=True)
        (job_dir / "outputs").mkdir(exist_ok=True)
        (job_dir / "logs").mkdir(exist_ok=True)

        return job_id

    @staticmethod
    def job_exists(job_id: str) -> bool:
        # Check if the job exists in the metadata store.
        return job_store.job_exists(job_id)

    @staticmethod
    def get_job_dir(job_id: str) -> Path:
        return JobManager.BASE_DIR / job_id

    @staticmethod
    def get_upload_dir(job_id: str) -> Path:
        return JobManager.get_job_dir(job_id) / "uploads"

    @staticmethod
    def get_database_dir(job_id: str) -> Path:
        return JobManager.get_job_dir(job_id) / "database"

    @staticmethod
    def get_output_dir(job_id: str) -> Path:
        return JobManager.get_job_dir(job_id) / "outputs"

    @staticmethod
    def get_logs_dir(job_id: str) -> Path:
        return JobManager.get_job_dir(job_id) / "logs"

    @staticmethod
    def get_database_path(job_id: str) -> str:
        return str(JobManager.get_database_dir(job_id) / "benchmark.duckdb")

    @staticmethod
    def get_real_csv(job_id: str) -> Path:
        return JobManager.get_upload_dir(job_id) / "real.csv"

    @staticmethod
    def get_synthetic_csv(job_id: str) -> Path:
        return JobManager.get_upload_dir(job_id) / "synthetic.csv"

    @staticmethod
    def get_result_path(job_id: str) -> Path:
        return JobManager.get_output_dir(job_id) / "result.json"