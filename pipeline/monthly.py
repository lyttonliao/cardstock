import subprocess
import sys
from pipeline.s3 import download, upload, BASE_DIR


def main():
    download(["trends", "duckdb", "model"])

    subprocess.run([sys.executable, "ingestion/google_trends.py"], check=True)
    subprocess.run(
        ["dbt", "run", "--profiles-dir", "."],
        cwd=BASE_DIR / "transform/cardstock_dbt",
        check=True,
    )
    subprocess.run([sys.executable, "ml/train.py"], check=True)

    upload(["trends", "duckdb", "model"])


if __name__ == "__main__":
    main()

