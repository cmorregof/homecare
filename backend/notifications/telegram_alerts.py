from __future__ import annotations

import asyncio
from typing import Any

import httpx

from config import settings
from utils.risk_levels import RISK_LEVELS, normalize_risk_level


async def send_telegram_risk_alert(
    payload: dict[str, Any],
    attempts: int = 3,
    patient_text: str | None = None,
) -> bool:
    token = settings.telegram_bot_token
    patient_chat_id = payload.get("patient_telegram_chat_id")
    doctor_chat_id = payload.get("doctor_telegram_chat_id")
    if not token or not (patient_chat_id or doctor_chat_id):
        return False

    message = build_telegram_alert_message(payload)
    results = []
    if patient_chat_id:
        results.append(
            await send_telegram_message(
                chat_id=int(patient_chat_id),
                text=patient_text or message,
                token=token,
                attempts=attempts,
            )
        )
    if doctor_chat_id:
        results.append(
            await send_telegram_message(
                chat_id=int(doctor_chat_id), text=message, token=token, attempts=attempts
            )
        )
    return any(results)


async def send_telegram_message(chat_id: int, text: str, token: str | None = None, attempts: int = 3) -> bool:
    token = token or settings.telegram_bot_token
    if not token:
        return False
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    for attempt in range(1, attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    endpoint,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                )
                if response.status_code < 400:
                    return True
        except httpx.HTTPError:
            pass
        if attempt < attempts:
            await asyncio.sleep(0.4 * attempt)
    return False


def build_telegram_alert_message(payload: dict[str, Any]) -> str:
    risk_level = normalize_risk_level(payload.get("risk_level"))
    risk = RISK_LEVELS[risk_level]
    patient_name = payload.get("patient_name") or payload.get("patient_id") or "paciente"
    vitals = _format_vitals(payload.get("vital_signs") or {})
    recommendation = payload.get("recommendations") or risk["action"]
    urgent = "\n\nSi hay signos de alarma, llama al 123 o dirígete a urgencias." if risk_level == "critical" else ""
    return (
        f"HomecareCCV - Alerta {risk['label']}\n"
        f"Paciente: {patient_name}\n"
        f"Signos vitales: {vitals}\n"
        f"Recomendación: {recommendation}{urgent}"
    )


def _format_vitals(vital_signs: dict[str, Any]) -> str:
    if not vital_signs:
        return "no disponibles"
    labels = {
        "systolic_bp": "PAS",
        "diastolic_bp": "PAD",
        "heart_rate": "FC",
        "respiratory_rate": "FR",
        "oxygen_saturation": "SpO2",
        "temperature": "temp",
        "weight_kg": "peso",
        "glucose": "glucosa",
        "pain_score": "dolor",
        "dizziness_score": "mareo",
        "dyspnea_score": "disnea",
    }
    return ", ".join(f"{labels.get(key, key)} {value}" for key, value in vital_signs.items() if value is not None)
