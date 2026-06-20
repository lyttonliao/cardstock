---
description: Run one or more Cardstock data ingestion scripts to fetch fresh card prices, registry updates, or Algolia sync.
---

You are running Cardstock data ingestion. Ask the user which steps they want to run, then execute them in the correct order from the repo root.

**Available ingestion scripts:**

| # | Script | What it does | Frequency |
|---|---|---|---|
| 1 | `python ingestion/update_card_registry.py` | Refresh card metadata from pokemontcg.io | Daily |
| 2 | `python ingestion/tcgplayer_daily_prices.py` | Fetch today's TCGPlayer market prices | Daily |
| 3 | `python ingestion/sync_algolia.py` | Sync card search index to Algolia | After registry update |
| 4 | `python ingestion/google_trends.py` | Fetch monthly Pokemon TCG interest score | Monthly |
| 5 | `python ingestion/enrich_card_registry.py` | Add computed fields (pull rates, specialty flags) | After bootstrap/update |

**Recommended daily run order:** 1 → 2 → 3

**Notes:**
- All scripts run from the **repo root** (not from `ingestion/`)
- `tcgplayer_daily_prices.py` is **idempotent** — it skips sets already fetched today, safe to re-run
- `update_card_registry.py` retries failed API calls with exponential backoff (4x, up to 8s)
- After ingestion, ask if the user wants to run `dbt run` to rebuild `fct_card_price_features`
- After dbt, ask if they want to upload updated files to S3: `python pipeline/s3.py upload registry daily_prices duckdb`

Run each script, show its output, and report success or failure before moving to the next.
