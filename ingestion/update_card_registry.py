import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pokemontcg_client import fetch_all_set_ids, fetch_cards_for_set, fetch_all_sets
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

    card_set = card.get("set", {})
    base = {
        "id": card.get("id"),
        "name": card.get("name"),
        "number": card.get("number"),
        "rarity": card.get("rarity"),
        "set_id": card_set.get("id"),
        "set_name": card_set.get("name"),
        "set_series": card_set.get("series"),
        "set_image_symbol": card_set.get("images", {}).get("symbol"),
        "set_image_logo": card_set.get("images", {}).get("logo"),
        "set_release_date": card_set.get("releaseDate"),
        "image_small": card.get("images", {}).get("small"),
        "image_large": card.get("images", {}).get("large"),
        "tcgplayer_url": tcgplayer_url,
        "pokedex_number": next(iter(card.get("nationalPokedexNumbers", [])), None),
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
    existing_df = pq.read_table(REGISTRY_PATH).to_pandas()
    new_df = df.reindex(columns=existing_df.columns)
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    pq.write_table(pa.Table.from_pandas(combined, preserve_index=False), REGISTRY_PATH)
    return len(combined)


def backfill_null_set_details():
    """Backfill card registry with fields (series, logo, symbol)."""
    print("Initiating - backfilling card registry with set details")

    sets = fetch_all_sets()

    rows = [
        {
            "set_id": s["id"],
            "set_series": s.get("series"),
            "set_image_symbol": s.get("images", {}).get("symbol"),
            "set_image_logo": s.get("images", {}).get("logo"),
        }
        for s in sets
    ]

    existing_df = pq.read_table(REGISTRY_PATH).to_pandas()
    updates_df = pd.DataFrame(rows).drop_duplicates("set_id").set_index("set_id")

    for col in ["set_series", "set_image_symbol", "set_image_logo"]:
        existing_df[col] = existing_df["set_id"].map(updates_df[col])

    pq.write_table(pa.Table.from_pandas(existing_df, preserve_index=False), REGISTRY_PATH)

    print("Completed backfilling card registry with set details")


def backfill_null_pokedex_numbers():
    """One-time backfill: add pokedex_number for cards added before this field existed.

    Fetches nationalPokedexNumbers from the pokemontcg.io API for every set that has
    cards with a missing pokedex_number, then writes the updated registry back to disk.
    """
    df = pq.read_table(REGISTRY_PATH).to_pandas()

    if "pokedex_number" not in df.columns:
        df["pokedex_number"] = None

    needs_backfill_sets = (
        df[df["pokedex_number"].isna()]["set_id"].dropna().unique().tolist()
    )

    if not needs_backfill_sets:
        print("All registry cards already have pokedex_number — nothing to backfill.")
        return

    print(f"Backfilling pokedex_number for {len(needs_backfill_sets)} sets...")

    card_to_dex = {}
    for set_id in needs_backfill_sets:
        print(f"  Fetching {set_id}...")
        cards = fetch_cards_for_set(set_id)
        if not cards:
            continue
        for card in cards:
            cid = card.get("id")
            dex = card.get("nationalPokedexNumbers", [])
            if cid and dex:
                card_to_dex[cid] = dex[0]

    filled = df["id"].map(card_to_dex)
    df["pokedex_number"] = df["pokedex_number"].where(df["pokedex_number"].notna(), filled)

    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), REGISTRY_PATH)
    print(f"Backfilled {filled.notna().sum()} rows with pokedex_number.")


