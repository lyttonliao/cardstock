# pipeline/ — Claude Context

Orchestration layer. Coordinates ingestion, transforms, and S3 sync. Runs in GitHub Actions.

## Files

```
daily.py     Daily pipeline: download S3 → ingest → dbt run → upload S3
monthly.py   Monthly pipeline: likely retraining
s3.py        S3 upload/download helpers
```

## daily.py — Execution Order

```
1. download(["registry", "duckdb", "model"])   ← pull latest from S3
2. python ingestion/update_card_registry.py    ← refresh card metadata
3. python ingestion/tcgplayer_daily_prices.py  ← today's prices
4. dbt run                                     ← rebuild fct_card_price_features
5. upload(["registry", "daily_prices", "duckdb"]) ← push updated files to S3
```

Steps run via `subprocess.run(..., check=True)` from the repo root. A failure in any step raises `CalledProcessError` and stops the pipeline — subsequent steps are skipped. Check GitHub Actions logs to see which step failed.

## s3.py — Asset Keys

```python
S3_KEYS = {
    "registry":     "data/registry/card_registry.parquet",
    "duckdb":       "transform/cardstock_dbt/dev.duckdb",
    "model":        "ml/models/xgb_v1.json",
    "daily_prices": "data/prices/daily_price_history.parquet",
}
```

`download(keys)` and `upload(keys)` accept a list of these string keys. The S3 bucket is read from `core/config.py::settings.s3_bucket`. If `s3_bucket` is not set, download/upload are no-ops (safe for local development).

## GitHub Actions Triggers

- `deploy.yml` — push to `main` → builds Docker image → deploys to ECS
- `daily.yml` — cron at noon UTC → runs `pipeline/daily.py` inside the ECS container or a separate runner

## Local Development

The pipeline scripts are not meant to run locally against production S3. For local dev:
- Run ingestion scripts directly: `python ingestion/tcgplayer_daily_prices.py`
- Run dbt manually: `cd transform/cardstock_dbt && dbt run`
- S3 download/upload require `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET` in `.env`

## Common Failure Modes

| Failure | Where to look |
|---|---|
| Timeout fetching pokemontcg.io | `ingestion/tcgplayer_daily_prices.py` — retried 4x, skips set on total failure |
| dbt model error | GitHub Actions logs, or `transform/cardstock_dbt/logs/` |
| S3 permission error | Check IAM role attached to the GitHub Actions runner has `s3:GetObject`/`s3:PutObject` on the bucket |
| ECS task can't read DB | Check if `download(["duckdb"])` ran at API startup — requires `S3_BUCKET` env var to be set |
