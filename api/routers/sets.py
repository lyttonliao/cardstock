from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends

import pandas as pd
import duckdb

from api.schemas.sets import SetListResponse, SetSummary
from api.dependencies import get_cursor
from api.constants import REGISTRY_PATH


router = APIRouter(prefix="/sets", tags=["sets"])

@router.get("", response_model=SetListResponse)
def get_sets(
    cursor: Annotated[duckdb.DuckDBPyConnection, Depends(get_cursor)]
):
    try:
        sql = f"""
            SELECT DISTINCT
                set_id,
                set_name AS name,
                set_series AS series,
                set_image_logo AS image_logo,
                set_image_symbol AS image_symbol
            FROM read_parquet('{REGISTRY_PATH}')
            ORDER BY set_name
        """
        rows = cursor.execute(sql).fetchdf()
    except Exception:
        # Image columns not yet backfilled — return sets without images
        sql = f"""
            SELECT DISTINCT
                set_id,
                set_name AS name,
                set_series AS series,
                NULL AS image_logo,
                NULL AS image_symbol
            FROM read_parquet('{REGISTRY_PATH}')
            ORDER BY set_name
        """
        rows = cursor.execute(sql).fetchdf()
    if rows.empty:
        raise HTTPException(status_code=404, detail="Set data not found")
    items = [
        SetSummary(
            set_id=row["set_id"],
            name=row["name"],
            series=row["series"],
            image_logo=row["image_logo"] if pd.notna(row["image_logo"]) else None,
            image_symbol=row["image_symbol"] if pd.notna(row["image_symbol"]) else None,
        ) for _, row in rows.iterrows()
    ]
    return SetListResponse(total=len(items), items=items)