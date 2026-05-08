import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("POKEMON_TCG_API_KEY")
BASE_URL = "https://api.pokemontcg.io/v2"


def fetch_all_set_ids():
    """Returns list of all set IDs from the pokemontcg.io API."""
    response = requests.get(BASE_URL + "/sets", headers={"X-Api-Key": API_KEY})
    response.raise_for_status()
    return [s["id"] for s in response.json()["data"]]


def fetch_cards_for_set(set_id):
    """Returns all cards for a set, or None on HTTP error."""
    response = requests.get(
        f"{BASE_URL}/cards?q=set.id:{set_id}",
        headers={"X-Api-Key": API_KEY},
    )
    if not response.ok:
        return None
    return response.json()["data"]