from datetime import date
from typing import Optional
from pydantic import BaseModel


class PredictRequest(BaseModel):
    card_id: str
    variant: str
    price_date: Optional[date] = None  # None = use latest available row


class PriceMetrics(BaseModel):
    monthly_price: float            # monthly_price
    daily_price: Optional[float]    # tcgplayer daily price
    launch_price: Optional[float]   # first ever recorded price
    all_time_high: Optional[float]  # price_running_max


class MovingAverages(BaseModel):
    ma_3m: Optional[float]
    ma_6m: Optional[float]
    ma_12m: Optional[float]


class Momentum(BaseModel):
    price_change_1m_pct: Optional[float]
    price_change_3m_pct: Optional[float]
    price_change_6m_pct: Optional[float]
    price_change_12m_pct: Optional[float]
    price_vs_ma_3m: Optional[float]    # (price - ma_3m) / ma_3m
    price_vs_ma_12m: Optional[float]   # (price - ma_12m) / ma_12m
    price_change_since_launch: Optional[float]  # ln(price / launch_price)


class Volatility(BaseModel):
    stddev_3m: Optional[float]          # price_stddev_3m
    cv_3m: Optional[float]              # stddev / price (normalised)
    price_6m_high: Optional[float]
    price_6m_low: Optional[float]
    stochastic_k_6m: Optional[float]    # position within 6m range [0, 1]
    stochastic_k_3m: Optional[float]    # position within 3m range [0, 1]


class TrendRegime(BaseModel):
    above_ma_3m: Optional[bool]
    above_ma_6m: Optional[bool]
    above_ma_12m: Optional[bool]
    months_above_ma_12m: Optional[int]  # count of months above 12m MA in trailing year
    price_ath_ratio: Optional[float]    # price / all_time_high; 1.0 = at ATH
    price_vs_set_index: Optional[float] # price / avg price in set; >1 = chase card


class MarketContext(BaseModel):
    pokemon_interest_score: Optional[float]         # Google Trends 0-100
    days_since_recent_set_release: Optional[int]
    hype_weighted_release_90d: Optional[float]      # avg launch price of sets in trailing 90d
    days_since_release: Optional[int]
    is_specialty_set: bool
    packs_per_specific_card: Optional[float]        # pull rate proxy


class Forecast(BaseModel):
    predicted_3m_price: float
    log_return_3m: float                        # raw model output
    actual_next_1m_price: Optional[float]       # non-null only for historical rows
    actual_next_3m_price: Optional[float]
    actual_next_6m_price: Optional[float]


class PredictResponse(BaseModel):
    card_id: str
    name: str
    variant: str
    rarity: Optional[str]
    set_id: str
    set_name: str
    price_date: date                # actual date the feature row came from
    prices: PriceMetrics
    moving_averages: MovingAverages
    momentum: Momentum
    volatility: Volatility
    trend: TrendRegime
    market_context: MarketContext
    forecast: Forecast


class MoverCardSummary(BaseModel):
    card_id: str
    name: str
    variant: str
    rarity: Optional[str]
    set_id: str
    set_name: str
    monthly_price: float
    log_return_3m: float
    pred_3m: float


class MoversListResponse(BaseModel):
    gainers: list[MoverCardSummary]
    losers: list[MoverCardSummary]
