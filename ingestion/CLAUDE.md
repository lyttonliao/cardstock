# ingestion/ — Claude Context

Data ingestion scripts. Each script is standalone and writes to `data/` as Parquet via PyArrow.

## Scripts

| Script | Purpose | Frequency |
|---|---|---|
| `bootstrap_card_registry.py` | Build initial card catalog from pokemontcg.io | Once |
| `update_card_registry.py` | Refresh registry with new sets/cards | Daily (via pipeline) |
| `enrich_card_registry.py` | Add computed fields (pull rates, specialty flags) | After registry update |
| `tcgplayer_daily_prices.py` | Fetch today's TCGPlayer market prices | Daily (via pipeline) |
| `price_history_scraper.py` | Scrape monthly price history from PriceCharting | Once (resumable) |
| `google_trends.py` | Fetch monthly Pokemon TCG interest score | Monthly |
| `sync_algolia.py` | Sync card index to Algolia for search | After registry update |

## pokemontcg_client.py — API Wrapper

All external HTTP calls go through `_get()` which has:
- 4 retries with exponential backoff (`2^attempt` seconds: 1, 2, 4, 8s)
- Retries on HTTP status: `{429, 500, 502, 503, 504}`
- Catches both `ConnectionError` and `Timeout` (read timeout set to 60s)
- Returns `None` on total failure — callers must check for `None`

```python
cards = fetch_cards_for_set(set_id)
if not cards:                          # always guard the None case
    log.warning(f"Skipping {set_id}")
    continue
```

## constants.py — Key Values

- `REGISTRY_PATH` — path to `data/registry/card_registry.parquet`
- `MIN_MARKET_PRICE = 5.00` — cards below this are excluded from the registry (filters bulk commons)
- `SPECIALTY_SETS` — frozenset of ~30 specialty/limited set IDs (Celebrations, Shining Fates, Crown Zenith, etc.)
- `SET_SLOT_RATES` — dict mapping set_id → pull rate per slot (from riporfliptcg.com); used to compute `packs_per_specific_card`

## Parquet I/O Pattern

All scripts read and write Parquet using PyArrow. The standard append pattern:

```python
new_table = pa.Table.from_pylist(rows)
if os.path.exists(OUTPUT_PATH):
    existing = pq.read_table(OUTPUT_PATH)
    combined = pa.concat_tables([existing, new_table])
    pq.write_table(combined, OUTPUT_PATH)
else:
    pq.write_table(new_table, OUTPUT_PATH)
```

DuckDB can query Parquet files directly: `SELECT * FROM 'data/registry/card_registry.parquet'`.

## tcgplayer_daily_prices.py — Idempotency

- `already_fetched_today(conn, set_id, date)` checks whether rows for a set+date already exist before fetching.
- Runs are safe to retry — skips sets already written.
- Uses `REGISTRY_PATH` to determine which card IDs to track; ignores cards not in the registry.

## price_history_scraper.py — Resumability

- Tracks already-scraped `(card_id, variant)` pairs at startup.
- Adds `random.uniform(1.5, 3.0)` second delay between requests (polite crawling).
- `SET_SLUG_MAP` and `VARIANT_SLUG_MAP` handle naming differences between pokemontcg.io and PriceCharting URLs.
- Falls back from variant-specific URL to base card URL if the variant 404s.

## Running Scripts

Scripts expect to be run from the **repo root** (not from `ingestion/`):

```bash
python ingestion/tcgplayer_daily_prices.py
python ingestion/sync_algolia.py
```

They import `from constants import ...` and `from pokemontcg_client import ...` — these are resolved relative to the `ingestion/` directory because `pyproject.toml` registers `ingestion` as a package path. When running via `pipeline/daily.py` (which uses `subprocess.run`), the working directory is set to the repo root.
