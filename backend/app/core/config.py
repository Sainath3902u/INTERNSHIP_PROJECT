from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BENCHMARK_")

    # --- Storage -----------------------------------------------------
    # Converted to an absolute path at startup so it works correctly
    # no matter where the application is started from.
    storage_base_dir: Path = Path("storage/jobs")

    # SQLite database for storing job metadata.
    job_db_path: Path = Path("storage/job_metadata.db")

    # --- Uploads - Maximum allowed upload size (2 GB by default).
    max_upload_mb: int = 2048

    # --- CORS --------------------------------------------------------
    # Comma-separated list of allowed frontend origins.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # --- Cleanup policy ----------------------------------------------
    # Automatically remove old or abandoned jobs after these limits.
    cleanup_failed_after_hours: int = 24
    cleanup_done_after_days: int = 7
    cleanup_abandoned_after_hours: int = 24  # created/uploading, never finished
    cleanup_interval_minutes: int = 60       # how often the scheduler runs

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_post_init(self, __context) -> None:
        # Convert storage paths to absolute paths once at startup so
        # every part of the application uses the same locations.
        object.__setattr__(self, "storage_base_dir", self.storage_base_dir.resolve())
        object.__setattr__(self, "job_db_path", self.job_db_path.resolve())


# Shared application settings. Import this instance instead of
# creating new Settings() objects.
settings = Settings()