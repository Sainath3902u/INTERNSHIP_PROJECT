"""
Local/CLI mode.

Usage:

    python -m app.backend --real real.csv --syn synthetic.csv

Example:

    python -m app.backend \
        --real "C:\\Users\\nares\\Downloads\\Dataset\\real.csv" \
        --syn "C:\\Users\\nares\\Downloads\\Dataset\\synthetic.csv"

WHAT THIS DOES
--------------
1. Validates the real and synthetic CSV files.
2. Creates a normal backend job using JobManager.
3. Copies the CSV files directly into the job upload directory.
4. Runs the same evaluation pipeline used by the API.
5. Starts the FastAPI server.
6. Opens the frontend dashboard with the job ID:

       http://localhost:3000/dashboard?job_id=<job_id>

The frontend can then use the job ID to request:

       GET /jobs/<job_id>/result

This avoids uploading the CSV files through HTTP when they already exist
on the same machine.
"""

import argparse
import shutil
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

from app.core.logging_config import configure_logging
from app.database import job_store
from app.main import app
from app.services.job.job_executor import JobExecutor
from app.services.job.job_manager import JobManager


def _validate_csv(path: Path, label: str) -> Path:
    """
    Validate that the supplied path exists and is a CSV file.
    """

    resolved = path.expanduser().resolve()

    if not resolved.exists():
        print(f"Error: {label} file not found: {resolved}")
        sys.exit(1)

    if not resolved.is_file():
        print(f"Error: {label} path is not a file: {resolved}")
        sys.exit(1)

    if resolved.suffix.lower() != ".csv":
        print(f"Error: {label} file must be a .csv: {resolved}")
        sys.exit(1)

    return resolved


def _print_progress_dots(stop_event: threading.Event) -> None:
    """
    Print progress dots while evaluation is running.
    """

    while not stop_event.is_set():
        print(".", end="", flush=True)
        time.sleep(1)


def _open_dashboard_after_server_starts(
    dashboard_url: str,
    delay: float = 1.5,
) -> None:
    """
    Open the dashboard shortly after Uvicorn starts.

    Uvicorn.run() is blocking, so opening the browser before calling it can
    cause the dashboard to request the API before port 8000 is ready.

    A short delayed daemon thread avoids that race in normal local usage.
    """

    time.sleep(delay)
    webbrowser.open(dashboard_url)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a benchmark evaluation locally from CSV files on disk."
    )

    parser.add_argument(
        "--real",
        required=True,
        help="Path to the real dataset CSV",
    )

    parser.add_argument(
        "--syn",
        required=True,
        help="Path to the synthetic dataset CSV",
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to serve the FastAPI application on",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to serve the FastAPI application on",
    )

    parser.add_argument(
        "--frontend-url",
        default="http://localhost:3000/dashboard",
        help="Dashboard URL. The generated job_id is appended as a query parameter.",
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the dashboard",
    )

    args = parser.parse_args()

    # Validate input files
    real_path = _validate_csv(Path(args.real), "real")
    syn_path = _validate_csv(Path(args.syn), "synthetic")

    # Initialize backend
    configure_logging()
    job_store.init_db()

    # Create job
    job_id = JobManager.create_job()

    print(f"Job created: {job_id}")

    # Copy CSV files into the same location used by API uploads
    real_destination = JobManager.get_real_csv(job_id)
    synthetic_destination = JobManager.get_synthetic_csv(job_id)

    shutil.copyfile(
        real_path,
        real_destination,
    )

    shutil.copyfile(
        syn_path,
        synthetic_destination,
    )

    job_store.set_status(
        job_id,
        job_store.STATUS_UPLOADING,
    )

    # Run evaluation
    print("Running evaluation ", end="", flush=True)

    stop_event = threading.Event()

    dots_thread = threading.Thread(
        target=_print_progress_dots,
        args=(stop_event,),
        daemon=True,
    )

    dots_thread.start()

    try:
        JobExecutor.run_parallel(job_id)

    except Exception as exc:
        stop_event.set()
        dots_thread.join()

        print()
        print(f"Evaluation failed: {exc}")
        print(f"Job ID: {job_id}")
        print("Check the job logs / job_store row for details.")

        sys.exit(1)

    finally:
        stop_event.set()

    dots_thread.join()

    print()
    print("Evaluation completed successfully.")

    # Dashboard URL
    separator = "&" if "?" in args.frontend_url else "?"

    dashboard_url = (
        f"{args.frontend_url}"
        f"{separator}job_id={job_id}"
    )

    print()
    print(f"Job ID:    {job_id}")
    print(f"Dashboard: {dashboard_url}")
    print(
        f"API:       http://{args.host}:{args.port}"
        "  (Ctrl+C to stop)"
    )

    # Open browser after FastAPI has had time to start
    if not args.no_browser:
        browser_thread = threading.Thread(
            target=_open_dashboard_after_server_starts,
            args=(dashboard_url,),
            daemon=True,
        )

        browser_thread.start()

    # Start the same FastAPI application used in server mode
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()