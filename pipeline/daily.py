import subprocess
import sys
from pipeline.s3 import download, upload, BASE_DIR


def main():
    download(["registry", "daily_prices", "duckdb"])

    subprocess.run([sys.executable, "ingestion/update_card_registry.py"], check=True)
    subprocess.run([sys.executable, "ingestion/tcgplayer_daily_prices.py"], check=True)
    subprocess.run(
        ["dbt", "run", "--profiles-dir", "."],
        cwd=BASE_DIR / "transform/cardstock_dbt",
        check=True,
    )

    upload(["registry", "daily_prices", "duckdb"])


if __name__ == "__main__":
    main()


