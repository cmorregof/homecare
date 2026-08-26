from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ml.forecast import forecast_deterioration
from ml.predict import predict_risk


router = APIRouter(prefix="/ml", tags=["ml"])


class MlPredictRequest(BaseModel):
    patient_id: str
    vital_sign_id: str | None = None
    features: dict[str, Any] = Field(default_factory=dict)


class MlPredictResponse(BaseModel):
    risk_level: str
    risk_probability: float
    probabilities: dict[str, float]
    model_used: str
    shap_values: dict[str, float]
    top_risk_factors: list[dict[str, Any]]
    confidence_score: float
    override_applied: bool = False
    override_factors: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/predict", response_model=MlPredictResponse)
async def predict(payload: MlPredictRequest) -> dict[str, Any]:
    return predict_risk(payload.features)


class ForecastRequest(BaseModel):
    vital_history: list[dict[str, Any]] = Field(default_factory=list)
    clinical_info: dict[str, Any] = Field(default_factory=dict)


@router.post("/forecast")
async def forecast(payload: ForecastRequest) -> dict[str, Any]:
    result = forecast_deterioration(payload.vital_history, payload.clinical_info)
    if result is None:
        return {"available": False}
    return {"available": True, **result}
