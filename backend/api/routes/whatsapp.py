"""Rutas del canal WhatsApp (Meta Cloud API).

GET  /whatsapp/webhook  → verificación del webhook (hub.challenge) al registrarlo en Meta.
POST /whatsapp/webhook  → mensajes entrantes. Se responde 200 de inmediato y el
                          procesamiento (voz LLM + pipeline) corre después de responder.

Sin `WHATSAPP_ACCESS_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID` el POST responde 503; sin
`WHATSAPP_VERIFY_TOKEN` el GET responde 503. Telegram no depende de nada de esto.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from channels.whatsapp.webhook import verify_signature
from config import settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
async def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    expected = settings.whatsapp_verify_token
    if not expected:
        raise HTTPException(status_code=503, detail="WHATSAPP_VERIFY_TOKEN no está configurado.")
    if hub_mode != "subscribe" or hub_verify_token != expected or hub_challenge is None:
        raise HTTPException(status_code=403, detail="Token de verificación inválido.")
    return PlainTextResponse(hub_challenge)


@router.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    # Import perezoso: si el canal fallara al importar, solo se cae esta ruta, no el servicio.
    from channels.whatsapp.service import get_whatsapp_service, is_whatsapp_configured

    if not is_whatsapp_configured():
        raise HTTPException(status_code=503, detail="El canal WhatsApp no está configurado.")
    raw_body = await request.body()
    app_secret = settings.whatsapp_app_secret
    if app_secret:
        if not verify_signature(app_secret, raw_body, request.headers.get("X-Hub-Signature-256")):
            raise HTTPException(status_code=403, detail="Firma del webhook inválida.")
    else:
        logger.warning("WhatsApp: WHATSAPP_APP_SECRET no configurado; el webhook acepta cualquier origen.")
    try:
        payload = json.loads(raw_body or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Cuerpo JSON inválido.") from exc

    service = get_whatsapp_service()
    inbound = service.accept_payload(payload)
    for message in inbound:
        background_tasks.add_task(service.handle_message, message)
    return {"ok": True, "queued": len(inbound)}
