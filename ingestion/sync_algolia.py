import duckdb
import pandas as pd

from algoliasearch.search.client import SearchClientSync

from core.config import settings
from constants import REGISTRY_PATH


def main():
    conn = duckdb.connect()
    df = conn.execute(f"""
        SELECT
            id AS card_id,
            name,
            COALESCE(variant, 'normal') AS variant,
            rarity,
            set_id,
            set_name,
            image_small
        FROM '{REGISTRY_PATH}'
    """).fetchdf()
    print(f"Loaded {len(df)} rows from registry.")

    records = []
    for _, row in df.iterrows():
        records.append({
            "objectID": f"{row['card_id']}_{row['variant']}",
            "card_id": row["card_id"],
            "name": row["name"],
            "variant": row["variant"],
            "rarity": row["rarity"] if pd.notna(row["rarity"]) else None,
            "set_id": row["set_id"],
            "set_name": row["set_name"],
            "image_small": row["image_small"],
        })

    _client = SearchClientSync(
        app_id=settings.algolia_application_id,
        api_key=settings.algolia_write_api_key
    )

    _client.save_objects(
        index_name="cards_index",
        objects=records,
    )
    print(f"Synced {len(records)} records to Algolia.")


if __name__ == "__main__":
    main()
