import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import json
import os
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("POKEMON_TCG_API_KEY")
BASE_URL = "https://api.pokemontcg.io/v2"

MIN_MARKET_PRICE = 1.00

def fetch_all_set_ids():
    """Returns list of all pokemon set ids"""
    try:
        response = requests.get(BASE_URL + "/sets", headers={ "X-Api-Key": API_KEY })
        response.raise_for_status()
        data = response.json()['data']
        return list(map(lambda x: x['id'], data))
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")

def fetch_all_sets():
    """Returns list of all pokemon sets"""
    try:
        response = requests.get(BASE_URL + "/sets", headers={ "X-Api-Key": API_KEY })
        response.raise_for_status()
        data = response.json()['data']
        return data
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")


def fetch_cards_for_set(set_id):
    """Returns all cards for a pokemon set, accounts for pagination"""

    try:
        response = requests.get(
            f"{BASE_URL}/cards?q=set.id:{set_id}",
            headers={ "X-Api-Key": API_KEY }
        )
        response.raise_for_status()
        data = response.json()['data']
        return data
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")


def fetch_card(card_id):
    """Return data for card by card id"""

    try:
        response = requests.get(f"{BASE_URL}/cards/{card_id}")
        response.raise_for_status()
        data = response.json()['data']
        return data
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")
    

def extract_registry_row(card):
    """Pulls the fields from a card dict"""

    return {
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
        "tcgplayer_market_price": card.get("tcgplayer", {}).get("prices", {}).get("holofoil", {}).get("market")
    }

def main():
    print(f"Loading cards from all sets...")

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
            row = extract_registry_row(card)
            if row["tcgplayer_market_price"] and row["tcgplayer_market_price"] > MIN_MARKET_PRICE:
                rows.append(row)
    print(f"Total rows: {len(rows)} loaded")

    os.makedirs("data/registry", exist_ok=True)

    table = pa.Table.from_pylist(rows)
    pq.write_table(table, "data/registry/card_registry.parquet")


if __name__ == "__main__":
    main()
