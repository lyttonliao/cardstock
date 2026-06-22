# pipeline/ — Claude Context

Orchestration layer. Coordinates ingestion, transforms, and S3 sync. Runs in GitHub Actions.

## Files

```
daily.py     Daily pipeline: download S3 → ingest → dbt run → upload S3
monthly.py   Monthly pipeline: Google Trends → dbt run → retrain XGBoost → upload S3
s3.py        S3 upload/download helpers (simplified — no LOCAL_ONLY logic)
```

## daily.py — Execution Order

```
1. download(["registry", "daily_prices", "duckdb"])  ← pull latest from S3 (not model)
2. python ingestion/update_card_registry.py          ← refresh card metadata
3. python ingestion/tcgplayer_daily_prices.py        ← today's prices
4. dbt run                                           ← rebuild fct_card_price_features
5. upload(["registry", "daily_prices", "duckdb"])    ← push updated files to S3
```

Steps run via `subprocess.run(..., check=True)` from the repo root. A failure in any step raises `CalledProcessError` and stops the pipeline — subsequent steps are skipped. Check GitHub Actions logs to see which step failed.

## monthly.py — Execution Order

Runs on the 1st of each month. Includes model retraining, so takes longer.

```
1. download(["daily_prices", "duckdb", "model"])  ← pull latest from S3
2. python ingestion/google_trends.py              ← monthly Pokemon interest score
3. dbt run                                        ← rebuild with new trends data
4. python ml/train.py                             ← retrain XGBoost
5. upload(["daily_prices", "duckdb", "model"])    ← push updated artifacts to S3
```

## GitHub Actions Cadence

| Workflow | Trigger | What it does |
|---|---|---|
| `daily.yml` | cron — noon UTC, daily | Runs `pipeline/daily.py` (ingest + dbt + upload) |
| `monthly.yml` | cron — 2 PM UTC, 1st of month | Runs `pipeline/monthly.py` (trends + dbt + retrain + upload) |
| `deploy.yml` | push to `main` | Builds Docker image → deploys to AWS ECS Fargate |

## s3.py — Asset Keys

```python
S3_KEYS = {
    "registry":     "data/registry/card_registry.parquet",
    "duckdb":       "transform/cardstock_dbt/dev.duckdb",
    "model":        "ml/models/xgb_v1.json",
    "daily_prices": "data/prices/daily_price_history.parquet",
}
```

`download(keys)` and `upload(keys)` accept a list of these string keys. The S3 bucket is read from `core/config.py::settings.s3_bucket`.

**Manual sync from the command line:**
```bash
python pipeline/s3.py download registry duckdb model
python pipeline/s3.py upload duckdb model registry
python pipeline/s3.py download daily_prices
```

`s3.py` has no LOCAL_ONLY logic — it always syncs when called. The LOCAL_ONLY guard lives only in `api/main.py` (prevents startup from overwriting local files when `LOCAL_ONLY=1` is set in `.env`).

## Local Development

For local dev, run scripts directly without going through the pipeline orchestration:
- `python ingestion/tcgplayer_daily_prices.py`
- `cd transform/cardstock_dbt && dbt run`
- `python pipeline/s3.py download <key>` — manually pull from S3 when you need fresh data
- S3 commands require `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET` in `.env`
- Set `LOCAL_ONLY=1` in `.env` so the API doesn't overwrite your local files on startup

## Common Failure Modes

| Failure | Where to look |
|---|---|
| Timeout fetching pokemontcg.io | `ingestion/tcgplayer_daily_prices.py` — retried 4x, skips set on total failure |
| dbt model error | GitHub Actions logs, or `transform/cardstock_dbt/logs/` |
| S3 permission error | Check IAM role attached to the GitHub Actions runner has `s3:GetObject`/`s3:PutObject` on the bucket |
| ECS task can't read DB | Check if `download(["duckdb"])` ran at API startup — requires `S3_BUCKET` env var to be set |
