from typing import Generator
import duckdb
import xgboost as xgb

# Module-level singletons — set during lifespan startup, read during requests
_db_conn: duckdb.DuckDBPyConnection | None = None
_model: xgb.XGBRegressor | None = None


def set_db_conn(conn: duckdb.DuckDBPyConnection) -> None:
    global _db_conn
    _db_conn = conn


def set_model(model: xgb.XGBRegressor) -> None:
    global _model
    _model = model


def get_cursor() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Yields a per-request DuckDB cursor from the shared read-only connection.
    Each cursor is independent — this is thread-safe (conn.cursor() not conn.execute()).
    """
    if _db_conn is None:
        raise RuntimeError("Database connection not initialized")
    cursor = _db_conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def get_model() -> xgb.XGBRegressor:
    """
    Returns the shared XGBRegressor loaded at startup.
    model.predict() is stateless and thread-safe.
    """
    if _model is None:
        raise RuntimeError("Model not initialized")
    return _model
