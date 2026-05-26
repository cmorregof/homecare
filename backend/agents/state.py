from typing import Any, TypedDict


class HomecareAgentState(TypedDict, total=False):
    patient_id: str
    raw_message: str
    vital_signs: dict[str, Any]
    vital_sign_id: str
    risk_level: str
    risk_probability: float
    shap_values: dict[str, Any]
    clinical_report: str
    recommendations: str
    alert_sent: bool
    final_response: str
