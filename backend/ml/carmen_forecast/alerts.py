from __future__ import annotations

from datetime import datetime

import pandas as pd

from ml.carmen_forecast.baselines import rule_based_forecast_baseline
from ml.carmen_forecast.config import SAFETY_NOTE
from ml.carmen_forecast.explainability import derive_driver_statements
from ml.carmen_forecast.schemas import CarmenForecastAlert


def probability_to_risk_tier(probability: float) -> str:
    if probability >= 0.75:
        return "critical"
    if probability >= 0.50:
        return "high"
    if probability >= 0.25:
        return "moderate"
    return "low"


def build_carmen_alert(
    patient_id: str,
    prediction_time: datetime | str,
    horizon_hours: int,
    risk_probability: float,
    feature_row: pd.Series | dict[str, object] | None = None,
) -> CarmenForecastAlert:
    if feature_row is None:
        feature_row = pd.Series(dtype="object")
    else:
        feature_row = pd.Series(feature_row)
    rule_override = rule_based_forecast_baseline(feature_row)
    override_triggered = bool(rule_override["override"])
    final_probability = max(float(risk_probability), float(rule_override["probability"]))
    risk_tier = "critical" if override_triggered else probability_to_risk_tier(final_probability)
    drivers = derive_driver_statements(feature_row)
    if override_triggered:
        drivers = ["immediate threshold breach requiring urgent review"] + drivers[:4]

    recommended_action = (
        "Immediate clinical escalation"
        if risk_tier == "critical"
        else "Escalate to clinical review"
        if risk_tier in {"high", "moderate"}
        else "Continue routine monitoring with human oversight"
    )
    return CarmenForecastAlert(
        patient_id=patient_id,
        prediction_time=pd.to_datetime(prediction_time).to_pydatetime(),
        horizon_hours=horizon_hours,
        risk_probability=round(final_probability, 4),
        risk_tier=risk_tier,
        main_risk_drivers=drivers,
        recommended_action=recommended_action,
        safety_note=SAFETY_NOTE,
        override_triggered=override_triggered,
    )
