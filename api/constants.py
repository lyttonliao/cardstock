import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "transform", "cardstock_dbt", "dev.duckdb")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "xgb_v1.json")
REGISTRY_PATH = os.path.join(BASE_DIR, "data", "registry", "card_registry.parquet")

# Model predicts log(next_1m_price / monthly_price); convert at inference: monthly_price * exp(prediction)
MODEL_VERSION = "xgb_v1"
TRAIN_CUTOFF = "2026-06-01"
# Walk-forward evaluation boundary: eval model trains on < EVAL_CUTOFF,
# validates on [EVAL_CUTOFF, TRAIN_CUTOFF) using next_1m_price as the target.
# March–May 2026 rows have next_1m_price available and are the first months
# with daily intra-month features, making this window the most informative eval split.
EVAL_CUTOFF = "2026-03-01"

# Must match dbt mart output exactly — order matters for XGBoost
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
    # MA deviations
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
    # Daily intra-month structure (NULL for pre-2026 rows; XGBoost handles NULLs natively)
    "daily_day_count",          # distinct days of TCGPlayer data in the month; 0/NULL = eBay/vintage card
    "daily_price_stddev",       # stddev of TCGPlayer daily prices within the month
    "daily_range_pct",          # (high - low) / avg for the month
    "daily_intramonth_return",  # (last daily price - first daily price) / first
    # Cross-Pokémon species features (NULL if pokedex_number missing)
    "pokemon_num_cards",            # tracked card variants for this Pokémon species
    "pokemon_avg_price",            # avg monthly price across all cards of the species
    "pokemon_max_price",            # most expensive card of this Pokémon (flagship)
    "pokemon_avg_price_change_3m",  # avg 3m price change across same-species cards
    "price_vs_pokemon_avg",         # this card's price / species avg  (>1 = chase card)
    "price_vs_pokemon_max",         # this card's price / flagship price (1.0 = IS the flagship)
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

# Metrics from walk-forward eval (EVAL_CUTOFF holdout, 1m target).
# Update after retraining.
MODEL_MAE_DOLLARS = 10.83
MODEL_RMSE_DOLLARS = 46.45
