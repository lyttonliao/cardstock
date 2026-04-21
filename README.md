# Cardstock — Card Price Oracle

A end-to-end ML system that predicts trading card prices by learning from historical price trends and card attributes. Built for Pokemon and One Piece TCG markets. Card price prediction has rich feature engineering — set release cycles, print run announcements, PSA population reports, pull rate data, and influencer hype cycles are all predictable signals. 

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION                           │
│                                                                 │
│   eBay Sold Listings ──┐                                        │
│   TCGPlayer API ───────┼──► GitHub Actions (cron) ──► Parquet  │
│   Reddit / Discord ────┘                              on R2     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TRANSFORMATION (dbt)                       │
│                                                                 │
│   Raw Parquet ──► DuckDB ──► dbt models ──► Feature tables      │
│                              (tested, typed, documented)        │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ML TRAINING                               │
│                                                                 │
│   Feature tables ──► XGBoost / Prophet ──► MLflow (Railway)     │
│                                            SHAP explainability  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVING                                   │
│                                                                 │
│   FastAPI (Railway) ──► React Dashboard (Vercel)                │
│   /predict endpoint        Recharts time-series                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE                              │
│                                                                 │
│   Terraform ──► terraform plan on PR / apply on merge           │
│                 (Railway services + R2 bucket as code)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Deep Dives

### 1. Data Sources

#### eBay Finding API + Playwright (Scraping)

**What it is:** eBay's Finding API gives access to completed (sold) listings — the actual transaction prices, not just asking prices. For cards not well-covered by the API, Playwright (a browser automation library) handles JavaScript-rendered pages.

**Why completed listings matter:** A card listed at $500 is noise. A card *sold* for $500 is signal. This distinction is the foundation of any serious price model. The eBay completed listings feed is the closest thing the card market has to a real-time exchange.

**What you build:**
- An idempotent scraper: running it twice on the same day writes the same data, never duplicates. This is a distributed systems concept interviewers probe directly.
- Deduplication by listing ID before writing to Parquet
- Exponential backoff with jitter on rate limit (429) responses

**Interview talking point:** *"I designed the scraper to be idempotent — each run checks for existing listing IDs before writing, so reruns after a failure don't corrupt the dataset. This mirrors exactly how Kafka consumers handle at-least-once delivery."*

---

#### TCGPlayer API

**What it is:** TCGPlayer is the largest dedicated TCG marketplace. Their API provides structured market data: market price, low/mid/high, foil vs non-foil, condition breakdowns. Free tier with API key.

**What you build:**
- Paginated ingestion with cursor-based pagination (a common interview topic)
- Handling product variants: same card, different conditions (NM, LP, MP) are separate SKUs
- Price normalization across condition grades

**Interview talking point:** *"TCGPlayer gives me structured market aggregates while eBay gives raw transaction-level data. I join them on card ID to get both the 'official' market price and what cards are actually clearing for in real auctions — the spread between them is itself a feature."*

---

#### PRAW — Reddit API Wrapper

**What it is:** PRAW (Python Reddit API Wrapper) is the standard library for Reddit's API. Subreddits like r/PokemonTCG, r/pkmntcg, and r/OnePieceTCG are the primary hype signal sources.

**What you build:**
- Post and comment ingestion from target subreddits on a daily cron
- Keyword extraction: card names, set names, price mentions
- Sentiment scoring using VADER (rule-based, no GPU needed) or a small HuggingFace model

**Why it matters for the model:** Price spikes on cards frequently lead or coincide with Reddit discussion volume. A card getting 50 posts in 24 hours is a measurable leading indicator. This is the kind of domain-specific feature engineering that makes interviewers lean in.

**Interview talking point:** *"Social signal is a leading indicator, not a lagging one. I measure Reddit mention velocity — posts per day on a card — and it correlates with price movement 1-3 days later. That lag is actually useful: it gives the model a predictive window."*

---

### 2. Storage

#### DuckDB + Apache Parquet

**What it is:** DuckDB is an in-process analytical database — it runs inside your Python script or CLI, no server required. It reads Parquet files directly, executing SQL with columnar performance. Parquet is a binary column-oriented file format designed for analytical workloads.

**Why not SQLite or Postgres?** SQLite is row-oriented and slow on analytical queries. Postgres requires a running server. DuckDB + Parquet gives you:
- Columnar compression (a 1M row price history file might be 8MB on disk)
- SQL on files without loading into memory
- Zero ops — no database to manage, back up, or pay for
- Portable: the entire dataset is just files you can copy anywhere

**The data lake pattern:** Raw data lands in Parquet on object storage (Cloudflare R2). DuckDB reads it directly via the HTTP URL. No ETL pipeline needed to "load" data — the query engine reads the files in place.

