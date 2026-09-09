"""Servicio del canal WhatsApp: deduplicación, sesión por número, conversación y envío."""
from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any

from channels.messages import Outbound
from channels.whatsapp.client import WhatsAppClient
from channels.whatsapp.conversation import (
    WhatsAppConversation,
    default_whatsapp_dependencies,
    tw,
)
from channels.whatsapp.session import InMemorySessionStore, SessionStore
from channels.whatsapp.webhook import InboundMessage, parse_webhook_payload
from config import settings


logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(
        self,
        *,
        conversation: WhatsAppConversation,
        client: Any | None,
        store: SessionStore | None = None,
        seen_limit: int = 2000,
    ) -> None:
        self.conversation = conversation
        self.client = client
        self.store: SessionStore = store or InMemorySessionStore()
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._seen_limit = seen_limit

    def remember(self, message_id: str) -> bool:
        """True si el mensaje es nuevo; False si ya se procesó (Meta reintenta webhooks)."""
        if message_id in self._seen:
            return False
        self._seen[message_id] = None
        while len(self._seen) > self._seen_limit:
            self._seen.popitem(last=False)
        return True

    def accept_payload(self, payload: Any) -> list[InboundMessage]:
        return [message for message in parse_webhook_payload(payload) if self.remember(message.message_id)]

    async def handle_message(self, inbound: InboundMessage) -> None:
        async with self.store.lock(inbound.wa_id):
            session = await self.store.get(inbound.wa_id)

            async def emit(outbound: Outbound) -> None:
                if self.client is None:
                    logger.warning("WhatsApp: sin cliente configurado; respuesta descartada para %s", inbound.wa_id)
                    return
                await self.client.send(inbound.wa_id, outbound)

            if self.client is not None:
                await self.client.mark_read(inbound.message_id)
            try:
                await self.conversation.handle(session, inbound, emit)
            except Exception:  # noqa: BLE001 - falla ruidosa en logs, respuesta segura al paciente
                logger.exception(
                    "WhatsApp: fallo procesando el mensaje %s de %s", inbound.message_id, inbound.wa_id
                )
                language = session.language or (session.profile or {}).get("language") or "es"
                await emit(Outbound(tw(language, "generic_failed")))
            finally:
                await self.store.save(session)


_SERVICE: WhatsAppService | None = None


def is_whatsapp_configured() -> bool:
    return bool(settings.whatsapp_access_token and settings.whatsapp_phone_number_id)


def get_whatsapp_service() -> WhatsAppService:
    global _SERVICE
    if _SERVICE is None:
        if not is_whatsapp_configured():
            raise RuntimeError(
                "WHATSAPP_ACCESS_TOKEN y WHATSAPP_PHONE_NUMBER_ID son necesarios para el canal WhatsApp."
            )
        client = WhatsAppClient(
            access_token=str(settings.whatsapp_access_token),
            phone_number_id=str(settings.whatsapp_phone_number_id),
            api_version=settings.whatsapp_api_version,
        )
        _SERVICE = WhatsAppService(
            conversation=WhatsAppConversation(default_whatsapp_dependencies()),
            client=client,
        )
    return _SERVICE


def reset_whatsapp_service() -> None:
    global _SERVICE
    _SERVICE = None
