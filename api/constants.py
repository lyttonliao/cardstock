import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "transform", "cardstock_dbt", "dev.duckdb")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "xgb_v1.json")
REGISTRY_PATH = os.path.join(BASE_DIR, "data", "registry", "card_registry.parquet")

MODEL_VERSION = "xgb_v1"
TRAIN_CUTOFF = "2026-03-01"

# Must match ml/train.py FEATURES list exactly — order matters for XGBoost
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
    # Momentum / velocity
    "price_momentum_3m", "price_change_3m_pct", "price_change_12m_pct",
    "price_change_since_launch",
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
    # Categorical (XGBoost enable_categorical=True)
    "rarity", "variant", "set_id",
]

CATEGORICAL_FEATURES = ["rarity", "variant", "set_id"]

MODEL_PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 6,
    "random_state": 42,
}

# Metrics from the last training run (March 2026 holdout)
MODEL_MAE_DOLLARS = 4.92
MODEL_RMSE_DOLLARS = 15.12
