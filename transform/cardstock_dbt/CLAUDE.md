# transform/cardstock_dbt/ — Claude Context

dbt project using DuckDB. Transforms raw Parquet files into the ML feature table.

## Model Layers

```
staging/     Views — thin wrappers over raw Parquet, standardise names/types
intermediate/ Tables — joins, aggregations, feature engineering
marts/       Tables — final analytics-ready tables consumed by the API and ML
```

Run order: `stg_* → int_* → fct_*`. dbt handles dependency ordering via `ref()`.

## Key Table: fct_card_price_features

The main output. One row per `(card_id, variant, price_date)`. 41 columns used as ML features plus 3 forward-looking targets.

**To add a new feature:**
1. Add it in the CTE where it belongs (`windowed` for window functions, `enriched` for derived fields, final SELECT for joins)
2. Add the column name to `FEATURES` in `api/constants.py`
3. Re-run `dbt run` and retrain the model

**Targets** (computed as correlated subqueries in the final SELECT):
- `next_1m_price`, `next_3m_price`, `next_6m_price` — look forward by offsetting `price_date`

## SQL Conventions

**DuckDB-specific syntax used:**
- `QUALIFY ROW_NUMBER() OVER (...) = 1` — deduplicate to one row per partition (used heavily; standard SQL doesn't have `QUALIFY`)
- `date_trunc('month', date_col)` — truncate to month start for joining monthly with daily data
- `read_parquet('../../data/...')` — paths are relative to the dbt project root in staging models

**Two-pass window function pattern** — DuckDB (like all SQL) can't reference a window alias in the same SELECT, so features are built in two CTEs:
```sql
windowed AS (
    SELECT *, AVG(price) OVER w_3m AS price_ma_3m
    FROM base
    WINDOW w_3m AS (PARTITION BY card_id, variant ORDER BY price_date ROWS 2 PRECEDING)
),
enriched AS (
    SELECT *, monthly_price / NULLIF(price_ma_3m, 0) AS price_vs_ma_3m
    FROM windowed
)
```

**NULL safety:** Use `NULLIF(denominator, 0)` in divisions. Use `WHERE col IS NOT NULL` before division in the API layer.

**Log return:** `LN(monthly_price / launch_price)` — always use natural log (`LN`), not `LOG`.

## Staging Gotchas

- `stg_card_registry.sql`: pokemontcg.io returns dates as `"2024/01/26"` (slashes). Must cast: `cast(replace(set_release_date, '/', '-') as date)`.
- `stg_daily_price_history.sql`: renames `market_price` → `tcgplayer_market_price` to avoid ambiguity in joins.
- PriceCharting data (`stg_price_history`) lands on the **1st of the month** (`2026-04-01`). TCGPlayer daily data has dates like `2026-04-15`. Direct joins produce no matches — always join on `date_trunc('month', ...)`.

## Running dbt

```bash
cd transform/cardstock_dbt
dbt run                    # full run
dbt run -s fct_card_price_features   # single model
dbt test                   # run schema tests
```

The DuckDB file is written to `transform/cardstock_dbt/dev.duckdb`. The API reads from `DB_PATH` which points here (or to the S3-downloaded copy in production).

## Profiles

`profiles.yml` sets the DuckDB file path. The `dev` target writes to `dev.duckdb` in the project directory. Do not change this path without updating `api/constants.py::DB_PATH`.
