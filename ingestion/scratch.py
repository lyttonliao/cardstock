from dotenv import load_dotenv
import requests
import os

# Load variables from .env into the system environment
load_dotenv()

pokemontcg_api_key = os.getenv('POKEMONTCG_API_KEY')

try:
    response = requests.get(
        'https://api.pokemontcg.io/v2/cards?q=set.id:base1&pageSize=5',
        headers={
            "X-Api-Key": pokemontcg_api_key
        }
    )
    data = response.json()['data']
    print(data[0])
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print(f"HTTP error: {err}")
