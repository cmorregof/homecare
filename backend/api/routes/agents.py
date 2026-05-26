from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.nurse_agent import NurseAgent


router = APIRouter(prefix="/agents", tags=["agents"])


class VitalReportRequest(BaseModel):
    patient_id: str
    raw_message: str = ""
    vital_signs: dict[str, Any] = Field(default_factory=dict)
    source: str = "web"


class VitalReportResponse(BaseModel):
    patient_id: str
    vital_sign_id: str | None = None
    prediction_id: str | None = None
    risk_level: str | None = None
    risk_probability: float | None = None
    recommendations: str | None = None
    follow_up_actions: str | None = None
    alert_sent: bool = False
    final_response: str
    rag_sources: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/vital-report", response_model=VitalReportResponse)
async def process_vital_report(payload: VitalReportRequest) -> dict[str, Any]:
    state = await NurseAgent().process_vital_report(payload.model_dump())
    return {
        "patient_id": state["patient_id"],
        "vital_sign_id": state.get("vital_sign_id"),
        "prediction_id": state.get("prediction_id"),
        "risk_level": state.get("risk_level"),
        "risk_probability": state.get("risk_probability"),
        "recommendations": state.get("recommendations"),
        "follow_up_actions": state.get("follow_up_actions"),
        "alert_sent": bool(state.get("alert_sent")),
        "final_response": state.get("final_response", ""),
        "rag_sources": state.get("rag_sources", []),
    }
