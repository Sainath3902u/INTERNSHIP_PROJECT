from pathlib import Path
import uuid


class JobManager:

    BASE_DIR = Path("storage/jobs")

    @staticmethod
    def create_job():

        job_id = uuid.uuid4().hex

        job_dir = JobManager.BASE_DIR / job_id

        (job_dir / "uploads").mkdir(
            parents=True,
            exist_ok=True
        )

        (job_dir / "database").mkdir(
            exist_ok=True
        )

        (job_dir / "outputs").mkdir(
            exist_ok=True
        )

        (job_dir / "logs").mkdir(
            exist_ok=True
        )

        return job_id
    
    @staticmethod
    def job_exists(job_id):

        return JobManager.get_job_dir(job_id).exists()

    @staticmethod
    def get_job_dir(job_id):

        return JobManager.BASE_DIR / job_id

    @staticmethod
    def get_upload_dir(job_id):

        return (
            JobManager.get_job_dir(job_id)
            / "uploads"
        )

    @staticmethod
    def get_database_dir(job_id):

        return (
            JobManager.get_job_dir(job_id)
            / "database"
        )

    @staticmethod
    def get_output_dir(job_id):

        return (
            JobManager.get_job_dir(job_id)
            / "outputs"
        )

    @staticmethod
    def get_logs_dir(job_id):

        return (
            JobManager.get_job_dir(job_id)
            / "logs"
        )

    @staticmethod
    def get_database_path(job_id):

        return str(
            JobManager.get_database_dir(job_id)
            / "benchmark.duckdb"
        )
    
    @staticmethod
    def get_real_parquet(job_id):

        return (
            JobManager.get_upload_dir(job_id)
            / "real.parquet"
        )


    @staticmethod
    def get_synthetic_parquet(job_id):

        return (
            JobManager.get_upload_dir(job_id)
            / "synthetic.parquet"
        )

    @staticmethod
    def get_real_csv(job_id):

        return (
            JobManager.get_upload_dir(job_id)
            / "real.csv"
        )

    @staticmethod
    def get_synthetic_csv(job_id):

        return (
            JobManager.get_upload_dir(job_id)
            / "synthetic.csv"
        )

    @staticmethod
    def get_result_path(job_id):

        return (
            JobManager.get_output_dir(job_id)
            / "result.json"
        )