from datetime import date
from typing import Annotated, Optional

import pandas as pd
import numpy as np
import duckdb
import xgboost as xgb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.constants import FEATURES, CATEGORICAL_FEATURES
from api.dependencies import get_cursor, get_model
from api.schemas.predict import (
    PredictRequest,
    PredictResponse,
    PriceMetrics,
    Momentum,
    MovingAverages,
    MarketContext,
    Volatility,
    TrendRegime,
    Forecast,
)

router = APIRouter(prefix="/predict", tags=["predict"])

EXTRA_COLS = ["launch_price", "price_running_max", "next_1m_price", "next_3m_price", "next_6m_price"]

@router.post("", response_model=PredictResponse)
def get_prediction(
    body: PredictRequest,
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)],
    model: Annotated[xgb.XGBRegressor, Depends(get_model)],
):
    select_cols = ", ".join(FEATURES + EXTRA_COLS)
    conditions = ["card_id = ?", "variant = ?"]
    params: list = [body.card_id, body.variant]

    if body.price_date is not None:
        conditions.append("price_date <= ?")
        params.append(body.price_date)

    card_sql = f"""
        SELECT card_id, name, rarity, set_id, set_name, variant, price_date,
            {select_cols}
        FROM fct_card_price_features
        WHERE {" AND ".join(conditions)}
        ORDER BY price_date DESC
        LIMIT 1
    """
    rows = cursor.execute(card_sql, params).fetchdf()
    if rows.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for card {body.card_id} with variant {body.variant}"
        )

    r = rows.iloc[0]

    X = rows[FEATURES].copy()
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].astype("category")
    log_return = float(model.predict(X)[0])
    monthly_price = float(r["monthly_price"])
    predicted_3m = round(monthly_price * np.exp(log_return), 2)

    def opt(val):
        return None if pd.isna(val) else val

    return PredictResponse(
        card_id=r["card_id"],
        name=r["name"],
        variant=r["variant"],
        rarity=opt(r["rarity"]),
        set_id=r["set_id"],
        set_name=r["set_name"],
        price_date=r["price_date"],
        prices=PriceMetrics(
            monthly_price=monthly_price,
            daily_price=opt(r["daily_price"]),
            launch_price=opt(r["launch_price"]),
            all_time_high=opt(r["price_running_max"]),
        ),
        moving_averages=MovingAverages(
            ma_3m=opt(r["price_ma_3m"]),
            ma_6m=opt(r["price_ma_6m"]),
            ma_12m=opt(r["price_ma_12m"]),
        ),
        momentum=Momentum(
            price_momentum_3m=opt(r["price_momentum_3m"]),
            price_change_3m_pct=opt(r["price_change_3m_pct"]),
            price_change_12m_pct=opt(r["price_change_12m_pct"]),
            price_change_since_launch=opt(r["price_change_since_launch"]),
        ),
        volatility=Volatility(
            stddev_3m=opt(r["price_stddev_3m"]),
            cv_3m=opt(r["price_cv_3m"]),
            price_6m_high=opt(r["price_6m_high"]),
            price_6m_low=opt(r["price_6m_low"]),
            stochastic_k_6m=opt(r["stochastic_k_6m"]),
            stochastic_k_3m=opt(r["stochastic_k_3m"]),
        ),
        trend=TrendRegime(
            above_ma_3m=opt(r["above_ma_3m"]),
            above_ma_6m=opt(r["above_ma_6m"]),
            above_ma_12m=opt(r["above_ma_12m"]),
            months_above_ma_12m=opt(r["months_above_ma_12m"]),
            price_ath_ratio=opt(r["price_ath_ratio"]),
            price_vs_set_index=opt(r["price_vs_set_index"]),
        ),
        market_context=MarketContext(
            pokemon_interest_score=opt(r["pokemon_interest_score"]),
            days_since_recent_set_release=opt(r["days_since_recent_set_release"]),
            hype_weighted_release_90d=opt(r["hype_weighted_release_90d"]),
            days_since_release=opt(r["days_since_release"]),
            is_specialty_set=bool(r["is_specialty_set"]),
            packs_per_specific_card=opt(r["packs_per_specific_card"]),
        ),
        forecast=Forecast(
            predicted_3m_price=predicted_3m,
            log_return_3m=round(log_return, 6),
            actual_next_1m_price=opt(r["next_1m_price"]),
            actual_next_3m_price=opt(r["next_3m_price"]),
            actual_next_6m_price=opt(r["next_6m_price"]),
        ),
    )
