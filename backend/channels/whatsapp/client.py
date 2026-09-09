"""Cliente mínimo de la WhatsApp Cloud API (Graph API de Meta) para enviar mensajes.

Solo se usa dentro de la ventana de 24 horas de servicio (respuestas a mensajes del
paciente). Los mensajes iniciados por el sistema fuera de esa ventana requieren
plantillas aprobadas por Meta y no están implementados todavía.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Sequence

import httpx

from channels.messages import Outbound


logger = logging.getLogger(__name__)

GRAPH_API_BASE_URL = "https://graph.facebook.com"
TEXT_BODY_LIMIT = 4096
BUTTON_BODY_LIMIT = 1024
BUTTON_TITLE_LIMIT = 20
BUTTON_ID_LIMIT = 256
MAX_BUTTONS = 3


class WhatsAppClient:
    def __init__(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        api_version: str = "v25.0",
        http_client: Any | None = None,
        attempts: int = 3,
        base_url: str = GRAPH_API_BASE_URL,
        timeout: float = 15.0,
    ) -> None:
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.attempts = attempts
        self.timeout = timeout
        self._http_client = http_client
        self.messages_url = f"{base_url.rstrip('/')}/{api_version}/{phone_number_id}/messages"

    async def send(self, to: str, outbound: Outbound) -> bool:
        if not outbound.buttons:
            return await self.send_text(to, outbound.text)
        if len(outbound.text) <= BUTTON_BODY_LIMIT:
            return await self.send_buttons(to, outbound.text, outbound.buttons)
        # Cuerpo largo: el texto va aparte y los botones en un mensaje corto.
        sent_text = await self.send_text(to, outbound.text)
        sent_buttons = await self.send_buttons(to, "👇", outbound.buttons)
        return sent_text and sent_buttons

    async def send_text(self, to: str, text: str) -> bool:
        ok = True
        for chunk in split_text(text, TEXT_BODY_LIMIT):
            sent = await self._post(
                {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {"preview_url": False, "body": chunk},
                }
            )
            ok = ok and sent
        return ok

    async def send_buttons(self, to: str, body: str, buttons: Sequence[tuple[str, str]]) -> bool:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body[:BUTTON_BODY_LIMIT]},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": str(button_id)[:BUTTON_ID_LIMIT],
                                "title": str(title)[:BUTTON_TITLE_LIMIT],
                            },
                        }
                        for button_id, title in list(buttons)[:MAX_BUTTONS]
                    ]
                },
            },
        }
        return await self._post(payload)

    async def mark_read(self, message_id: str) -> bool:
        return await self._post(
            {"messaging_product": "whatsapp", "status": "read", "message_id": message_id},
            attempts=1,
        )

    async def _post(self, payload: dict[str, Any], attempts: int | None = None) -> bool:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        tries = attempts or self.attempts
        for attempt in range(1, tries + 1):
            try:
                response = await self._request(payload, headers)
            except httpx.HTTPError as exc:
                logger.warning("WhatsApp: fallo de red al enviar (intento %s/%s): %s", attempt, tries, exc)
            else:
                if response.status_code < 300:
                    return True
                logger.warning(
                    "WhatsApp: la API respondió %s (intento %s/%s): %s",
                    response.status_code,
                    attempt,
                    tries,
                    str(getattr(response, "text", ""))[:500],
                )
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    return False
            if attempt < tries:
                await asyncio.sleep(0.5 * attempt)
        return False

    async def _request(self, payload: dict[str, Any], headers: dict[str, str]) -> Any:
        if self._http_client is not None:
            return await self._http_client.post(self.messages_url, json=payload, headers=headers)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(self.messages_url, json=payload, headers=headers)


def split_text(text: str, limit: int) -> list[str]:
    """Parte un texto largo respetando saltos de línea cuando se puede."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) > limit:
            chunks.append(current)
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk]
