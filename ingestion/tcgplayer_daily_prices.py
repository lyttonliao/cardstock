import duckdb
import os
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timezone
import logging
from pokemontcg_client import fetch_cards_for_set
from constants import REGISTRY_PATH

OUTPUT_PATH = "data/prices/daily_price_history.parquet"

date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
logging.basicConfig(
    filename=f"logs/daily_price_scrape_{date}.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


def fetch_set_ids():
    """Returns set IDs from the registry (only sets we track)."""
    conn = duckdb.connect()
    set_ids_df = conn.execute(f"SELECT DISTINCT set_id FROM '{REGISTRY_PATH}' ORDER BY set_id ASC").fetchdf()
    return set_ids_df["set_id"].tolist()


def extract_price_rows(card, today):
    rows = []
    for variant, prices in card.get("tcgplayer", {}).get("prices", {}).items():
        market_price = prices.get("market")
        if market_price:
            rows.append({
                "id": card["id"],
                "variant": variant,
                "market_price": market_price,
                "date": today,
            })
    return rows


def already_fetched_today(conn, set_id, date):
    """Returns True if we already have price rows for this set today."""
    if not os.path.exists(OUTPUT_PATH):
        return False
    count = conn.execute(
        f"SELECT count(*) FROM '{OUTPUT_PATH}' WHERE date = '{date}' AND id LIKE '{set_id}-%'"
    ).fetchone()[0]
    return count > 0


def append_rows(rows):
    """Appends a list of row dicts to the output parquet file."""
    new_table = pa.Table.from_pylist(rows)
    if os.path.exists(OUTPUT_PATH):
        existing = pq.read_table(OUTPUT_PATH)
        combined = pa.concat_tables([existing, new_table])
        pq.write_table(combined, OUTPUT_PATH)
    else:
        pq.write_table(new_table, OUTPUT_PATH)


def main():
    date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    os.makedirs("data/prices", exist_ok=True)

    conn = duckdb.connect()
    set_ids = fetch_set_ids()
    if not set_ids:
        raise Exception("Unable to fetch set ids")

    registry_ids = set(
        conn.execute(f"SELECT DISTINCT id FROM '{REGISTRY_PATH}'").fetchdf()["id"].tolist()
    )
    print(f"Tracking {len(registry_ids)} cards across {len(set_ids)} sets for {date}...")

    total_rows = 0
    for set_id in set_ids:
        if already_fetched_today(conn, set_id, date):
            print(f"  {set_id}: already done — skipping")
            continue

        cards = fetch_cards_for_set(set_id)
        if not cards:
            log.warning(f"Skipping {set_id}: no cards returned")
            continue

        rows = []
        for card in cards:
            if card["id"] in registry_ids:
                rows.extend(extract_price_rows(card, date))

        if rows:
            append_rows(rows)
            total_rows += len(rows)
            print(f"  {set_id}: {len(rows)} rows written")
        else:
            print(f"  {set_id}: no prices available")

    print(f"Done. Total rows written today: {total_rows}")


if __name__ == "__main__":
    main()