```
r2://cardstock-data/
  raw/
    ebay/2025-01-15.parquet
    ebay/2025-01-16.parquet
    tcgplayer/2025-01-15.parquet
  transformed/
    features/card_price_features.parquet
```

**Interview talking point:** *"I deliberately chose DuckDB over Postgres because the workload is analytical — range scans over time-series data, aggregations, joins. DuckDB's columnar execution is 10-100x faster for this access pattern. This is the same reasoning behind why data warehouses like BigQuery and Snowflake use columnar storage."*

---

#### Cloudflare R2

**What it is:** R2 is Cloudflare's S3-compatible object storage. 10GB free, no egress fees (unlike AWS S3), and accessible via the standard boto3/S3 SDK by just changing the endpoint URL.

**Why it matters:** It's a real production data lake, not a local folder. Your GitHub Actions runners write to R2, your dbt models read from R2, your training jobs pull from R2 — all using standard S3 interfaces. This is cloud-native architecture without cloud costs.

**Interview talking point:** *"Using R2 means I can swap to AWS S3 by changing one environment variable. The interface is identical. This is the portability argument for cloud-agnostic tooling."*

---

### 3. Transformation

#### dbt Core

**What it is:** dbt (data build tool) lets you write data transformations as SQL `SELECT` statements. It handles the `CREATE TABLE AS SELECT` boilerplate, manages dependencies between models, runs data quality tests, and generates documentation automatically.

**The file that makes interviewers nod:** A dbt project has a `schema.yml` that looks like:

```yaml
models:
  - name: card_price_features
    description: "Daily card price features joined with social signals"
    columns:
      - name: price_usd
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 100000
      - name: card_id
        tests:
          - not_null
          - unique
```

This is automated data quality. Every dbt run validates your data contracts. If a scraper starts returning nulls or negative prices, the pipeline fails loudly before bad data reaches your model.

**The DAG:** dbt builds a directed acyclic graph of your models. `stg_ebay_sales` feeds into `int_card_daily_prices` feeds into `fct_card_price_features`. This is the exact mental model data engineers use for pipeline dependencies — and dbt makes it visual.

**Interview talking point:** *"Junior portfolios have notebooks. dbt gives me tested, documented, version-controlled transformations that anyone on the team can run. The data quality tests caught a bug where the eBay scraper was returning listing prices instead of sold prices — the `accepted_range` test failed immediately."*

---

### 4. Machine Learning

#### XGBoost / LightGBM

**What it is:** Gradient boosting libraries for tabular data. XGBoost and LightGBM are decision tree ensembles that win most Kaggle competitions on structured data. They handle missing values natively, are robust to feature scaling, and train in seconds on datasets of this size.

**Why not a neural network?** For tabular data with engineered features, gradient boosting consistently outperforms deep learning. Using a neural network here would signal you're chasing complexity over results. Interviewers respect the correct tool for the task.

**Features you engineer:**
- Rolling averages: 7-day, 30-day, 90-day price, 200-day price
- Price momentum: current price vs moving averages
- Reddit mention velocity: posts/day over a range of time
- PSA population growth rate: new graded copies per week (might exclude PSA)
- Days since set release
- Is reprint announced (binary)
- Pull rate (cards per box for this rarity)
- Tournament appearance count (trailing 30 days)

**Interview talking point:** *"The model's most important features were 30-day price momentum and public sentiment/mention velocity. SHAP values told me that — which leads into how I used explainability to validate that the model was learning real signals, not spurious correlations."*

---

#### Prophet

**What it is:** Facebook's open-source time series forecasting library. It fits an additive model with trend, seasonality, and holiday components. It handles missing data and outliers well, and produces uncertainty intervals out of the box.

**Role in this project:** Prophet serves as the baseline model. Every ML project needs a baseline to beat — it's the benchmark that justifies the complexity of XGBoost. If XGBoost only marginally outperforms Prophet, that's a finding worth explaining.

**Interview talking point:** *"I ran Prophet as a baseline to establish how much of the price movement is explainable by pure time-series trend and seasonality. XGBoost with engineered features outperformed it by 23% on MAE — which tells me the cross-sectional features (social signals, population reports) are genuinely adding predictive value beyond what the time series alone captures."*

---

#### MLflow (hosted on Railway)

**What it is:** MLflow is the open-source standard for ML experiment tracking. Every training run logs: hyperparameters, metrics (MAE, RMSE, R²), artifacts (model files, SHAP plots), and the code version that produced them.

**What you track:**
```
Run: xgb_v3_2025-01-15
  Params: n_estimators=500, max_depth=6, learning_rate=0.05
  Metrics: val_mae=2.31, val_rmse=4.87, val_r2=0.78
  Artifacts: model.pkl, shap_summary.png, feature_importance.json
```

