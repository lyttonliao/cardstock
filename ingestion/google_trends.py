import os
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pytrends.request import TrendReq

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE_DIR, "data", "trends", "google_trends.parquet")

KEYWORDS = ["pokemon cards", "pokemon tcg"]

TIMEFRAME = "2020-01-01 2026-05-01"


def fetch_trends() -> pd.DataFrame:
    pytrends = TrendReq(hl="en-US", tz=0, retries=3, backoff_factor=1)
    pytrends.build_payload(KEYWORDS, timeframe=TIMEFRAME, geo="US", gprop="")

    df = pytrends.interest_over_time()

    if df.empty:
        raise RuntimeError("Google Trends returned empty data — possible rate limit. Try again in a few minutes.")

    # Drop the 'isPartial' flag column if present
    df = df.drop(columns=["isPartial"], errors="ignore")

    # Average the two keyword columns into one composite interest score
    df["interest_score"] = df[KEYWORDS].mean(axis=1)
    df = df[["interest_score"]].reset_index().rename(columns={"date": "trend_date"})

    # Trends returns weekly data for long windows; resample to monthly mean
    df["trend_date"] = pd.to_datetime(df["trend_date"])
    df = df.set_index("trend_date").resample("MS")["interest_score"].mean().reset_index()

    return df


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    print(f"Fetching Google Trends for: {KEYWORDS}")
    print(f"Timeframe: {TIMEFRAME}")

    df = fetch_trends()

    print(f"Fetched {len(df)} monthly rows ({df['trend_date'].min().date()} → {df['trend_date'].max().date()})")
    print(df.tail(6).to_string(index=False))

    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, OUT_PATH)
    print(f"\nSaved → {OUT_PATH}")


if __name__ == "__main__":
    main()
