from __future__ import annotations

import asyncio
from html import escape
from typing import Any

import httpx

from config import settings
from utils.risk_levels import RISK_LEVELS, normalize_risk_level


RESEND_ENDPOINT = "https://api.resend.com/emails"


async def send_risk_email_alert(payload: dict[str, Any], attempts: int = 3) -> bool:
    doctor_email = payload.get("doctor_email")
    if not settings.resend_api_key or not doctor_email:
        return False

    risk_level = normalize_risk_level(payload.get("risk_level"))
    risk = RISK_LEVELS[risk_level]
    subject = f"HomecareCCV - alerta {risk['label']} paciente {payload.get('patient_name') or payload.get('patient_id')}"
    body = build_risk_email_html(payload)
    request_payload = {
        "from": settings.from_email,
        "to": [doctor_email],
        "subject": subject,
        "html": body,
    }
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(RESEND_ENDPOINT, headers=headers, json=request_payload)
                if response.status_code < 400:
                    return True
        except httpx.HTTPError:
            pass
        if attempt < attempts:
            await asyncio.sleep(0.4 * attempt)
    return False


def build_risk_email_html(payload: dict[str, Any]) -> str:
    risk_level = normalize_risk_level(payload.get("risk_level"))
    risk = RISK_LEVELS[risk_level]
    patient = escape(str(payload.get("patient_name") or payload.get("patient_id") or "Paciente"))
    recommendation = escape(str(payload.get("recommendations") or risk["action"]))
    message = escape(str(payload.get("message") or risk["description"]))
    vitals = escape(_format_vitals(payload.get("vital_signs") or {}))
    emergency = (
        "<p><strong>Accion inmediata:</strong> orientar al paciente a urgencias o linea 123 Colombia.</p>"
        if risk_level == "critical"
        else ""
    )
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #17202a;">
        <h2>Alerta HomecareCCV: {escape(risk['label'])}</h2>
        <p><strong>Paciente:</strong> {patient}</p>
        <p><strong>Mensaje:</strong> {message}</p>
        <p><strong>Signos vitales:</strong> {vitals}</p>
        <p><strong>Recomendacion:</strong> {recommendation}</p>
        {emergency}
        <p>Este mensaje fue generado automaticamente por HomecareCCV.</p>
      </body>
    </html>
    """


def _format_vitals(vital_signs: dict[str, Any]) -> str:
    if not vital_signs:
        return "No disponibles"
    labels = {
        "systolic_bp": "PAS",
        "diastolic_bp": "PAD",
        "heart_rate": "FC",
        "oxygen_saturation": "SpO2",
        "glucose": "Glucosa",
        "pain_score": "Dolor",
        "dizziness_score": "Mareo",
        "dyspnea_score": "Disnea",
    }
    return ", ".join(f"{labels.get(key, key)}: {value}" for key, value in vital_signs.items() if value is not None)
