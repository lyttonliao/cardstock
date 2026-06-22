---
description: Validate Cardstock data quality — check Parquet file freshness, DuckDB row counts, null rates in key features, and schema completeness against the 41-feature list.
---

Run a full data quality validation across the Cardstock pipeline. Execute all checks and report results.

**Check 1 — DuckDB freshness and size**
```bash
python -c "
import duckdb
conn = duckdb.connect('transform/cardstock_dbt/dev.duckdb', read_only=True)
row = conn.execute('''
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT card_id) AS distinct_cards,
        COUNT(DISTINCT card_id || chr(124) || variant) AS distinct_card_variants,
        MAX(price_date) AS latest_date,
        MIN(price_date) AS earliest_date
    FROM fct_card_price_features
''').fetchone()
print(f'Rows: {row[0]:,}')
print(f'Distinct cards: {row[1]:,}')
print(f'Distinct card+variant combos: {row[2]:,}')
print(f'Date range: {row[4]} → {row[3]}')
"
```

**Check 2 — NULL rates in key features**
```bash
python -c "
import duckdb
conn = duckdb.connect('transform/cardstock_dbt/dev.duckdb', read_only=True)
rows = conn.execute('''
    SELECT
        COUNT(*) FILTER (WHERE monthly_price IS NULL) AS null_monthly_price,
        COUNT(*) FILTER (WHERE price_3m_ago IS NULL)  AS null_3m_ago,
        COUNT(*) FILTER (WHERE rarity IS NULL)        AS null_rarity,
        COUNT(*) FILTER (WHERE set_id IS NULL)        AS null_set_id,
        COUNT(*) AS total
    FROM fct_card_price_features
''').fetchone()
print(f'null monthly_price: {rows[0]} / {rows[4]}')
print(f'null price_3m_ago:  {rows[1]} / {rows[4]}')
print(f'null rarity:        {rows[2]} / {rows[4]}')
print(f'null set_id:        {rows[3]} / {rows[4]}')
"
```

**Check 3 — Feature schema completeness**
```bash
python -c "
import sys; sys.path.insert(0, '.')
from api.constants import FEATURES
import duckdb
conn = duckdb.connect('transform/cardstock_dbt/dev.duckdb', read_only=True)
cols = {r[0] for r in conn.execute('DESCRIBE fct_card_price_features').fetchall()}
missing = [f for f in FEATURES if f not in cols]
if missing:
    print('MISSING features:', missing)
else:
    print(f'All {len(FEATURES)} features present')
"
```

**Check 4 — Parquet file freshness**
```bash
python -c "
import os, datetime
files = {
    'registry':      'data/registry/card_registry.parquet',
    'daily_prices':  'data/prices/daily_price_history.parquet',
    'price_history': 'data/prices/price_history.parquet',
    'trends':        'data/trends/google_trends.parquet',
}
for name, path in files.items():
    if os.path.exists(path):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        size_mb = os.path.getsize(path) / 1e6
        print(f'{name}: modified {mtime:%Y-%m-%d %H:%M}, {size_mb:.1f} MB')
    else:
        print(f'{name}: FILE MISSING at {path}')
"
```

After running all checks, summarize:
- Overall data health (fresh / stale / missing)
- Any anomalies that need attention
- Recommended next action (re-run ingestion, dbt, etc.)
