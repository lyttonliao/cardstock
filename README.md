# Cardstock — Card Price Prediction

An end-to-end ML pipeline that predicts Pokemon TCG card prices 3 months forward. Combines historical price data, TCGPlayer market prices, and Google Trends signals into a feature-rich XGBoost model.

**Current model performance (May 2026):** MAE $4.92 · RMSE $15.12 on a March 2026 holdout set.

---

## Architecture

```
Data Sources
    │
    ▼
[Ingestion Layer]   Python scripts
    │               pokemontcg.io API, PriceCharting scraper,
    │               TCGPlayer API (daily), Google Trends
    │
    │  writes Parquet files → data/
    ▼
[Transform Layer]   dbt Core + DuckDB
    │               Staging → Intermediate → Mart
    │
    │  materialises fct_card_price_features → dev.duckdb
    ▼
[ML Layer]          XGBoost + MLflow
                    trains on log returns, saves ml/models/xgb_v1.json
```

---

## Project Structure

```
cardstock/
├── ingestion/
│   ├── pokemontcg_client.py          # pokemontcg.io API wrapper
│   ├── bootstrap_card_registry.py    # one-time: build card catalog
│   ├── price_history_scraper.py      # PriceCharting monthly history
│   ├── tcgplayer_daily_prices.py     # daily TCGPlayer prices (cron)
│   └── google_trends.py              # Google Trends monthly interest
├── transform/
│   └── cardstock_dbt/
│       └── models/
│           ├── staging/
│           │   ├── stg_card_registry.sql
│           │   ├── stg_price_history.sql
│           │   ├── stg_daily_price_history.sql
│           │   └── stg_google_trends.sql
│           ├── intermediate/
│           │   ├── int_card_daily_prices.sql
│           │   └── int_set_release_features.sql
│           └── marts/
│               └── fct_card_price_features.sql
├── ml/
│   ├── train.py
│   └── models/
│       └── xgb_v1.json
├── data/
│   ├── registry/card_registry.parquet
│   ├── prices/
│   │   ├── price_history.parquet
│   │   └── daily_price_history.parquet
│   └── trends/google_trends.parquet
└── requirements.txt
```

---

## Data Flow

```
pokemontcg.io API
    → bootstrap_card_registry.py
    → data/registry/card_registry.parquet        (one row per card+variant)

PriceCharting.com (scraped)
    → price_history_scraper.py
    → data/prices/price_history.parquet          (monthly NM prices, 2020→now)

pokemontcg.io API (daily cron)
    → tcgplayer_daily_prices.py
    → data/prices/daily_price_history.parquet    (daily TCGPlayer prices)

Google Trends (pytrends)
    → google_trends.py
    → data/trends/google_trends.parquet          (monthly US interest score)

dbt run
    stg_card_registry          ← card_registry.parquet
    stg_price_history          ← price_history.parquet
    stg_daily_price_history    ← daily_price_history.parquet
    stg_google_trends          ← google_trends.parquet
    int_card_daily_prices      ← stg_price_history + stg_card_registry + stg_daily_price_history
    int_set_release_features   ← stg_price_history + stg_card_registry + stg_google_trends
    fct_card_price_features    ← int_card_daily_prices + int_set_release_features + stg_google_trends
        → materialised in transform/cardstock_dbt/dev.duckdb

python ml/train.py
    → reads fct_card_price_features from dev.duckdb
    → trains XGBRegressor on log(next_3m_price / monthly_price)
    → saves ml/models/xgb_v1.json
    → logs run to ml/mlruns/
```

---

## Ingestion

### `pokemontcg_client.py`
Thin wrapper around the pokemontcg.io REST API. `fetch_all_set_ids()` returns every set ID; `fetch_cards_for_set(set_id)` returns all cards for a set with TCGPlayer pricing and metadata. Reads `POKEMON_TCG_API_KEY` from `.env`.

### `bootstrap_card_registry.py`
Run once to build the master card catalog. Loops every set, extracts one row per card+variant, filters out variants below a minimum market price (removes bulk commons). Writes to `data/registry/card_registry.parquet` via PyArrow.

### `price_history_scraper.py`
Scrapes monthly Near Mint price history from PriceCharting.com for every card in the registry. PriceCharting embeds historical data as a JavaScript variable (`VGPC.chart_data`) in the page HTML, extracted with a regex. Key features:
- `slugify()` converts card/set names to URL-safe slugs with Unicode normalization
- `SET_SLUG_MAP` and `VARIANT_SLUG_MAP` handle cases where PriceCharting URLs differ from pokemontcg.io naming
- Fallback logic: if a variant URL 404s, retries without the variant suffix
- Resume logic: tracks already-scraped `(card_id, variant)` pairs so the job can be stopped and restarted
- Polite crawling: `random.uniform(1.5, 3.0)` second delay between requests
- Appends to existing Parquet on re-runs using `pa.concat_tables`

### `tcgplayer_daily_prices.py`
Designed as a daily cron. Fetches today's TCGPlayer market prices for all tracked cards via the pokemontcg.io API. Idempotent: `already_fetched_today()` checks the existing parquet before writing to prevent duplicate rows.

### `google_trends.py`
Fetches US search interest for `["pokemon cards", "pokemon tcg"]` over the full data window using pytrends (Google Trends unofficial API). Averages both keywords into a single `interest_score`, then resamples weekly data to monthly using `resample("MS")` (month-start). Saves 77 monthly rows to `data/trends/google_trends.parquet`.

---

## Transform (dbt)

### Staging

