from contextlib import asynccontextmanager
import duckdb
import xgboost as xgb
from fastapi import FastAPI

from api.constants import DB_PATH, MODEL_PATH
from api.dependencies import set_db_conn, set_model
from api.routers import cards, predict, model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open a single read-only DuckDB connection shared across all requests.
    # read_only=True allows multiple processes to open the same .duckdb file.
    conn = duckdb.connect(DB_PATH, read_only=True)

    # Load the XGBoost model once at startup.
    # model.predict() is stateless and thread-safe for concurrent inference.
    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(MODEL_PATH)

    set_db_conn(conn)
    set_model(xgb_model)

    yield

    conn.close()


app = FastAPI(
    title="Cardstock",
    description="Pokemon TCG card price prediction API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(cards.router)
app.include_router(predict.router)
app.include_router(model.router)
