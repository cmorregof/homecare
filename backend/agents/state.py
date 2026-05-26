from typing import Any, TypedDict


class HomecareAgentState(TypedDict, total=False):
    patient_id: str
    raw_message: str
    vital_signs: dict[str, Any]
    vital_sign_id: str
    prediction_id: str
    risk_level: str
    risk_probability: float
    probabilities: dict[str, float]
    shap_values: dict[str, Any]
    top_risk_factors: list[dict[str, Any]]
    model_used: str
    confidence_score: float
    patient_clinical_info: dict[str, Any]
    clinical_report: str
    interpretation: str
    recommendations: str
    follow_up_actions: str
    rag_sources: list[dict[str, Any]]
    validation_errors: list[str]
    alert_needed: bool
    alert_sent: bool
    final_response: str
