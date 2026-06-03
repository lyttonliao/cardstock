from datetime import date
from typing import Annotated, Optional

import pandas as pd
import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.constants import REGISTRY_PATH, MODEL_MAE_DOLLARS, MODEL_RMSE_DOLLARS
from api.dependencies import get_cursor
from api.schemas.cards import CardListResponse, CardSummary, PriceHistoryResponse, PricePoint, MarketAggregatesResponse, MoversListResponse, MoverCardSummary


router = APIRouter(prefix="/cards", tags=["cards"])

@router.get("", response_model=CardListResponse)
def get_cards_list(
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)],
    name: Optional[str] = Query(None, description="Fuzzy name search"),
    set_id: Optional[str] = Query(None),
    rarity: Optional[str] = Query(None),
    variant: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    conditions = ["1=1"]
    params: list = []

    if name:
        conditions.append("r.name ILIKE ?")
        params.append(f"%{name}%")
    if set_id:
        conditions.append("r.set_id = ?")
        params.append(set_id)
    if variant:
        conditions.append("COALESCE(r.variant, 'normal') = ?")
        params.append(variant)
    if rarity:
        conditions.append("r.rarity = ?")
        params.append(rarity)
    
    where = (" AND ").join(conditions)
    offset = (page - 1) * page_size

    count_sql = f"""
        SELECT COUNT(*)
        FROM read_parquet('{REGISTRY_PATH}') r
        WHERE {where}
    """
    result = cursor.execute(count_sql, params).fetchone()
    total = result[0] if result is not None else 0

    if min_price:
        conditions.append("f.daily_price >= ?")
        params.append(min_price)
    if max_price:
        conditions.append("f.daily_price <= ?")
        params.append(max_price)

    where = (" AND ").join(conditions) # recompute - includes price conditions

    items_sql = f"""
        SELECT 
            r.id as card_id,
            r.name,
            r.rarity,
            r.set_id,
            r.set_name,
            r.set_release_date,
            COALESCE(r.variant, 'normal') as variant,
            r.is_specialty_set,
            r.packs_per_specific_card,
            r.image_small,
            r.image_large,
            r.tcgplayer_url,
            f.launch_price,
            f.price_running_max,
            f.monthly_price,
            f.daily_price
        FROM read_parquet('{REGISTRY_PATH}') r
        LEFT JOIN (
            SELECT card_id, variant, launch_price, price_running_max, monthly_price, daily_price
            FROM fct_card_price_features
            QUALIFY ROW_NUMBER() OVER (
                PARTITION BY card_id, variant ORDER BY price_date DESC
            ) = 1
        ) f ON r.id = f.card_id AND COALESCE(r.variant, 'normal') = f.variant
        WHERE {where}
        ORDER BY r.name, r.variant
        LIMIT ? OFFSET ?
    """
    rows = cursor.execute(items_sql, params + [page_size, offset]).fetchdf()

    items = [
        CardSummary(
            card_id = row["card_id"],
            name=row["name"],
            rarity=row["rarity"] if pd.notna(row["rarity"]) else None,
            set_id=row["set_id"],
            set_name=row["set_name"],
            variant=row["variant"],
            set_release_date=pd.to_datetime(row["set_release_date"]).date() if pd.notna(row["set_release_date"]) else None,
            is_specialty_set=int(row["is_specialty_set"]),
            packs_per_specific_card=row["packs_per_specific_card"] if pd.notna(row["packs_per_specific_card"]) else None,
            image_small=row["image_small"],
            image_large=row["image_large"],
            tcgplayer_url=row["tcgplayer_url"],
            launch_price=row["launch_price"] if pd.notna(row["launch_price"]) else None,
            price_running_max=row["price_running_max"] if pd.notna(row["price_running_max"]) else None,
            current_price=row["daily_price"] if pd.notna(row["daily_price"]) else row["monthly_price"] if pd.notna(row["monthly_price"]) else None
        ) for _, row in rows.iterrows()
    ]

    return CardListResponse(total=total, page=page, page_size=page_size, items=items)

@router.get("/{card_id}/variants")
def get_card_variants(
    card_id: str,
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)],
):
    sql = f"""
        SELECT DISTINCT COALESCE(variant, 'normal') as variant
        FROM read_parquet('{REGISTRY_PATH}')
        WHERE id = ?
        ORDER BY variant
    """
    rows = cursor.execute(sql, [card_id]).fetchdf()
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Card '{card_id}' not found")
    return {"card_id": card_id, "variants": rows["variant"].tolist()}


