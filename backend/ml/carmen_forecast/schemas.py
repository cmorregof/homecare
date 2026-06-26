from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RiskTier = Literal["low", "moderate", "high", "critical"]


class ForecastWindowMetadata(BaseModel):
    patient_id: str
    prediction_time: datetime
    horizon_hours: int = Field(ge=1)


class CarmenForecastAlert(BaseModel):
    patient_id: str
    prediction_time: datetime
    horizon_hours: int = Field(ge=1)
    risk_probability: float = Field(ge=0.0, le=1.0)
    risk_tier: RiskTier
    main_risk_drivers: list[str]
    recommended_action: str
    safety_note: str
    override_triggered: bool = False
