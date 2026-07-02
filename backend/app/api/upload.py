from fastapi import APIRouter, HTTPException
from app.services.ingestion.csv_loader import CSVLoader
from app.database.db import db

import requests
import tempfile
import os
import traceback

router = APIRouter()

REAL_CSV_URL = (
    "https://github.com/naresh-au27/"
    "packet-data-storage/releases/download/"
    "CSV/real.csv"
)

SYNTHETIC_CSV_URL = (
    "https://github.com/naresh-au27/"
    "packet-data-storage/releases/download/"
    "CSV/synthetic.csv"
)


def download_csv(url: str) -> str:

    print(f"Downloading: {url}")

    response = requests.get(
        url,
        stream=True,
        timeout=600
    )

    response.raise_for_status()

    temp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".csv"
    )

    total = 0

    for chunk in response.iter_content(
        chunk_size=1024 * 1024
    ):
        if chunk:
            temp.write(chunk)
            total += len(chunk)

    temp.close()

    print(
        f"Downloaded {total / 1024 / 1024:.2f} MB "
        f"to {temp.name}"
    )

    return temp.name


@router.post("/load-datasets")
async def load_datasets():

    real_file = None
    synthetic_file = None

    try:

        print("START DATASET LOAD")

        real_file = download_csv(
            REAL_CSV_URL
        )

        synthetic_file = download_csv(
            SYNTHETIC_CSV_URL
        )

        print(
            f"real file exists = "
            f"{os.path.exists(real_file)}"
        )

        print(
            f"synthetic file exists = "
            f"{os.path.exists(synthetic_file)}"
        )

        print("Loading real_packets...")

        real_result = (
            CSVLoader.load_csv_to_table(
                real_file,
                "real_packets",
                db
            )
        )

        print(real_result)

        print(
            "Loading synthetic_packets..."
        )

        synthetic_result = (
            CSVLoader.load_csv_to_table(
                synthetic_file,
                "synthetic_packets",
                db
            )
        )

        print(synthetic_result)

        print(
            "DATASET LOAD COMPLETE"
        )

        return {
            "status": "success",
            "real": real_result,
            "synthetic": synthetic_result
        }

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if (
            real_file and
            os.path.exists(real_file)
        ):
            os.remove(real_file)

        if (
            synthetic_file and
            os.path.exists(synthetic_file)
        ):
            os.remove(synthetic_file)