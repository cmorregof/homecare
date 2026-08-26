"""Voz LLM de Carmen: reescribe con calidez los mensajes al paciente.

Fusión determinista + LLM: el contenido clínico (tier, cifras, overrides,
acciones) lo produce el núcleo determinista y llega aquí como borrador; el
LLM solo lo reescribe en la voz de Carmen (prompt de sistema de la enfermera,
colombiana, cálida, emojis con moderación). Guardas duras:

- Si no hay API key, el cliente falla, o la respuesta viene vacía → borrador.
- Si el nivel es crítico y la reescritura pierde la urgencia (123/urgencias)
  → borrador.
- El LLM tiene prohibido cambiar cifras, nivel de riesgo o inventar datos.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from config import settings

logger = logging.getLogger(__name__)

NURSE_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "nurse_system.txt"

STYLE_ADDENDUM = """
TAREA DE REESCRITURA:
Recibirás un JSON con datos clínicos verificados y un "borrador_actual" que ya
contiene toda la información correcta. Reescríbelo en tu voz: cálida, cercana,
colombiana, con emojis usados con moderación (2-4 por mensaje, nunca en temas
de urgencia grave salvo ⚠️ o 🚨). Reglas estrictas:
- NO cambies ninguna cifra, nivel de riesgo, ni recomendación clínica.
- NO agregues información clínica que no esté en el JSON.
- Si el nivel es crítico o alto, la urgencia debe quedar igual de clara
  (urgencias, línea 123 si aparece en el borrador).
- Mantén los comandos como /vitales tal cual.
- Máximo ~120 palabras, párrafos cortos.
Responde SOLO con el mensaje reescrito, sin comillas ni explicaciones.
"""


async def compose_patient_message(
    kind: str,
    payload: dict[str, Any],
    fallback: str,
    client: AsyncOpenAI | None = None,
) -> str:
    if not settings.openai_api_key:
        return fallback
    try:
        openai_client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        system_prompt = NURSE_PROMPT_PATH.read_text(encoding="utf-8") + STYLE_ADDENDUM
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            temperature=0.6,
            max_tokens=400,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"contexto": kind, **payload, "borrador_actual": fallback},
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            return fallback
        if _loses_urgency(payload, fallback, text):
            logger.warning("La voz LLM diluyó la urgencia; se usa el borrador determinista")
            return fallback
        return text
    except (OpenAIError, ValueError, KeyError) as exc:
        logger.warning("Voz LLM no disponible (%s); se usa el borrador determinista", exc)
        return fallback


def _loses_urgency(payload: dict[str, Any], fallback: str, text: str) -> bool:
    risk_level = str(payload.get("risk_level") or "").lower()
    if risk_level == "critical" or payload.get("es_emergencia"):
        return "123" not in text and "urgencias" not in text.lower()
    if risk_level == "high":
        return "médico" not in text.lower() and "medico" not in text.lower()
    return False
