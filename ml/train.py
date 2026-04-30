import os
import duckdb
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

conn = duckdb.connect(os.path.join(BASE_DIR, "transform/cardstock_dbt/dev.duckdb"))
df = conn.execute("SELECT * FROM fct_card_price_features").fetchdf()

TARGET = "next_3m_price"

FEATURES = [
    "nm_price", "price_ma_3m", "price_ma_6m", "price_ma_12m",
    "price_stddev_3m", "days_since_release", "price_6m_high", "price_6m_low",
    "stochastic_k_6m", "stochastic_k_3m", "above_ma_3m", "above_ma_6m",
    "price_momentum_3m", "month_of_year",
    "rarity", "variant", "set_id"
]

df = df[df[TARGET].notna()].copy()
print(f"Rows after dropping NULL targets: {len(df)}")

for col in ["rarity", "variant", "set_id"]:
    df[col] = df[col].astype("category")

df["price_date"] = df["price_date"].astype("datetime64[ns]")

cutoff = pd.Timestamp("2025-03-01")
train = df[df["price_date"] < cutoff]
test = df[df["price_date"] >= cutoff]

X_train, y_train = train[FEATURES], train[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]

print(f"Train: {len(train)} rows, Test: {len(test)} rows")

model = xgb.XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    enable_categorical=True,
    random_state=42
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=100
)

preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)
rmse = root_mean_squared_error(y_test, preds)

importances = pd.Series(
    model.feature_importances_,
    index=FEATURES
).sort_values(ascending=False)

results = test[["card_id", "name", "price_date", "nm_price"]].copy()
results["predicted"] = preds
results["actual"] = y_test.values
results["error"] = results["predicted"] - results["actual"]
results["abs_error"] = results["error"].abs()

print("\nWorst predictions (largest errors):")
print(results.nlargest(10, "abs_error")[["name", "price_date", "nm_price", "predicted", "actual", "error"]].to_string())

print("\nSample predictions:")
print(results.sample(10, random_state=42)[["name", "price_date", "nm_price", "predicted", "actual", "error"]].to_string())