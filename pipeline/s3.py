import boto3
from pathlib import Path
from core.config import settings

BASE_DIR = Path(__file__).parent.parent

S3_KEYS = {
    "registry":       "registry/card_registry.parquet",
    "price_history":  "prices/price_history.parquet",
    "daily_prices":   "prices/daily_price_history.parquet",
    "trends":         "trends/google_trends.parquet",
    "duckdb":         "db/dev.duckdb",
    "model":          "ml/xgb_v1.json",
}

LOCAL_PATHS = {
    "registry":       BASE_DIR / "data/registry/card_registry.parquet",
    "price_history":  BASE_DIR / "data/prices/price_history.parquet",
    "daily_prices":   BASE_DIR / "data/prices/daily_price_history.parquet",
    "trends":         BASE_DIR / "data/trends/google_trends.parquet",
    "duckdb":         BASE_DIR / "transform/cardstock_dbt/dev.duckdb",
    "model":          BASE_DIR / "ml/models/xgb_v1.json",
}


def create_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_default_region,
    )


def download(keys: list[str]) -> None:
    s3 = create_client()
    bucket = settings.s3_bucket

    for key in keys:
        local = LOCAL_PATHS[key]
        local.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {key}: s3://{bucket}/{S3_KEYS[key]} → {local}")
        s3.download_file(bucket, S3_KEYS[key], str(local))


def upload(keys: list[str]) -> None:
    s3 = create_client()
    bucket = settings.s3_bucket

    for key in keys:
        local = LOCAL_PATHS[key]
        print(f"Uploading {key}: {local} → s3://{bucket}/{S3_KEYS[key]}")
        s3.upload_file(str(local), bucket, S3_KEYS[key])


if __name__ == "__main__":
    import argparse

    all_keys = list(S3_KEYS.keys())
    parser = argparse.ArgumentParser(
        description="Sync files between local disk and S3.",
        epilog=f"Available keys: {', '.join(all_keys)}",
    )
    parser.add_argument("action", choices=["download", "upload"])
    parser.add_argument(
        "keys",
        nargs="*",
        default=all_keys,
        help="Which files to sync (default: all)",
    )
    args = parser.parse_args()

    if args.action == "download":
        download(args.keys)
    else:
        upload(args.keys)