**Why it matters:** Without MLflow, you can't answer "which model version is in production?" or "what hyperparameters produced that result last month?" These are questions you will be asked in any ML engineering interview.

**Interview talking point:** *"MLflow gave me reproducibility — every model in production has a logged run ID, and I can re-derive any artifact from scratch given that run's logged parameters and the Git SHA it was trained on."*

---

#### SHAP (SHapley Additive exPlanations)

**What it is:** SHAP computes each feature's contribution to each individual prediction using game theory (Shapley values). For tree models like XGBoost, it runs in O(TLD) time — fast enough for production use.

**What you produce:**
- Summary plots: which features matter most across the entire dataset
- Waterfall plots: for a single card, why is the model predicting $45 vs $30?
- Dependence plots: how does Reddit mention velocity affect price predictions across the range?

**Interview talking point:** *"When the model predicted an unusually high price for a card, I ran a SHAP waterfall plot. The top contributor was Reddit mention velocity spiking 400% — which turned out to be a streamer posting about the card that day. That kind of explainability is what separates a model you can trust from a black box."*

---

### 5. Serving

#### FastAPI

**What it is:** FastAPI is the modern Python web framework for building APIs. It's built on Starlette (ASGI) and Pydantic, giving you async request handling, automatic OpenAPI docs, and runtime type validation out of the box.

**What you build:**
```
POST /predict
  body: { card_id: str, horizon_days: int }
  response: { predicted_price: float, confidence_interval: [float, float], shap_values: {...} }

GET /cards/{card_id}/history
  response: { prices: [{date, price, volume}] }

GET /health
  response: { status: "ok", model_version: str, last_trained: str }
```

**The `/health` endpoint matters:** In interviews about production systems, you'll be asked about observability. A health endpoint that exposes model version and last training date shows you think about ops, not just code.

**Interview talking point:** *"FastAPI's dependency injection lets me swap the model artifact in tests without changing the endpoint logic — the same pattern you'd use in Spring or ASP.NET. It also generates OpenAPI docs automatically, which is what the React frontend consumes to stay in sync with the API contract."*

---

#### React + Recharts

**What it is:** React is the standard frontend library. Recharts is a React-native charting library built on D3 — it handles the SVG rendering for you while staying idiomatic React (components, props, state).

**What you build:**
- Price history chart: candlestick or line chart of daily prices with volume bars
- Forecast overlay: predicted price with confidence interval shaded
- Feature importance sidebar: which signals drove this card's prediction
- Card search with autocomplete

**Why Recharts over D3 directly:** D3 is powerful but imperative — you manipulate the DOM directly. Recharts wraps D3 in React components, so the chart re-renders when data changes and integrates cleanly with React state. For a portfolio project, this is the pragmatic choice.

**Interview talking point:** *"I used Recharts because the charts need to respond to user interactions — selecting a date range re-queries the API and re-renders. D3 would work, but Recharts keeps the rendering inside React's reconciler, which is the correct mental model for a React app."*

---

### 6. Infrastructure

#### GitHub Actions (Free Cloud Compute)

**What it is:** GitHub Actions is CI/CD with cron scheduling. It runs workflows on GitHub's servers — 2,000 free minutes/month on private repos, unlimited on public.

**How it powers this project:**

```yaml
# .github/workflows/ingest.yml
on:
  schedule:
    - cron: '0 6 * * *'   # 6 AM UTC daily

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - run: python ingestion/ebay_scraper.py
      - run: python ingestion/tcgplayer_scraper.py
      - run: python ingestion/reddit_scraper.py

# .github/workflows/transform.yml
on:
  workflow_run:
    workflows: ["ingest"]
    types: [completed]

jobs:
  transform:
    steps:
      - run: dbt run && dbt test

# .github/workflows/retrain.yml
on:
  schedule:
    - cron: '0 8 * * 0'   # Sunday 8 AM — weekly retrain
```

**The key design principle — idempotency:** Every job can be re-run without corrupting data. This is the distributed systems property that makes cron jobs safe. Interviewers probe this: "what happens if the job runs twice?"

**Interview talking point:** *"GitHub Actions is my orchestrator. Each workflow is triggered by the previous completing successfully — ingest, then transform, then optionally retrain. This is a simplified version of the DAG scheduling that Airflow and Prefect do, and it costs nothing."*

---

#### Terraform

**What it is:** Terraform is an infrastructure-as-code tool. You declare what infrastructure you want in `.tf` files, run `terraform plan` to preview changes, and `terraform apply` to provision them.

