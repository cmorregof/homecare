from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query, Request

from bot.telegram_bot import configure_webhook, process_webhook_update
from config import settings


router = APIRouter(tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(update_payload: dict[str, Any]) -> dict[str, bool]:
    try:
        await process_webhook_update(update_payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/telegram/webhook/setup")
async def setup_telegram_webhook(
    request: Request,
    webhook_url: str | None = Query(default=None),
) -> dict[str, bool | str]:
    try:
        resolved_url = resolve_webhook_url(request, explicit_url=webhook_url)
        configured = await configure_webhook(webhook_url=resolved_url)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"ok": configured, "webhook_url": resolved_url}


def resolve_webhook_url(request: Request, explicit_url: str | None = None) -> str | None:
    if explicit_url:
        return explicit_url

    derived_url = str(request.url_for("telegram_webhook"))
    configured_url = settings.telegram_webhook_url
    if not configured_url:
        return derived_url

    configured_host = urlparse(configured_url).netloc
    request_host = request.url.netloc
    if (
        configured_host.endswith(".up.railway.app")
        and request_host.endswith(".up.railway.app")
        and configured_host != request_host
    ):
        return derived_url

    return configured_url
