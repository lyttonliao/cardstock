# Cardstock — Claude Context

Pokemon TCG card price prediction platform. End-to-end: data ingestion → dbt transforms → XGBoost model → FastAPI → Next.js frontend.

## Monorepo Layout

```
api/          FastAPI backend (Python)
core/         Shared config (Settings via pydantic-settings)
ingestion/    Data ingestion scripts
transform/    dbt project (cardstock_dbt/) + DuckDB file
ml/           XGBoost training + MLflow experiments
pipeline/     Orchestration: daily.py, monthly.py, s3.py
frontend/     Next.js 16 app
data/         Local Parquet files (gitignored)
```

## How the Data Flows

```
pokemontcg.io API + PriceCharting scraper
    → Parquet files in data/
    → dbt run (fct_card_price_features in dev.duckdb)
    → ml/train.py (XGBoost, saves ml/models/xgb_v1.json)
    → api/ reads DuckDB + model at startup (downloaded from S3)
    → frontend/ calls api/ for data
```

## Key Invariants

- **DuckDB is read-only in the API.** `duckdb.connect(DB_PATH, read_only=True)` — never open it read-write in API code. Write access belongs only to the pipeline.
- **Card identity = `(card_id, variant)`.** A card like "Charizard sv3pt5-1" exists as multiple rows — `normal`, `holofoil`, `reverseHolofoil`. Always filter/group by both fields.
- **Prices are log returns in the ML layer.** The model predicts `log(next_3m_price / monthly_price)`. Convert back to dollars at inference: `monthly_price * exp(prediction)`.
- **Temporal split, not random.** Train cutoff is `2026-03-01` (`api/constants.py::TRAIN_CUTOFF`). Never use random splits for this time-series data.
- **S3 is the source of truth in production.** The API pulls `registry`, `duckdb`, and `model` from S3 at startup. The pipeline pushes updated files after each run.

## Branches

- `main` — production; push here triggers ECS API deploy via GitHub Actions
- `new_ml_training_features` — current active feature branch
- `frontend` — was the frontend development branch (now merged)

## Deployment

- **API**: AWS ECS Fargate, behind `cardstock-alb` (ALB). GitHub Actions (`deploy.yml`) deploys on push to `main`.
- **Frontend**: Vercel, auto-deploys from connected branch. Root directory: `frontend/`.
- **Health check**: `GET /health` on port 8000 — required by ALB. Must return 200.

## Environment Variables

Backend (`.env`):
- `POKEMON_TCG_API_KEY` — pokemontcg.io
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- `S3_BUCKET` — where DuckDB/model/registry live
- `ALGOLIA_APP_ID`, `ALGOLIA_WRITE_KEY`

Frontend (`frontend/.env.local`):
- `NEXT_PUBLIC_API_URL=/api` — client-side calls go through Next.js proxy
- `API_URL=http://localhost:8000` — server components call the API directly
- `NEXT_PUBLIC_ALGOLIA_APP_ID`, `NEXT_PUBLIC_ALGOLIA_SEARCH_KEY`
