from fastapi import APIRouter
from datetime import date
from api.constants import (
    FEATURES,
    MODEL_VERSION,
    TRAIN_CUTOFF,
    MODEL_PARAMS,
    MODEL_MAE_DOLLARS,
    MODEL_RMSE_DOLLARS
)
from api.schemas.model import ModelInfoResponse, ModelMetrics

router = APIRouter(prefix="/model", tags=["model"])

@router.get("/info", response_model=ModelInfoResponse)
def get_model_info():
    return ModelInfoResponse(
        model_version=MODEL_VERSION,
        model_type="XGBRegressor",
        objective="reg:squarederror",
        target="return_3m",
        n_estimators=MODEL_PARAMS["n_estimators"],
        learning_rate=MODEL_PARAMS["learning_rate"],
        max_depth=MODEL_PARAMS["max_depth"],
        n_features=len(FEATURES),
        features=FEATURES,
        train_cutoff=date.fromisoformat(TRAIN_CUTOFF),
        metrics=ModelMetrics(
            mae_dollars=MODEL_MAE_DOLLARS,
            rmse_dollars=MODEL_RMSE_DOLLARS,
            evaluation_set="March 2026 holdout (2026-03-01 onward)" # hard coded temporarily
        )
    )