Thin wrappers that read Parquet via DuckDB's `read_parquet()` and standardise types/names. Notable:
- `stg_card_registry.sql`: `cast(replace(set_release_date, '/', '-') as date)` — the API returns dates as `"2024/01/26"`, DuckDB needs hyphens
- `stg_daily_price_history.sql`: renames `market_price` → `tcgplayer_market_price`

### `int_card_daily_prices.sql`

Joins monthly PriceCharting history with registry metadata and daily TCGPlayer prices. The core challenge: PriceCharting snapshots land on the 1st of each month (`2026-04-01`) while TCGPlayer daily data has dates like `2026-04-30` — a direct join produces no matches. Solution: a `daily_prices_monthly` CTE aggregates daily prices to monthly averages using `date_trunc('month', ...)`, then the join matches on month.

Also computes `launch_price` — the first-ever recorded price per card — using `first_value(nm_price) over (partition by card_id, variant order by price_date)`.

### `int_set_release_features.sql`

Computes two macro market signals per price date:

- `days_since_recent_set_release`: how many days since the most recent set launched
- `hype_weighted_release_90d`: sum of average card launch prices for sets released in the trailing 90 days — a pure set quality signal (market temperature is captured separately by `pokemon_interest_score`)

Uses a `QUALIFY` clause to select each card's first price snapshot after its release date, then averages by set. Cross-joins every price date against all released sets to compute the rolling window aggregate.

### `fct_card_price_features.sql`

The final feature table — one row per card per month, ~30 columns. Three CTE layers:

**`windowed`** — rolling window features using named SQL windows (`w_3m`, `w_6m`, `w_12m`):
- Moving averages: `price_ma_3m/6m/12m`
- Volatility: `price_stddev_3m`
- Range: `price_6m_high/low`
- Oscillators: `stochastic_k_6m/3m` = `(current - min) / (max - min)`, returns 0–1 relative to the period's range
- Trend flags: `above_ma_3m/6m/12m`

**`enriched`** — second layer required because SQL can't reference window aliases in the same SELECT:
- `price_change_3m_pct/12m_pct`: how far current price sits from its 3m/12m moving average (momentum)
- `price_change_since_launch`: `ln(monthly_price / launch_price)` — log appreciation since earliest recorded price; 0 at launch, `ln(10) ≈ 2.3` for a 10x card
- `months_above_ma_12m`: rolling 12-month count of how many months the card stayed above its 12m MA — distinguishes sustained uptrends from brief spikes

**Final SELECT** — joins the two intermediate models and google trends, adds `price_momentum_3m`, `pokemon_interest_score`, `month_of_year`, and three correlated subqueries for forward-looking targets (`next_1m_price`, `next_3m_price`, `next_6m_price`).

---

## ML Training (`ml/train.py`)

**Target:** `return_3m = log(next_3m_price / monthly_price)` — the 3-month log return. Training in log-return space is scale-invariant: a $10 card doubling looks identical to a $500 card doubling. This prevents XGBoost from learning absolute price levels and regressing to the mean on high-value cards.

At inference time, predictions are converted back to dollars: `predicted_price = monthly_price × exp(model.predict(X))`.

**Train/test split:** Temporal cutoff at `2026-03-01` — all data before is training, March 2026 onward is the holdout. A random split would leak future prices into training and produce falsely optimistic metrics.

**Features (28 total):**

| Group | Features |
|---|---|
| Price levels | `monthly_price`, `daily_price` |
| Moving averages | `price_ma_3m/6m/12m` |
| Volatility | `price_stddev_3m` |
| Range | `price_6m_high/low`, `stochastic_k_6m/3m` |
| Momentum | `price_momentum_3m`, `price_change_3m_pct`, `price_change_12m_pct`, `price_change_since_launch` |
| Trend regime | `above_ma_3m/6m/12m`, `months_above_ma_12m` |
| Card fundamentals | `days_since_release`, `is_specialty_set`, `packs_per_specific_card` |
| Market macro | `days_since_recent_set_release`, `hype_weighted_release_90d`, `pokemon_interest_score` |
| Calendar | `month_of_year` |
| Categorical | `rarity`, `variant`, `set_id` |

**Model:** `XGBRegressor` with `enable_categorical=True` (native handling of `rarity`, `variant`, `set_id` without encoding), 500 trees, learning rate 0.05, max depth 6.

**Experiment tracking:** MLflow wraps every run, logging hyperparameters, train/test row counts, dollar-space MAE and RMSE, and the model artifact. Tracking URI is local (`ml/mlruns/`, gitignored).

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Set: POKEMON_TCG_API_KEY

# 1. Build card registry (run once)
cd ingestion && python bootstrap_card_registry.py

# 2. Scrape price history (run once, takes a while)
python ingestion/price_history_scraper.py

# 3. Fetch Google Trends (run once)
python ingestion/google_trends.py

# 4. Run daily price fetch (or set up as cron)
python ingestion/tcgplayer_daily_prices.py

# 5. Run dbt transforms
cd transform/cardstock_dbt
dbt run

# 6. Train model
cd ml && python train.py
```

---

## Known Limitations

- **High-value vintage cards:** The test set RMSE ($15.12) is skewed by ~10 vintage cards (Umbreon, Lugia, Lucky Stadium) that underwent sharp price surges in early 2026. These regime changes are hard to predict from historical patterns alone. For cards under $200, error is substantially lower.
- **No volume data:** Buy/sell volume from marketplaces would be a strong signal but requires paid API access.
- **Pull rate data:** Pack pull rates affect card supply; currently approximated by `packs_per_specific_card` from the registry.

---

*Stack: Python · DuckDB · Apache Parquet · dbt Core · XGBoost · MLflow · pytrends · pokemontcg.io API*
