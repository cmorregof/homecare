"""Webhook de la WhatsApp Cloud API (Meta): parseo de mensajes entrantes y verificación
de firma. Solo librería estándar; sin dependencias del resto del backend.

Forma del payload (campo `messages`):
{"object": "whatsapp_business_account",
 "entry": [{"changes": [{"field": "messages",
    "value": {"messaging_product": "whatsapp",
              "metadata": {"phone_number_id": "..."},
              "contacts": [{"wa_id": "573001234567", "profile": {"name": "Ana"}}],
              "messages": [{"from": "573001234567", "id": "wamid...", "type": "text",
                            "text": {"body": "hola"}}]}}]}]}

Las notificaciones de estado (`statuses`: sent/delivered/read) llegan por el mismo
webhook y se ignoran.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InboundMessage:
    wa_id: str  # número del paciente en E.164 sin '+', p. ej. 573001234567
    message_id: str  # wamid: sirve para deduplicar reintentos y marcar leído
    kind: str  # text | button | unsupported
    text: str = ""
    button_id: str | None = None
    profile_name: str = ""
    timestamp: str = ""
    phone_number_id: str = ""
    raw_type: str = ""


def parse_webhook_payload(payload: Any) -> list[InboundMessage]:
    inbound: list[InboundMessage] = []
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return inbound
    for entry in payload.get("entry") or []:
        for change in (entry or {}).get("changes") or []:
            value = (change or {}).get("value") or {}
            if value.get("messaging_product") != "whatsapp":
                continue
            names: dict[str, str] = {}
            for contact in value.get("contacts") or []:
                wa_id = str((contact or {}).get("wa_id") or "")
                if wa_id:
                    names[wa_id] = str(((contact or {}).get("profile") or {}).get("name") or "")
            phone_number_id = str((value.get("metadata") or {}).get("phone_number_id") or "")
            for message in value.get("messages") or []:
                parsed = _parse_message(message or {}, names, phone_number_id)
                if parsed is not None:
                    inbound.append(parsed)
    return inbound


def _parse_message(
    message: dict[str, Any],
    names: dict[str, str],
    phone_number_id: str,
) -> InboundMessage | None:
    wa_id = str(message.get("from") or "")
    message_id = str(message.get("id") or "")
    if not wa_id or not message_id:
        return None
    raw_type = str(message.get("type") or "")
    common: dict[str, Any] = {
        "wa_id": wa_id,
        "message_id": message_id,
        "profile_name": names.get(wa_id, ""),
        "timestamp": str(message.get("timestamp") or ""),
        "phone_number_id": phone_number_id,
        "raw_type": raw_type,
    }
    if raw_type == "text":
        body = str((message.get("text") or {}).get("body") or "")
        return InboundMessage(kind="text", text=body, **common)
    if raw_type == "interactive":
        interactive = message.get("interactive") or {}
        reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
        return InboundMessage(
            kind="button",
            text=str(reply.get("title") or ""),
            button_id=str(reply.get("id") or "") or None,
            **common,
        )
    if raw_type == "button":  # respuesta rápida de una plantilla
        button = message.get("button") or {}
        return InboundMessage(
            kind="button",
            text=str(button.get("text") or ""),
            button_id=str(button.get("payload") or "") or None,
            **common,
        )
    return InboundMessage(kind="unsupported", **common)


def verify_signature(app_secret: str | None, raw_body: bytes, header_value: str | None) -> bool:
    """Valida `X-Hub-Signature-256: sha256=<hmac>` calculado con el App Secret de Meta."""
    if not app_secret or not header_value:
        return False
    scheme, _, received = header_value.partition("=")
    if scheme.strip().lower() != "sha256" or not received:
        return False
    expected = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received.strip())
