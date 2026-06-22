---
description: Run dbt transformations to rebuild fct_card_price_features, then report model results and row counts.
---

Run the Cardstock dbt transformation pipeline from the dbt project directory:

```bash
cd transform/cardstock_dbt && dbt run
```

After the run completes, report:
1. Which models succeeded and which (if any) failed
2. Total run duration
3. On success — verify output with a quick row count:

```bash
python -c "
import duckdb
conn = duckdb.connect('transform/cardstock_dbt/dev.duckdb', read_only=True)
row = conn.execute('SELECT COUNT(*) AS rows, MAX(price_date) AS latest FROM fct_card_price_features').fetchone()
print(f'fct_card_price_features: {row[0]:,} rows, latest price_date: {row[1]}')
"
```

**On failure:**
- Show the full dbt error output
- Check `transform/cardstock_dbt/logs/dbt.log` for details
- Common causes:
  - Missing upstream Parquet files (run ingestion first)
  - Schema mismatch in a staging model
  - DuckDB file locked (another process has it open in write mode)

**Model execution order:**
```
staging/         stg_card_registry, stg_daily_price_history, stg_price_history, stg_google_trends
intermediate/    int_card_daily_prices, int_set_price_index, int_set_release_features
marts/           fct_card_price_features
```

To run a specific model and its dependencies: `dbt run --select +fct_card_price_features`
