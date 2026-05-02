import duckdb
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# conn = duckdb.connect(os.path.join(BASE_DIR, "transform/cardstock_dbt/dev.duckdb"))
# res = conn.execute("""
#     SELECT card_id, name, price_date, nm_price, next_3m_price, variant
#     FROM fct_card_price_features
#     WHERE name ILIKE '%Mewtwo%' AND set_name ILIKE '%Destined%'
# """).fetchdf()
# print(res.to_string())

# res = conn.execute("""
#     SELECT card_id, name
#     FROM fct_card_price_features
#     WHERE name ILIKE '%Aqua%' AND set_name ILIKE '%Team Aqua%'                
# """).fetchdf()
# print(res.to_string())

# import requests, re, json
# url = "https://www.pricecharting.com/game/pokemon-diamond-&-pearl/munchlax-33"
# resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
# match = re.search(r'VGPC\.chart_data\s*=\s*(\{.*?\});', resp.text, re.DOTALL)
# if match:
#     data = json.loads(match.group(1))
#     print("new entries:", len(data.get("new", [])))
#     print("used entries:", len(data.get("used", [])))

conn = duckdb.connect()

# print(conn.execute("SELECT * FROM '../data/registry/card_registry.parquet' WHERE id = 'dp1-33'").fetchdf())
# print(conn.execute("SELECT variant, count(*) FROM '../data/registry/card_registry.parquet' GROUP BY variant ORDER BY count(*) DESC").fetchdf()
# )

conn.execute("""
COPY (
    SELECT 
        card_id AS id,
        * EXCLUDE (card_id)
    FROM read_parquet('../data/prices/daily_price_history.parquet')
)
TO '../data/prices/daily_price_history_updated.parquet' (FORMAT PARQUET)
""")