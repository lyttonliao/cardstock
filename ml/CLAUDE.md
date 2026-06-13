# ml/ — Claude Context

XGBoost model training and experiment tracking.

## Files

```
train.py           Training pipeline (load → split → train → evaluate → save)
models/xgb_v1.json Trained model artifact (pushed to S3, pulled by API at startup)
mlruns/            MLflow experiment tracking (gitignored)
```

## Target Variable

`return_3m = log(next_3m_price / monthly_price)` — the 3-month log return.

**Why log returns?**
- Scale-invariant: a 2x move on a $10 card and a $500 card have the same log return (`ln(2) ≈ 0.693`)
- Prevents the model from regressing toward high absolute prices
- At inference: `predicted_price = monthly_price * exp(model_output)`

**Never** train on absolute price as the target — the model will learn price levels, not dynamics.

## Train/Test Split

Temporal cutoff: `TRAIN_CUTOFF = "2026-03-01"` (defined in `api/constants.py`, imported here).

```python
train = df[df["price_date"] < TRAIN_CUTOFF]
test  = df[df["price_date"] >= TRAIN_CUTOFF]
```

**Never use random splits** — future prices would leak into training data, producing falsely optimistic metrics. All evaluation must be on dates strictly after the cutoff.

## Feature Set

41 features defined in `api/constants.py::FEATURES`. Categorical features (`rarity`, `variant`, `set_id`) are listed in `CATEGORICAL_FEATURES` and must be cast to `category` dtype before prediction:

```python
X[CATEGORICAL_FEATURES] = X[CATEGORICAL_FEATURES].astype("category")
```

XGBoost uses `enable_categorical=True` — no one-hot encoding needed.

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

## Retraining Checklist

1. Run `dbt run` to refresh `fct_card_price_features` with latest data
2. Run `python ml/train.py`
3. Check MLflow metrics — compare MAE/RMSE against previous run
4. If metrics improve, upload new model: `python pipeline/s3.py upload model`
5. Redeploy API (or restart ECS task) to pick up the new model from S3

## Evaluation Notes

- RMSE ($15.09) is skewed by ~10 high-value vintage cards (Umbreon, Lugia, Lucky Stadium) that had sharp price regime changes in early 2026
- For cards under $200, performance is substantially better
- Consider per-rarity or per-price-tier breakdowns when evaluating new features
