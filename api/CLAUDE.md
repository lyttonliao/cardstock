# api/ — Claude Context

FastAPI application. DuckDB is read-only; XGBoost model is loaded once at startup.

## Structure

```
main.py           App factory, lifespan, CORS, /health
dependencies.py   get_cursor() and get_model() — inject into routes
constants.py      DB_PATH, MODEL_PATH, feature list, TRAIN_CUTOFF
routers/
  cards.py        /cards, /cards/{id}/prices, /cards/market_aggregates, /cards/movers
  predict.py      POST /predict, GET /predict/movers
  sets.py         GET /sets
  model.py        GET /model/info
schemas/
  cards.py        Pydantic response models for card endpoints
  predict.py      PredictRequest, PredictResponse (with nested models)
  sets.py         SetSummary, SetListResponse
  model.py        ModelInfoResponse
```

## Startup Pattern

```python
# main.py lifespan
conn = duckdb.connect(DB_PATH, read_only=True)   # shared, thread-safe reads
xgb_model = xgb.XGBRegressor()
xgb_model.load_model(MODEL_PATH)
set_db_conn(conn)
set_model(xgb_model)
```

Use `get_cursor()` (yields a cursor per request) and `get_model()` in route handlers:

```python
@router.get("/cards")
def list_cards(cursor=Depends(get_cursor), model=Depends(get_model)):
    ...
```

## DuckDB Conventions

- Always query `fct_card_price_features` for price/feature data.
- Card registry metadata comes from `card_registry.parquet` (via `REGISTRY_PATH`).
- To deduplicate to the latest row per card+variant, use:
  ```sql
  QUALIFY ROW_NUMBER() OVER (PARTITION BY card_id, variant ORDER BY price_date DESC) = 1
  ```
- NULL guard before arithmetic: if a column like `price_3m_ago` can be NULL, add `WHERE price_3m_ago IS NOT NULL` before dividing.
- Return pandas → `.itertuples()` to build Pydantic models; `rows.nlargest(10, col)` / `rows.nsmallest(10, col)` for top-N movers.

## Inference Pattern

```python
# predict.py
features_df = pd.DataFrame([row_dict])[FEATURES]  # FEATURES from constants.py
features_df[CATEGORICAL_FEATURES] = features_df[CATEGORICAL_FEATURES].astype("category")
log_return = float(model.predict(features_df)[0])
predicted_price = round(monthly_price * np.exp(log_return), 2)
```

`FEATURES` (41 total) and `CATEGORICAL_FEATURES` are defined in `constants.py`. Column order must match — always index with `FEATURES` list before predicting.

## Schemas

- Nested Pydantic models are used for the prediction response (`PredictResponse`). It has sub-objects: `prices`, `moving_averages`, `momentum`, `volatility`, `trend`, `market_context`, `forecast`.
- `MoverCardSummary` in `schemas/predict.py` includes `pred_3m: float` (the predicted dollar price, not the log return).
- For the cards movers endpoint, use `MoverCardSummary` from `schemas/cards.py` (no prediction fields).

## Error Handling

- Raise `HTTPException(status_code=404, detail="...")` for missing cards/data.
- Return `None` fields rather than raising for optional data (e.g., if a prediction feature is missing).
- The `/predict` endpoint returns a prediction even if some context features are null — the model handles missing data via XGBoost's categorical support.
