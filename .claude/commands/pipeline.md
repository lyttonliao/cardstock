---
description: Run the full Cardstock daily or monthly data pipeline end-to-end, including S3 sync, ingestion, dbt, and upload.
---

You are running the Cardstock data pipeline. First, ask the user which pipeline to run:

- **Daily** (`python pipeline/daily.py`) — ingestion + dbt + S3 sync
- **Monthly** (`python pipeline/monthly.py`) — includes Google Trends + may trigger retraining

**Before running, check prerequisites:**
```bash
# Verify AWS env vars are set (required for S3 steps)
python -c "
import os
keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET']
for k in keys:
    status = 'SET' if os.environ.get(k) else 'MISSING'
    print(f'{k}: {status}')
"
```
If S3 vars are missing, the pipeline still runs but S3 download/upload are no-ops (safe for local dev with existing data files).

**Daily pipeline step order:**
```
1. download(["registry", "duckdb", "model"])    ← S3 pull
2. python ingestion/update_card_registry.py
3. python ingestion/tcgplayer_daily_prices.py
4. cd transform/cardstock_dbt && dbt run
5. upload(["registry", "daily_prices", "duckdb"]) ← S3 push
```

Run the chosen pipeline and monitor output. A failure in any step stops the pipeline (`check=True`). Report:
- Which step failed (if any)
- The error message
- Whether the step is safe to retry
- Suggested fix

After a successful daily run, the updated DuckDB and registry are on S3 and the API will pick them up on its next startup or ECS task restart.
