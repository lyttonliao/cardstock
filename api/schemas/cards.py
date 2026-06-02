from datetime import date
from typing import Optional
from pydantic import BaseModel


class CardSummary(BaseModel):
    card_id: str
    name: str
    rarity: Optional[str]
    set_id: str
    set_name: str
    variant: str
    set_release_date: Optional[date]
    is_specialty_set: int
    packs_per_specific_card: Optional[float]
    image_small: str
    image_large: str
    tcgplayer_url: str
    launch_price: Optional[float]
    price_running_max: Optional[float]
    current_price: Optional[float]


class CardIndex(BaseModel):
    card_id: str
    name: str
    rarity: Optional[str]
    set_id: str
    set_name: str
    variant: str


class CardListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CardSummary]


class PricePoint(BaseModel):
    price_date: date
    monthly_price: Optional[float]
    daily_price: Optional[float]


class PriceHistoryResponse(BaseModel):
    card_id: str
    name: str
    variant: str
    rarity: Optional[str]
    set_id: str
    set_name: str
    image_small: str
    image_large: str
    prices: list[PricePoint]


class MoverSummary(BaseModel):
    card_id: str
    name: str
    variant: str
    rarity: Optional[str]
    set_id: str
    set_name: str
    current_price: float
    price_change_1m_pct: Optional[float]
    price_change_3m_pct: Optional[float]
    price_change_6m_pct: Optional[float]
    price_change_12m_pct: Optional[float]


class MoversResponse(BaseModel):
    total: int
    items: list[MoverSummary]


class MarketAggregatesResponse(BaseModel):
    total_cards: int
    date: str
    market_cap: float
    market_cap_1m: Optional[float]
    market_cap_3m: Optional[float]
    market_cap_6m: Optional[float]
    market_cap_12m: Optional[float]
    market_cap_5y: Optional[float]
    mae: float
    rmse: float
