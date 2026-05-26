from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from bot.telegram_bot import configure_webhook, process_webhook_update


router = APIRouter(tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(update_payload: dict[str, Any]) -> dict[str, bool]:
    try:
        await process_webhook_update(update_payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/telegram/webhook/setup")
async def setup_telegram_webhook() -> dict[str, bool]:
    try:
        configured = await configure_webhook()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"ok": configured}
