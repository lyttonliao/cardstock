import os
import boto3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

S3_KEYS = {
    "registry":     "registry/card_registry.parquet",
    "daily_prices": "prices/daily_price_history.parquet",
    "trends":       "trends/google_trends.parquet",
    "duckdb":       "db/dev.duckdb",
}

LOCAL_PATHS = {
    "registry":     BASE_DIR / "data/registry/card_registry.parquet",
    "daily_prices": BASE_DIR / "data/prices/daily_price_history.parquet",
    "trends":       BASE_DIR / "data/trends/google_trends.parquet",
    "duckdb":       BASE_DIR / "transform/cardstock_dbt/dev.duckdb",
}


def create_client():
    # boto3 automatically reads AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
    # and AWS_DEFAULT_REGION from environment variables — no credentials in code
    return boto3.client("s3")


def download(keys: list[str]) -> None:
    # Called at the start of a pipeline run to pull the latest files from S3
    # onto the GitHub Actions runner's local disk before the scripts need them
    s3 = create_client()
    bucket = os.environ["S3_BUCKET"]

    for key in keys:
        local = LOCAL_PATHS[key]
        # Create the parent directory if it doesn't exist yet
        # parents=True handles nested dirs (e.g. data/prices/), exist_ok=True
        # means no error if it already exists
        local.parent.mkdir(parents=True, exist_ok=True)

        print(f"Downloading {key}: s3://{bucket}/{S3_KEYS[key]} → {local}")
        s3.download_file(bucket, S3_KEYS[key], str(local))


def upload(keys: list[str]) -> None:
    # Called at the end of a pipeline run to push the updated files back to S3
    # so the next run (and the API server) can access the latest data
    s3 = create_client()
    bucket = os.environ["S3_BUCKET"]

    for key in keys:
        local = LOCAL_PATHS[key]
        print(f"Uploading {key}: {local} → s3://{bucket}/{S3_KEYS[key]}")
        s3.upload_file(str(local), bucket, S3_KEYS[key])
