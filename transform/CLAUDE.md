# transform/ — Claude Context

dbt project that reads raw Parquet files from `data/` and produces `fct_card_price_features` in DuckDB. This is the sole data preparation layer for the ML model and the API.

## Layout

```
transform/
  cardstock_dbt/
    dbt_project.yml         project config (profile: cardstock_dbt, data_dir: ../../data)
    profiles.yml            DuckDB connection (dev.duckdb in this directory)
    dev.duckdb              local DuckDB file — written by dbt, read-only in the API
    models/
      staging/              views over raw Parquet files
      intermediate/         tables joining/enriching staging data
      marts/                final output table (fct_card_price_features)
    logs/dbt.log            execution logs
    target/                 compiled SQL + run artifacts (gitignored)
```

## Materialization Strategy

| Layer | Type | Why |
|---|---|---|
| staging | view | no storage cost; always reflects latest Parquet |
| intermediate | table | expensive joins; cached for performance |
| marts | table | queried by the API on every request |

## Model DAG

```
stg_card_registry           ← data/registry/card_registry.parquet
stg_daily_price_history     ← data/prices/daily_price_history.parquet
stg_price_history           ← data/prices/price_history.parquet
stg_google_trends           ← data/trends/google_trends.parquet
         ↓
int_card_daily_prices       (joins stg_daily + stg_price_history)
int_set_price_index         (set-level price aggregates)
int_set_release_features    (set metadata: days_since_release, specialty flag, etc.)
         ↓
fct_card_price_features     (41+ ML features per card per month)
```

## Running dbt

**Always run from the dbt project directory:**
```bash
cd transform/cardstock_dbt && dbt run
```

Or run a specific model and its upstream dependencies:
```bash
cd transform/cardstock_dbt && dbt run --select +fct_card_price_features
```

The `data_dir` variable (`../../data`) resolves to the repo-root `data/` folder from inside `cardstock_dbt/`.

## Key Output: fct_card_price_features

This is the single table the API and ML training read. Every row is a `(card_id, variant, price_date)` triple with 41 computed features.

Key feature groups:
- **Price levels**: `monthly_price`, `daily_price`
- **Moving averages**: `price_ma_3m`, `price_ma_6m`, `price_ma_12m`
- **Volatility**: `price_stddev_3m`, `price_cv_3m`
- **Momentum / returns**: `price_change_1m_pct` through `price_change_12m_pct`
- **Oscillators**: `stochastic_k_6m`, `stochastic_k_3m`
- **Regime**: `above_ma_3m/6m/12m`, `months_above_ma_12m`
- **Card fundamentals**: `days_since_release`, `is_specialty_set`, `packs_per_specific_card`
- **Market macro**: `days_since_recent_set_release`, `hype_weighted_release_90d`, `pokemon_interest_score`
- **Calendar**: `month_of_year`
- **Categorical**: `rarity`, `variant`, `set_id`

## DuckDB Conventions

- `dev.duckdb` is the only DuckDB file; it lives in `transform/cardstock_dbt/`
- The API reads it at `transform/cardstock_dbt/dev.duckdb` relative to the repo root
- **Never open dev.duckdb in write mode outside of dbt** — the API holds a read-only connection at runtime
- DuckDB can read Parquet directly: `SELECT * FROM '{{ var("data_dir") }}/prices/daily_price_history.parquet'`

## Deduplication Pattern

To get the latest row per card+variant (used throughout the API):
```sql
QUALIFY ROW_NUMBER() OVER (PARTITION BY card_id, variant ORDER BY price_date DESC) = 1
```

## Debugging Failures

1. Check `transform/cardstock_dbt/logs/dbt.log` for the full error
2. Compile SQL without running: `dbt compile --select fct_card_price_features`
3. Test a staging model in isolation: `dbt run --select stg_daily_price_history`
4. Verify upstream Parquet files exist before running dbt