def backfill_null_price_sets(conn):
    """For sets with null-price placeholder rows:
    1. Add any card IDs that exist in the API but aren't in the registry yet
       (handles sets where pokemontcg.io added cards after our initial ingest).
    2. If prices are now available, replace placeholder rows with per-variant rows.
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

    existing_df = pq.read_table(REGISTRY_PATH).to_pandas()
    existing_ids = set(existing_df["id"].tolist())

    backfilled = []      # (set_id, priced_rows) — sets that now have market prices
    new_placeholder_rows = []  # cards newly added to pokemontcg.io since last ingest

    for set_id in null_sets:
        cards = fetch_cards_for_set(set_id)
        if not cards:
            continue

        priced_rows = []
        for card in cards:
            card_id = card.get("id")
            tcgplayer = card.get("tcgplayer", {})
            tcgplayer_url = tcgplayer.get("url")
            prices = tcgplayer.get("prices", {})

            # New card IDs not yet in the registry — add as placeholder
            if card_id and card_id not in existing_ids and tcgplayer_url:
                new_placeholder_rows.extend(extract_registry_rows(card))
                existing_ids.add(card_id)
                continue

            if not prices:
                continue
            for variant_name, variant_prices in prices.items():
                market_price = variant_prices.get("market")
                if market_price and market_price > MIN_MARKET_PRICE:
                    priced_rows.append({
                        "id": card_id,
                        "name": card.get("name"),
                        "number": card.get("number"),
                        "rarity": card.get("rarity"),
                        "set_id": card.get("set", {}).get("id"),
                        "set_name": card.get("set", {}).get("name"),
                        "set_series": card.get("set", {}).get("series"),
                        "set_image_symbol": card.get("set", {}).get("images", {}).get("symbol"),
                        "set_image_logo": card.get("set", {}).get("images", {}).get("logo"),
                        "set_release_date": card.get("set", {}).get("releaseDate"),
                        "image_small": card.get("images", {}).get("small"),
                        "image_large": card.get("images", {}).get("large"),
                        "tcgplayer_url": tcgplayer_url,
                        "variant": variant_name,
                        "tcgplayer_market_price": market_price,
                        "pokedex_number": next(iter(card.get("nationalPokedexNumbers", [])), None),
                    })

        if priced_rows:
            backfilled.append((set_id, priced_rows))

    # Append newly discovered cards as placeholders
    if new_placeholder_rows:
        new_df = enrich(pd.DataFrame(new_placeholder_rows)).reindex(columns=existing_df.columns)
        existing_df = pd.concat([existing_df, new_df], ignore_index=True)
        print(f"  Added {len(new_placeholder_rows)} new placeholder rows for cards not previously in registry")

    if not backfilled:
        if not new_placeholder_rows:
            print("No prices available yet and no new cards found for pending sets.")
        pq.write_table(pa.Table.from_pandas(existing_df, preserve_index=False), REGISTRY_PATH)
        return

    # Remove placeholder rows for sets that now have prices, then append real rows
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

    # ── Backfill sets that were added without prices ──────────────────────────
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


def backfill_set(set_id: str):
    """Backfill a single set: add missing card IDs and populate prices if TCGPlayer has them.

    Faster than running main() when you only need to update one set.
    """
    cards = fetch_cards_for_set(set_id)
    if not cards:
        print(f"No cards returned for {set_id}")
        return

    print(f"Fetched {len(cards)} cards for {set_id}")

    existing_df = pq.read_table(REGISTRY_PATH).to_pandas()
    existing_ids = set(existing_df["id"].tolist())

    new_placeholder_rows = []
    priced_rows = []

    for card in cards:
        card_id = card.get("id")
        tcgplayer = card.get("tcgplayer", {})
        tcgplayer_url = tcgplayer.get("url")
        prices = tcgplayer.get("prices", {})

        if not tcgplayer_url:
            continue

        if card_id not in existing_ids:
            # Brand new card — register it (with prices if available, placeholder if not)
            new_placeholder_rows.extend(extract_registry_rows(card))
            existing_ids.add(card_id)
        elif existing_df.loc[existing_df["id"] == card_id, "tcgplayer_market_price"].isna().all():
            # Already in registry as a placeholder — try to replace with priced rows
            if not prices:
                continue
            for variant_name, variant_prices in prices.items():
                market_price = variant_prices.get("market")
                if market_price and market_price > MIN_MARKET_PRICE:
                    priced_rows.append({
                        "id": card_id,
                        "name": card.get("name"),
                        "number": card.get("number"),
                        "rarity": card.get("rarity"),
                        "set_id": card.get("set", {}).get("id"),
                        "set_name": card.get("set", {}).get("name"),
                        "set_series": card.get("set", {}).get("series"),
                        "set_image_symbol": card.get("set", {}).get("images", {}).get("symbol"),
                        "set_image_logo": card.get("set", {}).get("images", {}).get("logo"),
                        "set_release_date": card.get("set", {}).get("releaseDate"),
                        "image_small": card.get("images", {}).get("small"),
                        "image_large": card.get("images", {}).get("large"),
                        "tcgplayer_url": tcgplayer_url,
                        "variant": variant_name,
                        "tcgplayer_market_price": market_price,
                        "pokedex_number": next(iter(card.get("nationalPokedexNumbers", [])), None),
                    })

    if new_placeholder_rows:
        new_df = enrich(pd.DataFrame(new_placeholder_rows)).reindex(columns=existing_df.columns)
        existing_df = pd.concat([existing_df, new_df], ignore_index=True)
        print(f"  Added {len(new_placeholder_rows)} new cards")

    if priced_rows:
        # Remove placeholder rows for this set, then append real priced rows
        existing_df = existing_df[
            ~((existing_df["set_id"] == set_id) & (existing_df["tcgplayer_market_price"].isna()))
        ]
        new_df = enrich(pd.DataFrame(priced_rows)).reindex(columns=existing_df.columns)
        existing_df = pd.concat([existing_df, new_df], ignore_index=True)
        print(f"  Backfilled {len(priced_rows)} priced rows")

    if not new_placeholder_rows and not priced_rows:
        print(f"  Nothing to update for {set_id}")
        return

    pq.write_table(pa.Table.from_pandas(existing_df, preserve_index=False), REGISTRY_PATH)
    print(f"  Registry updated — {len(existing_df)} total rows")


def patch_card_url(card_id: str, tcgplayer_url: str):
    """Manually register a card that pokemontcg.io hasn't linked to TCGPlayer yet.

    Fetches card metadata from pokemontcg.io, injects the provided URL, and appends
    a placeholder row to the registry. Useful when TCGPlayer has a listing but the
    pokemontcg.io API still returns no tcgplayer.url for the card.

    The daily price scraper will pick up market prices on its next run.
    """
    from pokemontcg_client import _get, BASE_URL

    # Strip query string to keep URLs consistent with pokemontcg.io format
    clean_url = tcgplayer_url.split("?")[0]

    resp = _get(f"{BASE_URL}/cards/{card_id}")
    if not resp or not resp.ok:
        print(f"Failed to fetch card {card_id} from pokemontcg.io")
        return

    card = resp.json().get("data")
    if not card:
        print(f"No data returned for {card_id}")
        return

    # Inject the URL so extract_registry_rows picks it up
    if "tcgplayer" not in card:
        card["tcgplayer"] = {}
    card["tcgplayer"]["url"] = clean_url

    existing_df = pq.read_table(REGISTRY_PATH).to_pandas()
    if card_id in existing_df["id"].values:
        print(f"{card_id} is already in the registry — nothing to do")
        return

    rows = extract_registry_rows(card)
    if not rows:
        print(f"extract_registry_rows returned no rows for {card_id}")
        return

    total = append_to_registry(rows)
    print(f"Added {card_id} to registry (url={clean_url}) — total rows: {total}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update the card registry.")
    parser.add_argument("--set", dest="set_id", help="Backfill a single set by ID (e.g. me4)")
    parser.add_argument("--patch", dest="patch_card_id", metavar="CARD_ID",
                        help="Manually add a card by ID when pokemontcg.io lacks its TCGPlayer URL")
    parser.add_argument("--url", dest="patch_url", metavar="TCGPLAYER_URL",
                        help="TCGPlayer URL for the card specified by --patch")
    args = parser.parse_args()

    if args.patch_card_id:
        if not args.patch_url:
            parser.error("--patch requires --url")
        patch_card_url(args.patch_card_id, args.patch_url)
    elif args.set_id:
        backfill_set(args.set_id)
    else:
        main()
        backfill_null_pokedex_numbers()
