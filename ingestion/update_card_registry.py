import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pokemontcg_client import fetch_all_set_ids, fetch_cards_for_set
from constants import REGISTRY_PATH, MIN_MARKET_PRICE, SPECIALTY_SETS, SET_SLOT_RATES


def extract_registry_rows(card):
    """Returns a list of rows, one per variant.

    For new sets, TCGPlayer prices may not be populated yet in the API.
    We register any card that has a TCGPlayer URL so price history can
    be collected as soon as pricing data becomes available.
    If prices are present, we still filter to MIN_MARKET_PRICE to avoid bulk commons.
    """
    tcgplayer = card.get("tcgplayer", {})
    tcgplayer_url = tcgplayer.get("url")
    if not tcgplayer_url:
        return []

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
        "tcgplayer_url": tcgplayer_url,
    }

    prices = tcgplayer.get("prices", {})
    if prices:
        # Prices available — apply price filter
        rows = []
        for variant_name, variant_prices in prices.items():
            market_price = variant_prices.get("market")
            if market_price and market_price > MIN_MARKET_PRICE:
                rows.append({**base, "variant": variant_name, "tcgplayer_market_price": market_price})
        return rows
    else:
        # No prices yet — register with a null-price row so we can track it later
        return [{**base, "variant": None, "tcgplayer_market_price": None}]


def enrich(df):
    """Adds is_specialty_set, packs_per_slot, cards_in_rarity_slot, packs_per_specific_card."""
    df["is_specialty_set"] = df["set_id"].isin(SPECIALTY_SETS).astype(int)

    def get_packs_per_slot(row):
        slot_rates = SET_SLOT_RATES.get(row["set_id"])
        if slot_rates is None:
            return None
        return slot_rates.get(row["rarity"])

    df["packs_per_slot"] = df.apply(get_packs_per_slot, axis=1)

    rarity_counts = (
        df.groupby(["set_id", "rarity"])
        .size()
        .reset_index(name="cards_in_rarity_slot")
    )
    df = df.merge(rarity_counts, on=["set_id", "rarity"], how="left")
    df["cards_in_rarity_slot"] = df["cards_in_rarity_slot"].astype(float)
    df["packs_per_specific_card"] = df["packs_per_slot"] * df["cards_in_rarity_slot"]
    return df


def append_to_registry(rows):
    df = enrich(pd.DataFrame(rows))
    existing = pq.read_table(REGISTRY_PATH)
    new_table = pa.Table.from_pandas(df, preserve_index=False)
    combined = pa.concat_tables([existing, new_table], promote_options="default")
    pq.write_table(combined, REGISTRY_PATH)
    return len(combined)


def backfill_null_price_sets(conn):
    """For sets with null-price placeholder rows, check if the API now has prices.
    If so, remove the placeholders and replace with proper per-variant rows.
    """
    null_sets = (
        conn.execute(
            f"SELECT DISTINCT set_id FROM '{REGISTRY_PATH}' WHERE tcgplayer_market_price IS NULL"
        )
        .fetchdf()["set_id"]
        .tolist()
    )

    if not null_sets:
        return

    print(f"Checking {len(null_sets)} sets with pending prices: {null_sets}")

    backfilled = []
    for set_id in null_sets:
        cards = fetch_cards_for_set(set_id)
        if not cards:
            continue

        rows = []
        for card in cards:
            prices = card.get("tcgplayer", {}).get("prices", {})
            if not prices:
                continue
            for variant_name, variant_prices in prices.items():
                market_price = variant_prices.get("market")
                if market_price and market_price > MIN_MARKET_PRICE:
                    rows.append({
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
                        "variant": variant_name,
                        "tcgplayer_market_price": market_price,
                    })

        if rows:
            backfilled.append((set_id, rows))

    if not backfilled:
        print("  No prices available yet for pending sets.")
        return

    # Remove placeholder rows for sets that now have prices, then append real rows
    existing_df = pq.read_table(REGISTRY_PATH).to_pandas()
    sets_to_replace = {s for s, _ in backfilled}
    existing_df = existing_df[
        ~((existing_df["set_id"].isin(sets_to_replace)) & (existing_df["tcgplayer_market_price"].isna()))
    ]

    all_new_rows = [row for _, rows in backfilled for row in rows]
    new_df = enrich(pd.DataFrame(all_new_rows))

    combined = pd.concat([existing_df, new_df], ignore_index=True)
    pq.write_table(pa.Table.from_pandas(combined, preserve_index=False), REGISTRY_PATH)

    for set_id, rows in backfilled:
        print(f"  {set_id}: backfilled {len(rows)} rows")


def main():
    conn = duckdb.connect()
    existing_set_ids = set(
        conn.execute(f"SELECT DISTINCT set_id FROM '{REGISTRY_PATH}'")
        .fetchdf()["set_id"]
        .tolist()
    )
    print(f"Registry has {len(existing_set_ids)} sets already.")

    # ── Backfill sets that were added without prices ───────────────────────────
    backfill_null_price_sets(conn)

    # ── Ingest brand new sets ─────────────────────────────────────────────────
    all_set_ids = fetch_all_set_ids()
    new_set_ids = [s for s in all_set_ids if s not in existing_set_ids]

    if not new_set_ids:
        print("No new sets found.")
        return

    print(f"New sets to ingest: {new_set_ids}")

    rows = []
    for set_id in new_set_ids:
        print(f"Fetching {set_id}...")
        cards = fetch_cards_for_set(set_id)
        if not cards:
            print(f"  {set_id}: no cards returned — skipping")
            continue
        print(f"  {len(cards)} cards found")
        for card in cards:
            rows.extend(extract_registry_rows(card))

    print(f"New rows to append: {len(rows)}")

    if not rows:
        print("No rows to append.")
        return

    total = append_to_registry(rows)
    print(f"Appended to {REGISTRY_PATH} — total rows: {total}")


if __name__ == "__main__":
    main()