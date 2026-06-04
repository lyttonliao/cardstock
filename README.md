# Cardstock — Card Price Prediction

An end-to-end ML pipeline that predicts Pokemon TCG card prices 3 months forward. Combines historical price data, TCGPlayer market prices, and Google Trends signals into a feature-rich XGBoost model, served via a FastAPI backend and a Next.js dashboard.

**Current model performance (May 2026):** MAE $4.92 · RMSE $15.12 on a March 2026 holdout set.

**Live:** [cardstock-39m8.vercel.app](https://cardstock-39m8.vercel.app)

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
    │               trains on log returns, saves ml/models/xgb_v1.json
    │
    ▼
[API Layer]         FastAPI (Python)
    │               Serves predictions + price history from DuckDB
    │               Deployed on AWS ECS (Fargate) behind an ALB
    │
    ▼
[Frontend]          Next.js 16 (App Router)
                    Dashboard, card registry, price charts
                    Deployed on Vercel
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
│           ├── intermediate/
│           └── marts/
│               └── fct_card_price_features.sql
├── ml/
│   ├── train.py
│   └── models/xgb_v1.json
├── api/
│   ├── main.py                       # FastAPI app, CORS, lifespan
│   ├── routers/
│   │   ├── cards.py                  # /cards, /cards/movers, /cards/market_aggregates
│   │   ├── predict.py                # /predict, /predict/movers
│   │   ├── sets.py                   # /sets
│   │   └── model.py                  # /model/info
│   ├── schemas/
│   │   ├── cards.py                  # Pydantic response models
│   │   └── predict.py
│   └── dependencies.py               # DuckDB connection + model singletons
├── frontend/
│   ├── app/
│   │   ├── page.tsx                  # Home / landing page
│   │   ├── dashboard/page.tsx        # Market KPI tiles + leaderboards
│   │   ├── registry/
│   │   │   ├── page.tsx              # Set browser
│   │   │   └── cards/
│   │   │       ├── page.tsx          # Card list (infinite scroll)
│   │   │       └── [id]/page.tsx     # Card detail: price chart + prediction
│   │   └── api/[...proxy]/route.ts   # Server-side proxy to bypass mixed content
│   ├── components/
│   │   ├── KPITile/
│   │   ├── PriceChart/
│   │   ├── SearchDialog/
│   │   ├── NavBar/
│   │   ├── Footer/
│   │   └── Badge/
│   ├── lib/
│   │   ├── api.ts                    # API client (server: direct, client: via proxy)
│   │   ├── format.ts                 # Price, percent, date formatters
│   │   └── utils.ts
│   └── types/api.ts                  # TypeScript interfaces for API responses
├── Dockerfile                        # FastAPI container (python:3.13-slim)
├── vercel.json                       # Vercel build config (root: frontend/)
├── .github/workflows/
│   ├── deploy.yml                    # Push to main → build image → deploy to ECS
│   └── daily.yml                     # Daily pipeline cron
└── requirements.txt
```

---

## Frontend

A Next.js 16 App Router application with a dark finance-terminal aesthetic.

### Pages

| Route | Type | Description |
|---|---|---|
| `/` | Static | Landing page with hero and "how it works" |
| `/dashboard` | Static | Market KPIs + Top 10 predicted/actual movers leaderboard |
| `/registry` | Static | Browse sets |
| `/registry/cards` | Client | Infinite-scroll card list, filterable by set |
| `/registry/cards/[id]` | Dynamic | Card detail: price chart, XGBoost prediction, stats |

### Key Components

**`KPITile`** — displays a metric with title, value, and optional context line. Used for Market Cap, 1M/3M Change, Forecast Accuracy, Tracked Cards.

**`LeaderboardTable<T>`** — generic render-prop table with tab switching (Gainers/Losers), built-in rank column, and optional link wrapping per column. Accepts a `columns: Column<T>[]` prop where each column declares `header`, `render`, and optional `href`.

**`PriceChart`** — Recharts line chart rendering monthly price history with a 3-month moving average overlay.

**`SearchDialog`** — Algolia-powered instant search overlay.

### API Client (`lib/api.ts`)

All API calls go through `apiFetch()`. The base URL is resolved at module evaluation time:

```ts
const BASE =
  typeof window === "undefined"
    ? (process.env.API_URL ?? "")           // server component: direct HTTP to ALB
    : (process.env.NEXT_PUBLIC_API_URL ?? "") // client component: /api proxy (HTTPS)
```

**Why two URLs?** The Vercel frontend is served over HTTPS. Browsers block HTTPS pages from making plain HTTP requests (mixed content policy). Server components run in Vercel's Node.js runtime and are not subject to this restriction. So:
- Server components call the ALB directly over HTTP via `API_URL`
- Client components call `/api/...` on the same Vercel origin over HTTPS, which the proxy route forwards to the ALB server-side

### Proxy Route (`app/api/[...proxy]/route.ts`)

A catch-all Next.js API route that forwards browser requests to the backend:

```
Browser → GET https://cardstock.vercel.app/api/sets
       → Vercel server → GET http://alb.../sets
       → response forwarded back to browser
```

### Environment Variables

| Variable | Where set | Value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Vercel + `.env.local` | `/api` (routes through proxy) |
| `API_URL` | Vercel only (server-side) | `http://cardstock-alb-...elb.amazonaws.com` |
| `NEXT_PUBLIC_ALGOLIA_APP_ID` | Vercel + `.env.local` | Algolia app ID |
| `NEXT_PUBLIC_ALGOLIA_SEARCH_KEY` | Vercel + `.env.local` | Algolia search-only key |

---

## API

FastAPI application serving predictions and price data from DuckDB. DuckDB is opened once at startup in read-only mode; the XGBoost model is loaded once and reused across requests.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | ALB health check → `{"status":"ok"}` |
| `GET` | `/sets` | All tracked sets |
| `GET` | `/cards` | Paginated card list with optional filters |
| `GET` | `/cards/{id}/prices` | Monthly + daily price history for a card |
| `GET` | `/cards/{id}/variants` | Available variants for a card |
| `GET` | `/cards/market_aggregates` | Total market cap, MAE, RMSE, historical caps |
| `GET` | `/cards/movers` | Top 10 gainers/losers by actual 3-month return |
| `POST` | `/predict` | XGBoost inference: returns log return + predicted price |
| `GET` | `/predict/movers` | Top 10 predicted gainers/losers by model output |
| `GET` | `/model/info` | Model metadata, feature names |

### Startup Lifecycle

On ECS startup, the container downloads the latest DuckDB file and XGBoost model from S3, then opens them. This means data updates from the daily pipeline are picked up on the next deploy or task restart.

```python
@asynccontextmanager
async def lifespan(app):
    if settings.s3_bucket:
        download(["registry", "duckdb", "model"])  # pull from S3
    conn = duckdb.connect(DB_PATH, read_only=True)  # shared read-only connection
    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(MODEL_PATH)
    set_db_conn(conn)
    set_model(xgb_model)
    yield
    conn.close()
```

---

## Infrastructure

### AWS

```
                    ┌────────────────────────────────────┐
                    │              VPC                    │
                    │   vpc-04f0a60eb7e00b440             │
                    │                                     │
  Internet ──────►  │  [ALB: cardstock-alb]              │
  port 80           │   SG: cardstock-alb-sg             │
                    │   (inbound :80 from 0.0.0.0/0)     │
                    │           │                        │
                    │           ▼                        │
                    │  [Target Group: cardstock-tg]      │
                    │   health: GET /health every 30s    │
                    │           │                        │
                    │           ▼                        │
                    │  [ECS Task: Fargate]               │
                    │   SG: sg-0fba07ba139280536         │
                    │   (inbound :8000 from ALB SG only) │
                    │   FastAPI on port 8000             │
                    └────────────────────────────────────┘
```

#### Concepts

**VPC (Virtual Private Cloud)** — An isolated virtual network. All AWS resources live inside it and communicate over private IP addresses.

**Subnets** — Subdivisions of the VPC, each bound to one availability zone. The ECS tasks and ALB span two subnets (`us-east-2a`, `us-east-2b`) so traffic continues if one AZ has issues.

**Security Groups** — Stateful virtual firewalls attached to individual resources. Rules define allowed inbound and outbound traffic by protocol, port, and source. Stateful means response traffic is automatically permitted without an explicit outbound rule. Two are used here:
- `cardstock-alb-sg` (ALB): inbound TCP :80 from `0.0.0.0/0` — any browser can reach the ALB
- `sg-0fba07ba139280536` (ECS tasks): inbound TCP :8000 from `cardstock-alb-sg` only — the container is never directly reachable from the internet, only through the ALB

**ECR (Elastic Container Registry)** — AWS's private Docker image registry. GitHub Actions builds images and pushes them here tagged with the commit SHA. ECS pulls from here on deploy.

**ECS + Fargate** — ECS is AWS's container orchestration layer. Fargate is the serverless compute backend: no EC2 instances to manage. Three constructs:
- **Task Definition** — the container blueprint: image URI, CPU/memory, port mappings, environment variables
- **Service** — instructs ECS to keep N tasks running. On deploy, it starts a new task, waits for health checks, then drains and stops the old one (zero-downtime rolling deploy)
- **Task** — a single running container instance, assigned a private IP in the VPC

**ALB (Application Load Balancer)** — HTTP/HTTPS load balancer with a stable public DNS name that doesn't change between deploys. Components:
- **Listener** — listens on port 80, forwards traffic to the target group
- **Target Group** — a pool of registered ECS task IPs. The ALB sends traffic only to healthy targets
- **Health Check** — every 30 seconds, calls `GET /health` on port 8000. Two consecutive 200s → `healthy`. Three failures → target removed from rotation

#### Deployment Flow (GitHub Actions → ECS)

Triggered on push to `main`:

```
1. Checkout code
2. Configure AWS credentials (from GitHub Secrets)
3. Login to ECR
4. docker build -t $ECR/$REPO:$COMMIT_SHA .
5. docker push to ECR
6. Fetch current ECS task definition JSON
7. Swap container image field → new task definition revision
8. Register new revision with ECS
9. Update ECS service → rolling deploy begins
10. ECS starts new task → task registers with target group
11. ALB runs health checks on new task
12. Once healthy, ALB routes traffic to new task
13. Old task drains connections and stops
14. Workflow blocks until service is stable
```

Every deploy is tagged with the commit SHA, enabling rollback to any previous ECR image.

### Vercel

The Next.js frontend deploys automatically on every push to the connected branch. Configuration:
- `frontend/vercel.json` — sets `buildCommand`, `installCommand`, `framework`
- Root Directory in Vercel project settings — set to `frontend`
- Environment variables configured in Vercel project settings (see table above)

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
Fetches US search interest for `["pokemon cards", "pokemon tcg"]` over the full data window using pytrends (Google Trends unofficial API). Averages both keywords into a single `interest_score`, then resamples weekly data to monthly using `resample("MS")` (month-start).

---

## Transform (dbt)

### Staging

Thin wrappers that read Parquet via DuckDB's `read_parquet()` and standardise types/names. Notable:
- `stg_card_registry.sql`: `cast(replace(set_release_date, '/', '-') as date)` — the API returns dates as `"2024/01/26"`, DuckDB needs hyphens
- `stg_daily_price_history.sql`: renames `market_price` → `tcgplayer_market_price`

### `int_card_daily_prices.sql`

Joins monthly PriceCharting history with registry metadata and daily TCGPlayer prices. The core challenge: PriceCharting snapshots land on the 1st of each month while TCGPlayer daily data has dates like `2026-04-30` — a direct join produces no matches. Solution: a `daily_prices_monthly` CTE aggregates daily prices to monthly averages using `date_trunc('month', ...)`, then the join matches on month.

### `int_set_release_features.sql`

Computes two macro market signals per price date: `days_since_recent_set_release` and `hype_weighted_release_90d` (sum of average launch prices for sets released in the trailing 90 days). Uses `QUALIFY ROW_NUMBER() OVER (...) = 1` to deduplicate to one row per card per date.

### `fct_card_price_features.sql`

The final feature table — one row per card per month, ~30 columns. Three CTE layers:

**`windowed`** — rolling window features (`w_3m`, `w_6m`, `w_12m`): moving averages, volatility, range, stochastic oscillators, trend flags.

**`enriched`** — second pass required because SQL can't reference window aliases in the same SELECT: momentum ratios, log appreciation since launch, months above 12m MA.

**Final SELECT** — joins the two intermediate models and Google Trends, adds forward-looking targets (`next_1m_price`, `next_3m_price`, `next_6m_price`) as correlated subqueries.

---

## ML Training (`ml/train.py`)

**Target:** `return_3m = log(next_3m_price / monthly_price)` — the 3-month log return. Log-return space is scale-invariant: a $10 card doubling looks identical to a $500 card doubling. At inference time: `predicted_price = monthly_price × exp(model.predict(X))`.

**Train/test split:** Temporal cutoff at `2026-03-01`. A random split would leak future prices into training.

**Features (28 total):**

| Group | Features |
|---|---|
| Price levels | `monthly_price`, `daily_price` |
| Moving averages | `price_ma_3m/6m/12m` |
| Volatility | `price_stddev_3m` |
| Range | `price_6m_high/low`, `stochastic_k_6m/3m` |
| Momentum | `price_momentum_3m`, `price_vs_ma_3m`, `price_vs_ma_12m`, `price_change_since_launch` |
| Trend regime | `above_ma_3m/6m/12m`, `months_above_ma_12m` |
| Card fundamentals | `days_since_release`, `is_specialty_set`, `packs_per_specific_card` |
| Market macro | `days_since_recent_set_release`, `hype_weighted_release_90d`, `pokemon_interest_score` |
| Calendar | `month_of_year` |
| Categorical | `rarity`, `variant`, `set_id` |

**Model:** `XGBRegressor` with `enable_categorical=True`, 500 trees, learning rate 0.05, max depth 6.

**Experiment tracking:** MLflow logs hyperparameters, row counts, MAE, RMSE, and model artifact per run. Tracking URI is local (`ml/mlruns/`, gitignored).

---

## Getting Started

### Backend + Pipeline

```bash
pip install -r requirements.txt

# 1. Build card registry (run once)
python ingestion/bootstrap_card_registry.py

# 2. Scrape price history (run once)
python ingestion/price_history_scraper.py

# 3. Fetch Google Trends (run once)
python ingestion/google_trends.py

# 4. Run daily price fetch
python ingestion/tcgplayer_daily_prices.py

# 5. Run dbt transforms
cd transform/cardstock_dbt && dbt run

# 6. Train model
python ml/train.py

# 7. Start API
uvicorn api.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

`.env.local` (in `frontend/`):

```
NEXT_PUBLIC_API_URL=/api
API_URL=http://localhost:8000
NEXT_PUBLIC_ALGOLIA_APP_ID=...
NEXT_PUBLIC_ALGOLIA_SEARCH_KEY=...
```

---

## Known Limitations

- **High-value vintage cards:** RMSE is skewed by ~10 vintage cards (Umbreon, Lugia, Lucky Stadium) that underwent sharp price surges in early 2026. Regime changes are hard to predict from historical patterns. Error is substantially lower for cards under $200.
- **No volume data:** Buy/sell volume would be a strong signal but requires paid API access.
- **Pull rate data:** Pack pull rates affect card supply; currently approximated by `packs_per_specific_card`.

---

*Stack: Python · FastAPI · DuckDB · Apache Parquet · dbt Core · XGBoost · MLflow · Next.js 16 · TypeScript · Tailwind CSS v4 · Recharts · Algolia · AWS ECS Fargate · AWS ALB · AWS ECR · Vercel · GitHub Actions*
