RISK_LEVELS = {
    "low": {
        "label": "🟢 BAJO",
        "description": "Signos vitales estables. Continúe con el tratamiento indicado.",
        "action": "Monitoreo rutinario cada 6 horas.",
        "alert_staff": False,
        "mews_range": "0-2",
        "framingham": "< 5%",
    },
    "moderate": {
        "label": "🟡 MODERADO",
        "description": "Desviación leve en algunos parámetros. Se requiere atención.",
        "action": "Aumente la frecuencia de monitoreo. Contacte a su médico si persiste.",
        "alert_staff": False,
        "mews_range": "3-4",
        "framingham": "5-9%",
    },
    "high": {
        "label": "🔴 ALTO",
        "description": "Riesgo significativo detectado. Se está notificando a su médico.",
        "action": "Su médico ha sido notificado. Siga las instrucciones que le indiquen.",
        "alert_staff": True,
        "mews_range": "5-6",
        "framingham": "> 9%",
    },
    "critical": {
        "label": "🚨 CRÍTICO",
        "description": "⚠️ ATENCIÓN URGENTE REQUERIDA. Diríjase a urgencias o llame al 123.",
        "action": "URGENCIAS INMEDIATAS. Su médico ha sido notificado.",
        "alert_staff": True,
        "mews_range": "≥ 7",
        "framingham": "Riesgo inminente",
    },
}


def should_alert_staff(risk_level: str) -> bool:
    return bool(RISK_LEVELS[risk_level]["alert_staff"])


RISK_ORDER = {
    "low": 0,
    "moderate": 1,
    "high": 2,
    "critical": 3,
}


def normalize_risk_level(value: str | int | None) -> str:
    if isinstance(value, int):
        return ["low", "moderate", "high", "critical"][max(0, min(value, 3))]
    if not value:
        return "low"
    normalized = str(value).strip().lower()
    if normalized in RISK_LEVELS:
        return normalized
    if normalized in {"bajo", "verde"}:
        return "low"
    if normalized in {"moderado", "medio", "amarillo"}:
        return "moderate"
    if normalized in {"alto", "rojo"}:
        return "high"
    if normalized in {"critico", "crítico", "urgente"}:
        return "critical"
    return "low"


def estimate_rule_based_risk(
    vital_signs: dict[str, object],
    clinical_info: dict[str, object] | None = None,
) -> dict[str, object]:
    clinical_info = clinical_info or {}
    score = 0
    critical_hit = False
    factors: list[dict[str, object]] = []

    def add(points: int, feature: str, value: object, reason: str, critical: bool = False) -> None:
        nonlocal score
        nonlocal critical_hit
        score += points
        critical_hit = critical_hit or critical
        factors.append(
            {
                "feature": feature,
                "value": value,
                "points": points,
                "reason": reason,
                "critical": critical,
            }
        )

    systolic = _float_or_none(vital_signs.get("systolic_bp"))
    heart_rate = _float_or_none(vital_signs.get("heart_rate"))
    oxygen = _float_or_none(vital_signs.get("oxygen_saturation"))
    glucose = _float_or_none(vital_signs.get("glucose"))
    bmi = _float_or_none(clinical_info.get("bmi") or vital_signs.get("bmi"))

    if systolic is not None:
        if systolic >= 180 or systolic < 80:
            add(3, "systolic_bp", systolic, "Umbral crítico de presión sistólica", critical=True)
        elif systolic >= 160 or systolic < 90:
            add(2, "systolic_bp", systolic, "Presión sistólica fuera de rango seguro")
        elif systolic >= 140:
            add(1, "systolic_bp", systolic, "Presión sistólica elevada")

    if heart_rate is not None:
        if heart_rate > 130 or heart_rate < 40:
            add(3, "heart_rate", heart_rate, "Frecuencia cardíaca crítica", critical=True)
        elif heart_rate > 110 or heart_rate < 50:
            add(2, "heart_rate", heart_rate, "Frecuencia cardíaca alterada")

    if oxygen is not None:
        if oxygen < 88:
            add(3, "oxygen_saturation", oxygen, "Saturación de oxígeno crítica", critical=True)
        elif oxygen < 92:
            add(2, "oxygen_saturation", oxygen, "Saturación baja")

    if glucose is not None:
        if glucose > 400 or glucose < 50:
            add(3, "glucose", glucose, "Glucosa crítica", critical=True)
        elif glucose > 300:
            add(2, "glucose", glucose, "Glucosa muy elevada")
        elif glucose > 200:
            add(1, "glucose", glucose, "Glucosa elevada")

    if bmi is not None and bmi > 35:
        add(1, "bmi", bmi, "IMC mayor a 35")

    for feature, points in (
        ("stroke_history", 2),
        ("heart_disease_history", 1),
        ("hypertension_history", 1),
        ("diabetes_history", 1),
    ):
        if clinical_info.get(feature):
            add(points, feature, True, "Antecedente clínico relevante")

    cholesterol = clinical_info.get("cholesterol_level")
    if cholesterol == 3:
        add(1, "cholesterol_level", cholesterol, "Colesterol muy elevado")

    if critical_hit or score >= 7:
        risk_level = "critical"
    elif score >= 5:
        risk_level = "high"
    elif score >= 3:
        risk_level = "moderate"
    else:
        risk_level = "low"

    probabilities = {
        "low": 0.0,
        "moderate": 0.0,
        "high": 0.0,
        "critical": 0.0,
    }
    probabilities[risk_level] = min(0.95, 0.55 + (score * 0.05))

    return {
        "risk_level": risk_level,
        "risk_probability": probabilities[risk_level],
        "probabilities": probabilities,
        "model_used": "clinical_rules_fallback",
        "shap_values": {},
        "top_risk_factors": factors[:5],
        "confidence_score": 0.62 if factors else 0.5,
    }


def _float_or_none(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
