from datetime import date
from pydantic import BaseModel


class ModelMetrics(BaseModel):
    mae_dollars: float
    rmse_dollars: float
    evaluation_set: str     # description of the holdout set


class ModelInfoResponse(BaseModel):
    model_version: str
    model_type: str
    objective: str
    target: str             # what the model predicts, e.g. "return_3m"
    n_estimators: int
    learning_rate: float
    max_depth: int
    n_features: int
    features: list[str]
    train_cutoff: date
    metrics: ModelMetrics
