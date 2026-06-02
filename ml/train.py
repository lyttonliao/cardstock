import os
import duckdb
import mlflow
import pandas as pd
import xgboost as xgb
import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

conn = duckdb.connect(os.path.join(BASE_DIR, "transform/cardstock_dbt/dev.duckdb"))
df = conn.execute("SELECT * FROM fct_card_price_features").fetchdf()

# Predict 3-month log return; convert back to dollars at inference time.
# Log return is scale-invariant — a $10 card rising 20% looks the same as a $1000 card
# rising 20%, so the model learns price movement patterns rather than absolute price levels.
df["return_3m"] = np.log(df["next_3m_price"] / df["monthly_price"])
df["return_3m"] = df["return_3m"].replace([np.inf, -np.inf], np.nan)

TARGET = "return_3m"

FEATURES = [
    # Price levels
    "monthly_price", "daily_price",
    # Moving averages
    "price_ma_3m", "price_ma_6m", "price_ma_12m",
    # Volatility
    "price_stddev_3m",
    # Range features
    "price_6m_high", "price_6m_low",
    # Oscillators
    "stochastic_k_6m", "stochastic_k_3m",
    # Trailing returns (point-to-point)
    "price_change_1m_pct", "price_change_3m_pct", "price_change_6m_pct", "price_change_12m_pct",
    "price_change_since_launch",
    # MA deviations — magnitude of distance from rolling average (complements above_ma_* booleans)
    "price_vs_ma_3m", "price_vs_ma_6m", "price_vs_ma_12m",
    # Volatility (normalised) and price position
    "price_cv_3m", "price_ath_ratio", "price_vs_set_index",
    # Trend regime
    "above_ma_3m", "above_ma_6m", "above_ma_12m", "months_above_ma_12m",
    # Card fundamentals
    "days_since_release", "is_specialty_set", "packs_per_specific_card",
    # Market macro signals
    "days_since_recent_set_release", "hype_weighted_release_90d",
    "pokemon_interest_score",
    # Calendar
    "month_of_year",
    # Categorical
    "rarity", "variant", "set_id",
]

PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 6,
    "random_state": 42,
}

df = df[df[TARGET].notna()].copy()
print(f"Rows after dropping NULL targets: {len(df)}")

for col in ["rarity", "variant", "set_id"]:
    df[col] = df[col].astype("category")

df["price_date"] = df["price_date"].astype("datetime64[ns]")

cutoff = pd.Timestamp("2026-03-01")
train = df[df["price_date"] < cutoff]
test = df[df["price_date"] >= cutoff]

X_train, y_train = train[FEATURES], train[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]

print(f"Train: {len(train)} rows, Test: {len(test)} rows")

mlflow.set_tracking_uri(os.path.join(BASE_DIR, "ml", "mlruns"))
mlflow.set_experiment("cardstock-price-prediction")

with mlflow.start_run() as run:
    mlflow.log_params(PARAMS)
    mlflow.log_param("train_cutoff", str(cutoff.date()))
    mlflow.log_param("target", TARGET)
    mlflow.log_param("n_features", len(FEATURES))

    model = xgb.XGBRegressor(
        enable_categorical=True,
        **PARAMS
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=100
    )

    log_return_preds = model.predict(X_test)
    preds = test["monthly_price"].to_numpy() * np.exp(log_return_preds)
    y_test_dollars = test["next_3m_price"].to_numpy()
    mae = mean_absolute_error(y_test_dollars, preds)
    rmse = root_mean_squared_error(y_test_dollars, preds)

    mlflow.log_metric("mae_dollars", mae)
    mlflow.log_metric("rmse_dollars", rmse)
    mlflow.log_metric("train_rows", len(train))
    mlflow.log_metric("test_rows", len(test))

    model_path = os.path.join(BASE_DIR, "ml", "models", "xgb_v1.json")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save_model(model_path)
    mlflow.log_artifact(model_path, artifact_path="model")

    importances = pd.Series(
        model.feature_importances_,
        index=FEATURES
    ).sort_values(ascending=False)

    print(f"\nMAE:  ${mae:.2f}")
    print(f"RMSE: ${rmse:.2f}")
    print("\nFeature importances:")
    print(importances.to_string())

    results = test[["card_id", "name", "price_date", "monthly_price"]].copy()
    results["predicted"] = preds
    results["actual"] = y_test_dollars
    results["error"] = results["predicted"] - results["actual"]
    results["abs_error"] = results["error"].abs()

    print("\nWorst predictions (largest errors):")
    print(results.nlargest(10, "abs_error")[["name", "price_date", "monthly_price", "predicted", "actual", "error"]].to_string())

    print("\nSample predictions:")
    print(results.sample(10, random_state=42)[["name", "price_date", "monthly_price", "predicted", "actual", "error"]].to_string())

    print(f"\nMLflow run_id: {run.info.run_id}")
    print(f"Model saved to: {model_path}")