**What you define:**
```hcl
# infrastructure/main.tf

resource "cloudflare_r2_bucket" "cardstock_data" {
  name = "cardstock-data"
}

resource "railway_service" "mlflow" {
  name        = "mlflow-server"
  source_image = "ghcr.io/mlflow/mlflow:latest"
}

resource "railway_service" "fastapi" {
  name   = "cardstock-api"
  source = { repo = "your-org/cardstock" }
}
```

**The CI integration:**
```yaml
# On pull request: show what would change
- run: terraform plan

# On merge to main: apply the changes
- run: terraform apply -auto-approve
```

**Why this is a senior signal:** Clicking through a UI to provision infrastructure is not reproducible, not reviewable, and not recoverable when something goes wrong. Terraform means your infrastructure is in Git — it has history, it goes through code review, and you can rebuild from scratch in minutes.

**Interview talking point:** *"Every infrastructure change goes through a pull request. The CI pipeline runs `terraform plan` and posts the diff as a comment — same as a code diff, but for cloud resources. When a reviewer approves and the PR merges, `terraform apply` runs automatically. This is exactly how infrastructure teams at scale operate."*

---

#### Railway

**What it is:** Railway is a PaaS (Platform as a Service) that deploys Docker containers from a Git repo or image. It has a generous free tier and handles networking, environment variables, and persistent volumes.

**What runs on Railway:**
- **MLflow Tracking Server** — stores experiment metadata in Railway's managed Postgres, artifacts in R2
- **FastAPI prediction server** — auto-deploys on push to `main`

**Why Railway over Heroku/Render:** Railway's free tier is more generous, the developer experience is better, and it supports more service types. The important thing for this project is that it gives you a real HTTPS URL for your API — not localhost.

**Interview talking point:** *"I deploy to Railway via a `railway.toml` config file in the repo. Push to main triggers a build and deploy — zero manual steps. Combined with Terraform for provisioning the services themselves, the entire deployment process is automated and documented in code."*

---

## Feature Engineering Reference

The features that differentiate this model from a naive time-series predictor:

| Feature | Type | Signal |
|---|---|---|
| `price_ma_7d` | Numeric | Short-term momentum |
| `price_ma_30d` | Numeric | Medium-term trend |
| `price_ma_90d` | Numeric | Long-term baseline |
| `price_momentum` | Numeric | Current vs 30d MA ratio |
| `reddit_mentions_7d` | Numeric | Social hype velocity |
| `reddit_sentiment_avg` | Numeric | Positive vs negative discussion |
| `psa_pop_growth_rate` | Numeric | Supply pressure signal |
| `days_since_set_release` | Numeric | Set lifecycle position |
| `is_reprint_announced` | Binary | Major supply shock |
| `pull_rate_rarity` | Numeric | Pack EV component |
| `tournament_appearances_30d` | Numeric | Competitive demand |
| `ebay_tcgplayer_spread` | Numeric | Cross-market arbitrage signal |

---

## Project Structure

```
cardstock/
├── .github/
│   └── workflows/
│       ├── ingest.yml          # Daily scraping cron
│       ├── transform.yml       # dbt run + test
│       └── retrain.yml         # Weekly model retrain
├── ingestion/
│   ├── ebay_scraper.py
│   ├── tcgplayer_scraper.py
│   └── reddit_scraper.py
├── transform/
│   └── cardstock_dbt/          # dbt project
│       ├── models/
│       │   ├── staging/        # Raw → typed
│       │   ├── intermediate/   # Business logic
│       │   └── marts/          # Feature tables
│       └── tests/
├── training/
│   ├── train_xgboost.py
│   ├── train_prophet.py
│   └── evaluate.py
├── api/
│   └── main.py                 # FastAPI app
├── dashboard/
│   └── src/                    # React app
├── infrastructure/
│   └── main.tf                 # Terraform config
└── README.md
```

---

## Getting Started

```bash
# Clone and install
git clone https://github.com/your-org/cardstock
cd cardstock
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in: EBAY_API_KEY, TCGPLAYER_API_KEY, REDDIT_CLIENT_ID, R2_ACCESS_KEY, etc.

# Run ingestion locally
python ingestion/ebay_scraper.py --date 2025-01-15

# Run dbt transformations
cd transform/cardstock_dbt
dbt run && dbt test

# Train model
python training/train_xgboost.py

# Start API
uvicorn api.main:app --reload

# Start dashboard
cd dashboard && npm install && npm run dev
```

---

## Data Collection Timeline

Run the scrapers for **90 days minimum** before training. A year of daily price history across 5,000 cards is a real dataset — enough to demo forecasts that visually nail the price spike after a card appears in a competitive deck, or the crash after a reprint is announced.

---

*Built with DuckDB, dbt Core, XGBoost, MLflow, FastAPI, React, and Terraform. Deployed on Railway and Cloudflare R2.*
