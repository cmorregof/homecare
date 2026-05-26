from __future__ import annotations

from typing import Any


FEATURES = [
    "age",
    "gender_encoded",
    "systolic_bp",
    "diastolic_bp",
    "heart_rate",
    "oxygen_saturation",
    "glucose",
    "bmi",
    "cholesterol_level",
    "hypertension_history",
    "heart_disease_history",
    "stroke_history",
    "diabetes_history",
    "smoking_encoded",
    "alcohol_intake",
    "physical_activity",
    "pain_score",
    "dizziness_score",
    "dyspnea_score",
    "pulse_pressure",
    "map",
    "bmi_category",
]

TARGET = "risk_level"

RISK_LABELS = {
    0: "low",
    1: "moderate",
    2: "high",
    3: "critical",
}

RISK_TO_CLASS = {value: key for key, value in RISK_LABELS.items()}

FEATURE_DEFAULTS = {
    "age": 65,
    "gender_encoded": 0,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "heart_rate": 75,
    "oxygen_saturation": 97,
    "glucose": 100,
    "bmi": 25,
    "cholesterol_level": 1,
    "hypertension_history": False,
    "heart_disease_history": False,
    "stroke_history": False,
    "diabetes_history": False,
    "smoking_encoded": 0,
    "alcohol_intake": False,
    "physical_activity": True,
    "pain_score": 0,
    "dizziness_score": 0,
    "dyspnea_score": 0,
    "pulse_pressure": 40,
    "map": 93.3,
    "bmi_category": 1,
}


def normalize_feature_payload(features: dict[str, Any]) -> dict[str, Any]:
    normalized = {feature: features.get(feature, FEATURE_DEFAULTS[feature]) for feature in FEATURES}
    normalized["systolic_bp"] = _float_or_default(normalized["systolic_bp"], FEATURE_DEFAULTS["systolic_bp"])
    normalized["diastolic_bp"] = _float_or_default(normalized["diastolic_bp"], FEATURE_DEFAULTS["diastolic_bp"])
    normalized["heart_rate"] = _float_or_default(normalized["heart_rate"], FEATURE_DEFAULTS["heart_rate"])
    normalized["oxygen_saturation"] = _float_or_default(
        normalized["oxygen_saturation"],
        FEATURE_DEFAULTS["oxygen_saturation"],
    )
    normalized["glucose"] = _float_or_default(normalized["glucose"], FEATURE_DEFAULTS["glucose"])
    normalized["bmi"] = _float_or_default(normalized["bmi"], FEATURE_DEFAULTS["bmi"])
    normalized["pulse_pressure"] = normalized["systolic_bp"] - normalized["diastolic_bp"]
    normalized["map"] = normalized["diastolic_bp"] + (normalized["pulse_pressure"] / 3)
    normalized["bmi_category"] = bmi_category(normalized["bmi"])

    for field in (
        "hypertension_history",
        "heart_disease_history",
        "stroke_history",
        "diabetes_history",
        "alcohol_intake",
        "physical_activity",
    ):
        normalized[field] = bool(normalized[field])

    for field in ("gender_encoded", "cholesterol_level", "smoking_encoded", "pain_score", "dizziness_score", "dyspnea_score"):
        normalized[field] = int(_float_or_default(normalized[field], FEATURE_DEFAULTS[field]))

    return normalized


def add_derived_features(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    systolic = _float_or_default(normalized.get("systolic_bp"), FEATURE_DEFAULTS["systolic_bp"])
    diastolic = _float_or_default(normalized.get("diastolic_bp"), FEATURE_DEFAULTS["diastolic_bp"])
    bmi = _float_or_default(normalized.get("bmi"), FEATURE_DEFAULTS["bmi"])
    normalized["pulse_pressure"] = systolic - diastolic
    normalized["map"] = diastolic + (normalized["pulse_pressure"] / 3)
    normalized["bmi_category"] = bmi_category(bmi)
    return normalized


def bmi_category(bmi: float | int | None) -> int:
    bmi_value = _float_or_default(bmi, FEATURE_DEFAULTS["bmi"])
    if bmi_value < 18.5:
        return 0
    if bmi_value < 25:
        return 1
    if bmi_value < 30:
        return 2
    return 3


def risk_class_to_label(value: int | str) -> str:
    if isinstance(value, str):
        if value in RISK_TO_CLASS:
            return value
        return RISK_LABELS.get(int(value), "low")
    return RISK_LABELS.get(int(value), "low")


def risk_label_to_class(value: int | str) -> int:
    if isinstance(value, int):
        return max(0, min(value, 3))
    return RISK_TO_CLASS.get(str(value), 0)


def _float_or_default(value: Any, default: Any) -> float:
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)
