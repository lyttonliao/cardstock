import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("POKEMON_TCG_API_KEY")
BASE_URL = "https://api.pokemontcg.io/v2"
_headers = {"X-Api-Key": API_KEY}

_RETRY_STATUS = {429, 500, 502, 503, 504}


def _get(url: str, retries: int = 4, backoff: float = 2.0) -> requests.Response | None:
    """GET with exponential backoff retry. Returns None if all attempts fail."""
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=_headers, timeout=30)
            if response.status_code in _RETRY_STATUS and attempt < retries:
                time.sleep(backoff ** attempt)
                continue
            return response
        except requests.exceptions.ConnectionError:
            if attempt < retries:
                time.sleep(backoff ** attempt)
                continue
    return None


def fetch_all_sets():
    """Returns full set objects (id, series, images) from the API."""
    response = _get(BASE_URL + "/sets")
    if response is None or not response.ok:
        raise RuntimeError("Failed to fetch sets")
    return response.json()["data"]


def fetch_all_set_ids():
    """Returns list of all set IDs from the pokemontcg.io API."""
    response = _get(BASE_URL + "/sets")
    if response is None or not response.ok:
        raise RuntimeError("Failed to fetch set IDs")
    return [s["id"] for s in response.json()["data"]]


def fetch_cards_for_set(set_id):
    """Returns all cards for a set, or None on error."""
    response = _get(f"{BASE_URL}/cards?q=set.id:{set_id}")
    if response is None or not response.ok:
        return None
    return response.json()["data"]