@router.get("/{card_id}/prices", response_model=PriceHistoryResponse)
def get_price_history(
    card_id: str,
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)],
    variant: str = Query(..., description="Card variant (e.g. holofoil, normal, reverseHolofoil)"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
):
    meta_sql = f"""
        SELECT id AS card_id, name, rarity, set_id, set_name,
            COALESCE(variant, 'normal') as variant,
            image_small, image_large, tcgplayer_url
        FROM read_parquet('{REGISTRY_PATH}')
        WHERE id = ? AND COALESCE(variant, 'normal') = ?
        LIMIT 1
    """
    meta = cursor.execute(meta_sql, [card_id, variant]).fetchdf()
    if meta.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Card '{card_id}' with variant '{variant}' not found",
        )
    
    price_conditions = ["card_id = ?", "variant = ?"]
    price_params: list = [card_id, variant]

    if from_date:
        price_conditions.append("price_date >= ?")
        price_params.append(from_date)
    if to_date:
        price_conditions.append("price_date <= ?")
        price_params.append(to_date)
    
    prices_sql = f"""
        SELECT price_date, monthly_price, daily_price
        FROM fct_card_price_features
        WHERE {" AND ".join(price_conditions)}
        ORDER BY price_date ASC
    """
    prices_df = cursor.execute(prices_sql, price_params).fetchdf()

    m = meta.iloc[0]
    return PriceHistoryResponse(
        card_id=m["card_id"],
        name=m["name"],
        variant=m["variant"],
        rarity=m["rarity"] if pd.notna(m["rarity"]) else None,
        set_id=m["set_id"],
        set_name=m["set_name"],
        image_small=m["image_small"],
        image_large=m["image_large"],
        prices=[
            PricePoint(
                price_date=row["price_date"],
                monthly_price=row["monthly_price"] if pd.notna(row["monthly_price"]) else None,
                daily_price=row["daily_price"] if pd.notna(row["daily_price"]) else None,
            )
            for _, row in prices_df.iterrows()
        ],
    )

@router.get("/market_aggregates", response_model=MarketAggregatesResponse)
def get_market_aggregates(
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)],
):
    # price_Xm_ago columns are already computed by the dbt model via lag() —
    # summing them on the latest snapshot per card is equivalent to historical market caps.
    sql = """
        SELECT
            COUNT(*)              AS total_cards,
            MAX(price_date)       AS date,
            SUM(monthly_price)    AS market_cap,
            SUM(price_1m_ago)     AS market_cap_1m,
            SUM(price_3m_ago)     AS market_cap_3m,
            SUM(price_6m_ago)     AS market_cap_6m,
            SUM(price_12m_ago)    AS market_cap_12m,
            SUM(price_60m_ago)    AS market_cap_5y
        FROM (
            SELECT monthly_price, price_date, price_1m_ago, price_3m_ago,
                   price_6m_ago, price_12m_ago, price_60m_ago
            FROM fct_card_price_features
            QUALIFY ROW_NUMBER() OVER (PARTITION BY card_id, variant ORDER BY price_date DESC) = 1
        )
    """
    row = cursor.execute(sql).fetchdf().iloc[0]

    def opt(val) -> float | None:
        return None if pd.isna(val) else round(float(val), 2)

    return MarketAggregatesResponse(
        total_cards=int(row["total_cards"]),
        date=row["date"].isoformat(),
        market_cap=round(float(row["market_cap"]), 2),
        market_cap_1m=opt(row["market_cap_1m"]),
        market_cap_3m=opt(row["market_cap_3m"]),
        market_cap_6m=opt(row["market_cap_6m"]),
        market_cap_12m=opt(row["market_cap_12m"]),
        market_cap_5y=opt(row["market_cap_5y"]),
        mae=MODEL_MAE_DOLLARS,
        rmse=MODEL_RMSE_DOLLARS,
    )

@router.get("/movers", response_model=MoversListResponse)
def get_movers(
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)]
):
    sql = """
        SELECT
            card_id,
            name,
            variant,
            rarity,
            set_id,
            set_name,
            monthly_price,
            price_3m_ago,
            (monthly_price - price_3m_ago) / price_3m_ago as return_3m
        FROM fct_card_price_features
        WHERE price_3m_ago IS NOT NULL AND monthly_price IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (PARTITION BY card_id, variant ORDER BY price_date DESC) = 1
    """
    rows = cursor.execute(sql).fetchdf()

    def opt(val):
        return None if pd.isna(val) else val

    def to_mover(card) -> MoverCardSummary:
        return MoverCardSummary(
            card_id=card.card_id,
            name=card.name,
            variant=card.variant,
            rarity=opt(card.rarity),
            set_id=card.set_id,
            set_name=card.set_name,
            monthly_price=card.monthly_price,
            monthly_price_3m_ago = card.price_3m_ago,
            return_3m=card.return_3m,
        )
    
    gainers = [to_mover(c) for c in rows.nlargest(10, "return_3m").itertuples()]
    losers = [to_mover(c) for c in rows.nsmallest(10, "return_3m").itertuples()]

    return MoversListResponse(
        gainers=gainers,
        losers=losers,
    )
