# ml/ — Claude Context

XGBoost model training and experiment tracking.

## Files

```
train.py           Training pipeline (load → split → train → evaluate → save)
models/xgb_v1.json Trained model artifact (pushed to S3, pulled by API at startup)
mlruns/            MLflow experiment tracking (gitignored)
```

## Target Variable

`return_1m = log(next_1m_price / monthly_price)` — the 1-month log return.

**Why log returns?**
- Scale-invariant: a 2x move on a $10 card and a $500 card have the same log return (`ln(2) ≈ 0.693`)
- Prevents the model from regressing toward high absolute prices
- At inference: `predicted_price = monthly_price * exp(model_output)`

**Log return scale reference:**
- ±0.095 ≈ ±10% price change
- +0.693 ≈ +100% (2x)
- +2.0 ≈ +639% (7.4x) — extreme outlier territory
- -2.0 ≈ -86% — near-zero price

**Never** train on absolute price as the target — the model will learn price levels, not dynamics.

## Train/Test Split

Two cutoffs defined in `api/constants.py`:
- `TRAIN_CUTOFF = "2026-06-01"` — production model trains on all data before this date
- `EVAL_CUTOFF = "2026-03-01"` — walk-forward evaluation trains on data before this, tests on [EVAL_CUTOFF, TRAIN_CUTOFF)

**Two-phase training in `train.py`:**
```python
# Phase 1: evaluation model (smaller train set, but test set has next_1m_price available)
eval_train = df[df["price_date"] < EVAL_CUTOFF]
eval_test  = df[(df["price_date"] >= EVAL_CUTOFF) & (df["price_date"] < TRAIN_CUTOFF)]

# Phase 2: production model (all data before TRAIN_CUTOFF — saved to disk)
prod_train = df[df["price_date"] < TRAIN_CUTOFF]
```

MLflow metrics come from Phase 1 (eval model). The saved `xgb_v1.json` is Phase 2 (production model, more data).

**Never use random splits** — future prices would leak into training data.

## Feature Set

50+ features defined in `api/constants.py::FEATURES`. Categorical features (`rarity`, `variant`, `set_id`) are listed in `CATEGORICAL_FEATURES` and must be cast to `category` dtype before prediction:

```python
X[CATEGORICAL_FEATURES] = X[CATEGORICAL_FEATURES].astype("category")
```

XGBoost uses `enable_categorical=True` — no one-hot encoding needed.

**Top feature: `daily_day_count`** (~35% importance). Count of distinct days in the month that TCGPlayer had market data. It effectively routes the model: cards with 0/null day count are eBay/vintage cards where TCGPlayer market prices are unreliable. XGBoost uses this as a primary split condition to handle the two card populations differently.

**Null handling:** Features like `daily_price_stddev`, `daily_range_pct`, `daily_intramonth_return`, and all `pokemon_*` cross-species features are NULL for pre-2026 rows or non-Pokemon cards (Trainers, Energy). XGBoost routes NULL values via built-in missing-value splits — no imputation needed.

## Model Configuration

```python
XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    enable_categorical=True,
)
```

The model is saved as JSON (`xgb_v1.json`) — portable format, version-controlled in S3.

## MLflow Tracking

Every `train.py` run logs:
- Hyperparameters (n_estimators, learning_rate, max_depth)
- Row counts (train_rows, test_rows)
- Dollar-space metrics: `mae_dollars`, `rmse_dollars` (converted from log-return predictions back to prices)
- Model artifact

```bash
mlflow ui   # view experiments at http://localhost:5000
```

## Current Model Metrics (walk-forward eval on [EVAL_CUTOFF, TRAIN_CUTOFF))

- MAE: $10.83
- RMSE: $46.45

RMSE is heavily skewed by high-value vintage cards (Umbreon, Lugia, Lucky Stadium) that had sharp price regime changes. For cards under $200, performance is substantially better. Also reflected in `api/constants.py::MODEL_MAE_DOLLARS` and `MODEL_RMSE_DOLLARS`.

## Retraining Checklist

1. Run `dbt run` to refresh `fct_card_price_features` with latest data
2. Run `python ml/train.py`
3. Check MLflow metrics — compare MAE/RMSE against previous run
4. Update `MODEL_MAE_DOLLARS` and `MODEL_RMSE_DOLLARS` in `api/constants.py`
5. Upload new model: `python pipeline/s3.py upload model`
6. Redeploy API (or restart ECS task) to pick up the new model from S3
