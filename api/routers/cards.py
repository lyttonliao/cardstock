from datetime import date
from typing import Annotated, Optional

import pandas as pd
import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from api.constants import REGISTRY_PATH
from api.dependencies import get_cursor
from api.schemas.cards import CardListResponse, CardSummary, PriceHistoryResponse, PricePoint


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
        conditions.append("r.variant = ?")
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
            r.variant,
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
        ) f ON r.id = f.card_id AND r.variant = f.variant
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

@router.get("/{card_id}/prices", response_model=PriceHistoryResponse)
def get_price_history(
    card_id: str,
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)],
    variant: str = Query(..., description="Card variant (e.g. holofoil, normal, reverseHolofoil)"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
):
    meta_sql = f"""
        SELECT id AS card_id, name, rarity, set_id, set_name, variant,
            image_small, image_large, tcgplayer_url
        FROM read_parquet('{REGISTRY_PATH}')
        WHERE id = ? AND variant = ?
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
        prices=[
            PricePoint(
                price_date=row["price_date"],
                monthly_price=row["monthly_price"] if pd.notna(row["monthly_price"]) else None,
                daily_price=row["daily_price"] if pd.notna(row["daily_price"]) else None,
            )
            for _, row in prices_df.iterrows()
        ],
    )
