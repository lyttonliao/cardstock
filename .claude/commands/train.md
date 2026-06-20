---
description: Retrain the XGBoost price prediction model, compare MLflow metrics, and optionally upload the new artifact to S3.
---

You are running the Cardstock ML retraining workflow. Follow these steps in order:

**Step 1 — Verify data freshness**
Check that dbt has been run recently and data is current:
```bash
python -c "
import duckdb
conn = duckdb.connect('transform/cardstock_dbt/dev.duckdb', read_only=True)
row = conn.execute('SELECT MAX(price_date), COUNT(*) FROM fct_card_price_features').fetchone()
print(f'Latest price_date: {row[0]}  Total rows: {row[1]}')
"
```
If the latest date is more than 2 days old, ask the user if they want to run `dbt run` first.

**Step 2 — Run training**
```bash
python ml/train.py
```
Capture and show all output, including final MAE and RMSE metrics.

**Step 3 — Summarize results**
After training completes, report:
- `mae_dollars` and `rmse_dollars` from this run
- Baseline from last committed run: MAE $4.95, RMSE $15.09
- Whether this run is better, worse, or similar
- Train/test row counts

**Step 4 — Ask about S3 upload**
If metrics improved (MAE or RMSE decreased by >5%), recommend uploading:
```bash
python pipeline/s3.py upload model
```
Ask the user before running this — uploading replaces the production model artifact on S3.

**Reminders:**
- Train cutoff is `2026-03-01` (temporal split, not random)
- Target is log return (`log(next_3m / monthly)`), not absolute price
- RMSE above $15 may be acceptable — it's skewed by ~10 high-value vintage cards
- To view full MLflow history: `mlflow ui` → http://localhost:5000
