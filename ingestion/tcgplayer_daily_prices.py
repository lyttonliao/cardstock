import duckdb
import os
import requests
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

load_dotenv()

API_KEY = os.getenv("POKEMON_TCG_API_KEY")
BASE_URL = "https://api.pokemontcg.io/v2"
OUTPUT_PATH = "data/prices/recent_daily_price_history.parquet"

date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
logging.basicConfig(
    filename=f"logs/daily_price_scrape_{date}.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

def fetch_set_ids():
    """Return list of all pokemon set ids"""

    conn = duckdb.connect()
    set_ids_df = conn.execute("SELECT DISTINCT set_id FROM 'data/registry/card_registry.parquet' ORDER BY set_id ASC").fetchdf()
    return set_ids_df["set_id"].tolist()

def fetch_cards_for_set(set_id):
    """Returns all cards for a pokemon set, accounts for pagination"""

    response = requests.get(
        f"{BASE_URL}/cards?q=set.id:{set_id}",
        headers={ "X-Api-Key": API_KEY }
    )
    response.raise_for_status()
    data = response.json()['data']
    return data

def extract_price_rows(card, today):
    rows = []
    for variant, prices in card.get("tcgplayer", {}).get("prices", {}).items():
        market_price = prices.get("market")
        if market_price:
            rows.append({
                "card_id": card["id"],
                "variant": variant,
                "market_price": market_price,
                "date": today,
            })
    return rows

def main():
    date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    os.makedirs("data/prices", exist_ok=True)

    # Skip if today's snapshot already exists
    conn = duckdb.connect()
    if os.path.exists(OUTPUT_PATH):
        num_rows = conn.execute(f"SELECT count(*) FROM '{OUTPUT_PATH}' WHERE date = '{date}'"
        ).fetchone()
        if num_rows and num_rows[0] > 0:
            print(f"Already have {num_rows[0]} rows for {date} — skipping.")
            return

    print("Fetching cards list...")
    
    set_ids = fetch_set_ids()
    if not set_ids:
        raise Exception(f"Unable to fetch set ids")

    rows = []
    for set_id in set_ids:
        cards = fetch_cards_for_set(set_id)
        if not cards:
            print(f'Unable to search cards for set: {set_id}')
            continue
        for card in cards:
            print(f"Pulling today's market price for card: {card['id']}")
            rows.extend(extract_price_rows(card, date))

    print(f"Total rows: {len(rows)}")

    if not rows:
        print("No data collected — exiting.")
        return

    new_table = pa.Table.from_pylist(rows)

    if os.path.exists(OUTPUT_PATH):
        existing = pq.read_table(OUTPUT_PATH)
        combined = pa.concat_tables([existing, new_table])
        pq.write_table(combined, OUTPUT_PATH)
        print(f"Appended to {OUTPUT_PATH}")
    else:
        pq.write_table(new_table, OUTPUT_PATH)
        print(f"Created {OUTPUT_PATH}")


if __name__ == "__main__":
    main()