import os
import sys
import duckdb
import mlflow
import pandas as pd
import xgboost as xgb
import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from api.constants import FEATURES, CATEGORICAL_FEATURES, TRAIN_CUTOFF, EVAL_CUTOFF

conn = duckdb.connect(os.path.join(BASE_DIR, "transform/cardstock_dbt/dev.duckdb"))
df_raw = conn.execute("SELECT * FROM fct_card_price_features").fetchdf()
df_raw["price_date"] = df_raw["price_date"].astype("datetime64[ns]")

cutoff = pd.Timestamp(TRAIN_CUTOFF)
eval_cutoff = pd.Timestamp(EVAL_CUTOFF)

PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 6,
    "random_state": 42,
}

# Compute log returns for both horizons up front.
# Log return is scale-invariant — a 20% move looks identical on a $5 card and a $500 card.
df_raw["return_1m"] = np.log(df_raw["next_1m_price"] / df_raw["monthly_price"].clip(lower=0.01))
df_raw["return_1m"] = df_raw["return_1m"].replace([np.inf, -np.inf], np.nan)

df_raw["return_3m"] = np.log(df_raw["next_3m_price"] / df_raw["monthly_price"].clip(lower=0.01))
df_raw["return_3m"] = df_raw["return_3m"].replace([np.inf, -np.inf], np.nan)

mlflow.set_tracking_uri(os.path.join(BASE_DIR, "ml", "mlruns"))
mlflow.set_experiment("cardstock-price-prediction")

with mlflow.start_run() as run:
    mlflow.log_params(PARAMS)
    mlflow.log_param("train_cutoff", str(cutoff.date()))
    mlflow.log_param("eval_cutoff", str(eval_cutoff.date()))
    mlflow.log_param("n_features", len(FEATURES))
    mlflow.log_param("target", "return_1m")

    # ── Walk-forward evaluation ─────────────────────────────────────────────
    # Eval model trains on price_date < EVAL_CUTOFF, validates on
    # [EVAL_CUTOFF, TRAIN_CUTOFF) — rows we now have ground truth for.
    # This is the only honest out-of-sample split available right now.

    df_eval = df_raw[df_raw["return_1m"].notna()].copy()
    for col in CATEGORICAL_FEATURES:
        df_eval[col] = df_eval[col].astype("category")

    train_eval = df_eval[df_eval["price_date"] < eval_cutoff]
    val = df_eval[
        (df_eval["price_date"] >= eval_cutoff) &
        (df_eval["price_date"] < cutoff)
    ]

    print(f"\n── Walk-forward evaluation (1m return target) ──────────────────────")
    print(f"  Eval train: {len(train_eval):,} rows  (price_date < {EVAL_CUTOFF})")
    print(f"  Validation: {len(val):,} rows  ({EVAL_CUTOFF} – {TRAIN_CUTOFF})")

    mlflow.log_metric("eval_train_rows", len(train_eval))
    mlflow.log_metric("eval_val_rows", len(val))

    if len(train_eval) > 0 and len(val) > 0:
        eval_model = xgb.XGBRegressor(enable_categorical=True, **PARAMS)
        eval_model.fit(
            train_eval[FEATURES], train_eval["return_1m"],
            eval_set=[(val[FEATURES], val["return_1m"])],
            verbose=100,
        )

        log_preds_eval = eval_model.predict(val[FEATURES])
        preds_eval_dollars = val["monthly_price"].to_numpy() * np.exp(log_preds_eval)
        actuals_eval_dollars = val["next_1m_price"].to_numpy()

        mae_eval = mean_absolute_error(actuals_eval_dollars, preds_eval_dollars)
        rmse_eval = root_mean_squared_error(actuals_eval_dollars, preds_eval_dollars)

        mlflow.log_metric("eval_mae_1m_dollars", mae_eval)
        mlflow.log_metric("eval_rmse_1m_dollars", rmse_eval)

        print(f"\n  MAE  (1m, out-of-sample): ${mae_eval:.2f}")
        print(f"  RMSE (1m, out-of-sample): ${rmse_eval:.2f}")

        results_eval = val[["card_id", "name", "price_date", "monthly_price"]].copy()
        results_eval["predicted"] = preds_eval_dollars
        results_eval["actual"] = actuals_eval_dollars
        results_eval["error"] = results_eval["predicted"] - results_eval["actual"]
        results_eval["abs_error"] = results_eval["error"].abs()

        print("\n  Worst predictions (largest errors):")
        print(results_eval.nlargest(10, "abs_error")[
            ["name", "price_date", "monthly_price", "predicted", "actual", "error"]
        ].to_string(index=False))

        print("\n  Sample predictions:")
        print(results_eval.sample(min(10, len(results_eval)), random_state=42)[
            ["name", "price_date", "monthly_price", "predicted", "actual", "error"]
        ].to_string(index=False))
    else:
        print("  Skipping: insufficient data for walk-forward eval.")

    # ── Production model ────────────────────────────────────────────────────
    # Target: return_1m = log(next_1m_price / monthly_price)
    #
    # Rows where next_1m_price is null (typically the most recent month, since
    # next month's price hasn't been scraped yet) are dropped automatically.
    # As of June 2026 this means May 2026 rows are excluded from training —
    # they become the inference input: predict June prices from May features.
    #
    # Train cutoff gates out data we intentionally don't want to train on yet
    # (e.g., future months once they get scraped).

    df_prod = df_raw[
        df_raw["return_1m"].notna() &
        (df_raw["price_date"] < cutoff)
    ].copy()

    for col in CATEGORICAL_FEATURES:
        df_prod[col] = df_prod[col].astype("category")

    print(f"\n── Production model (1m return target) ──────────────────────────────")
    print(f"  Training rows: {len(df_prod):,}  (price_date < {TRAIN_CUTOFF}, next_1m_price known)")

    mlflow.log_metric("train_rows", len(df_prod))

    model = xgb.XGBRegressor(enable_categorical=True, **PARAMS)
    model.fit(df_prod[FEATURES], df_prod["return_1m"], verbose=100)

    model_path = os.path.join(BASE_DIR, "ml", "models", "xgb_v1.json")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save_model(model_path)
    mlflow.log_artifact(model_path, artifact_path="model")

    importances = pd.Series(
        model.feature_importances_,
        index=FEATURES,
    ).sort_values(ascending=False)

    print("\nFeature importances:")
    print(importances.to_string())

    print(f"\nMLflow run_id: {run.info.run_id}")
    print(f"Model saved to: {model_path}")
