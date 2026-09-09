"""Estado de conversación por número de WhatsApp.

Equivale al `context.user_data` de python-telegram-bot: idioma elegido, perfil en caché,
borrador del intake y banderas de vinculación/registro. Hoy vive en memoria del proceso
(un solo uvicorn, igual que Telegram); se pierde en cada redeploy. La versión persistida
en Supabase es trabajo pendiente y encaja detrás del protocolo `SessionStore`.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol


INTAKE_TTL = timedelta(hours=2)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class WhatsAppSession:
    wa_id: str
    language: str | None = None
    profile: dict[str, Any] | None = None
    intake_step: str | None = None
    vitals_draft: dict[str, Any] = field(default_factory=dict)
    intake_started_at: datetime | None = None
    awaiting_language: bool = False
    awaiting_document: bool = False
    awaiting_registration_name: bool = False
    registration_document: str | None = None
    updated_at: datetime = field(default_factory=utcnow)

    def clear_intake(self) -> None:
        self.intake_step = None
        self.vitals_draft = {}
        self.intake_started_at = None

    def clear_registration(self) -> None:
        self.awaiting_document = False
        self.awaiting_registration_name = False
        self.registration_document = None

    def expire_stale_intake(self, now: datetime | None = None) -> bool:
        """Descarta un intake a medias que lleva más de INTAKE_TTL sin respuesta."""
        now = now or utcnow()
        if self.intake_step and self.intake_started_at and now - self.intake_started_at > INTAKE_TTL:
            self.clear_intake()
            return True
        return False


class SessionStore(Protocol):
    async def get(self, wa_id: str) -> WhatsAppSession: ...

    async def save(self, session: WhatsAppSession) -> None: ...

    def lock(self, wa_id: str) -> asyncio.Lock: ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, WhatsAppSession] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def get(self, wa_id: str) -> WhatsAppSession:
        session = self._sessions.get(wa_id)
        if session is None:
            session = WhatsAppSession(wa_id=wa_id)
            self._sessions[wa_id] = session
        return session

    async def save(self, session: WhatsAppSession) -> None:
        session.updated_at = utcnow()
        self._sessions[session.wa_id] = session

    def lock(self, wa_id: str) -> asyncio.Lock:
        # Un paciente que manda dos mensajes seguidos no debe pisar su propia sesión.
        return self._locks.setdefault(wa_id, asyncio.Lock())
