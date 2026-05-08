import pyarrow as pa
import pyarrow.parquet as pq
import os
from pokemontcg_client import fetch_all_set_ids, fetch_cards_for_set
from constants import REGISTRY_PATH, MIN_MARKET_PRICE


def extract_registry_rows(card):
    """Returns a list of rows, one per variant above MIN_MARKET_PRICE."""
    base = {
        "id": card.get("id"),
        "name": card.get("name"),
        "number": card.get("number"),
        "rarity": card.get("rarity"),
        "set_id": card.get("set", {}).get("id"),
        "set_name": card.get("set", {}).get("name"),
        "set_release_date": card.get("set", {}).get("releaseDate"),
        "image_small": card.get("images", {}).get("small"),
        "image_large": card.get("images", {}).get("large"),
        "tcgplayer_url": card.get("tcgplayer", {}).get("url"),
    }
    rows = []
    for variant_name, prices in card.get("tcgplayer", {}).get("prices", {}).items():
        market_price = prices.get("market")
        if market_price and market_price > MIN_MARKET_PRICE:
            rows.append({**base, "variant": variant_name, "tcgplayer_market_price": market_price})
    return rows


def main():
    print("Loading cards from all sets...")

    all_set_ids = fetch_all_set_ids()
    if not all_set_ids:
        return

    rows = []
    for set_id in all_set_ids:
        print(f"Fetching cards from {set_id}")
        cards = fetch_cards_for_set(set_id)
        if not cards:
            continue
        for card in cards:
            rows.extend(extract_registry_rows(card))

    print(f"Total rows: {len(rows)} loaded")

    os.makedirs("data/registry", exist_ok=True)
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, REGISTRY_PATH)


if __name__ == "__main__":
    main()