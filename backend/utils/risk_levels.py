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
