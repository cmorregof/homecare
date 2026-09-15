"""Conversación de Carmen por WhatsApp: el mismo cerebro, un segundo canal.

Reproduce el comportamiento del bot de Telegram (`bot/handlers.py`) reutilizando sus
funciones puras: detección de documento y nombre, respuesta de texto libre, formato de
estado e historial, asignación de médico, y el pipeline completo del reporte
(`NurseAgent.process_vital_report`). Lo que cambia es la capa de transporte:

- No hay menú de comandos: se aceptan `/vitales` y también palabras sueltas
  ("vitales", "estado", "ayuda"...) y botones de respuesta.
- No llega `language_code` del teléfono: el idioma sale del perfil, de la elección
  explícita, o es español.
- La respuesta se emite por `emit` a medida que se produce, para que el paciente vea
  "estoy analizando" antes de que corra el pipeline.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from bot.handlers import (
    _first_name,
    _mentions_emergency,
    _normalize_text,
    build_carmen_free_text_response,
    build_raw_message_from_draft,
    extract_document_id,
    extract_full_name,
    format_latest_status_message,
    format_vital_history_message,
    looks_like_document_id,
    looks_like_vital_report,
    notify_doctor_new_patient,
    pick_doctor_for_new_patient,
    wants_history_context,
    wants_status_context,
)
from bot.i18n import (
    CHOOSE_LANGUAGE,
    LANGUAGE_NOT_UNDERSTOOD,
    normalize_language,
    parse_language_choice,
    t,
)
from channels.intake import IntakeContext, advance_intake, start_intake
from channels.messages import Outbound
from channels.whatsapp.session import WhatsAppSession, utcnow
from channels.whatsapp.webhook import InboundMessage
from db.repository import HomecareRepository
from notifications.email import send_risk_email_alert
from notifications.telegram_alerts import send_telegram_risk_alert


logger = logging.getLogger(__name__)

Emit = Callable[[Outbound], Awaitable[None]]

LANGUAGE_BUTTONS: tuple[tuple[str, str], ...] = (("lang:es", "Español 🇨🇴"), ("lang:en", "English 🇬🇧"))
_VITALS_BUTTON = {"es": ("vitals", "Registrar signos"), "en": ("vitals", "Log my vitals")}
_EMERGENCY_BUTTON = {"es": ("emergency", "🚨 Avisar al equipo"), "en": ("emergency", "🚨 Alert my team")}

# Textos propios del canal. Todo lo demás sale del catálogo compartido `bot/i18n.py`.
WHATSAPP_MESSAGES: dict[str, dict[str, str]] = {
    "help": {
        "es": (
            "Soy Carmen, la enfermera virtual de HomecareCCV. 👵 Por WhatsApp me puedes escribir:\n"
            "• *vitales* - registrar tus signos vitales paso a paso\n"
            "• *estado* - ver tu último nivel de riesgo\n"
            "• *historial* - ver tus últimas 5 mediciones\n"
            "• *emergencia* - avisar de inmediato a tu equipo de salud\n"
            "• *idioma* - cambiar el idioma en que te hablo\n"
            "• *cancelar* - detener el registro en curso\n"
            "• *ayuda* - ver esta lista\n\n"
            "También puedes escribirme en tus palabras, por ejemplo: presión 120/80, pulso 75."
        ),
        "en": (
            "I'm Carmen, HomecareCCV's virtual nurse. 👵 On WhatsApp you can write:\n"
            "• *vitals* - log your vital signs step by step\n"
            "• *status* - see your latest risk level\n"
            "• *history* - see your last 5 measurements\n"
            "• *emergency* - alert your care team right away\n"
            "• *language* - change the language I speak to you\n"
            "• *cancel* - stop the log in progress\n"
            "• *help* - show this list\n\n"
            "You can also write in your own words, for example: pressure 120/80, pulse 75."
        ),
    },
    "linked_ok": {
        "es": (
            "Listo, {name}. Tu WhatsApp quedó vinculado.\n\n"
            "Para registrar signos vitales escríbeme *vitales* o toca el botón."
        ),
        "en": (
            "Done, {name}. Your WhatsApp is now linked.\n\n"
            "To log your vital signs, write *vitals* or tap the button."
        ),
    },
    "unsupported": {
        "es": (
            "Por ahora solo entiendo mensajes de texto. "
            "Escríbeme tus datos en palabras o números, por favor."
        ),
        "en": (
            "For now I only understand text messages. "
            "Please write your data in words or numbers."
        ),
    },
    "report_failed": {
        "es": (
            "No pude procesar tu reporte en este momento y el fallo ya quedó registrado "
            "para el equipo técnico. Si te sientes mal, no esperes: llama al 123 o ve a "
            "urgencias. Intenta enviarlo de nuevo en unos minutos."
        ),
        "en": (
            "I couldn't process your report right now and the failure has been logged "
            "for the technical team. If you feel unwell, don't wait: call 123 or go to "
            "the emergency room. Please try again in a few minutes."
        ),
    },
    "generic_failed": {
        "es": (
            "Algo falló de mi lado y ya quedó registrado. Si te sientes mal, no esperes: "
            "llama al 123 o ve a urgencias. Escríbeme de nuevo en unos minutos."
        ),
        "en": (
            "Something failed on my side and it has been logged. If you feel unwell, "
            "don't wait: call 123 or go to the emergency room. Write to me again in a few minutes."
        ),
    },
}


def tw(language: str, key: str, **kwargs: object) -> str:
    entry = WHATSAPP_MESSAGES[key]
    template = entry.get(normalize_language(language)) or entry["es"]
    return template.format(**kwargs)


def vitals_button(language: str) -> tuple[str, str]:
    return _VITALS_BUTTON.get(normalize_language(language), _VITALS_BUTTON["es"])


def emergency_button(language: str) -> tuple[str, str]:
    return _EMERGENCY_BUTTON.get(normalize_language(language), _EMERGENCY_BUTTON["es"])


_COMMANDS: dict[str, set[str]] = {
    "start": {"/start", "start", "inicio", "/inicio"},
    "vitals": {
        "/vitales", "/registro", "vitales", "registro", "signos", "signos vitales",
        "registrar", "registrar signos", "reportar", "vitals", "log my vitals", "report",
    },
    "status": {"/estado", "estado", "status"},
    "history": {"/historial", "historial", "history"},
    "help": {"/ayuda", "ayuda", "/help", "help", "menu"},
    "emergency": {"/emergencia", "emergencia", "emergency", "sos"},
    "language": {"/idioma", "idioma", "/language", "language"},
    "cancel": {"/cancelar", "cancelar", "cancel"},
}
_BUTTON_COMMANDS = {"vitals": "vitals", "emergency": "emergency", "help": "help", "start": "start"}
_LANGUAGE_WORDS = {"/idioma", "idioma", "/language", "language"}


def parse_command(text: str, button_id: str | None = None) -> tuple[str | None, str]:
    """(comando, argumento). Los ids de botón mandan; luego palabras exactas."""
    if button_id:
        if button_id in _BUTTON_COMMANDS:
            return _BUTTON_COMMANDS[button_id], ""
        if button_id.startswith("lang:"):
            return "language", button_id.split(":", 1)[1]
    normalized = " ".join(_normalize_text(text).split())
    for command, words in _COMMANDS.items():
        if normalized in words:
            return command, ""
    first, _, rest = normalized.partition(" ")
    if first in _LANGUAGE_WORDS and rest:
        return "language", rest
    return None, ""


@dataclass
class WhatsAppDependencies:
    repository: HomecareRepository
    nurse_agent: Any
    voice: Any | None = None


def default_whatsapp_dependencies() -> WhatsAppDependencies:
    from agents.nurse_agent import build_wired_nurse_agent
    from agents.nurse_voice import compose_patient_message

    repository = HomecareRepository()
    return WhatsAppDependencies(
        repository=repository,
        nurse_agent=build_wired_nurse_agent(repository),
        voice=compose_patient_message,
    )


class WhatsAppConversation:
    """Procesa un mensaje entrante y emite las respuestas por `emit` a medida que salen."""

    def __init__(self, dependencies: WhatsAppDependencies) -> None:
        self.deps = dependencies

    async def handle(self, session: WhatsAppSession, inbound: InboundMessage, emit: Emit) -> None:
        if session.expire_stale_intake():
            logger.info("WhatsApp: intake de %s expirado por inactividad; se descarta el borrador.", session.wa_id)
        language = self._language(session)
        if inbound.kind == "unsupported":
            await emit(Outbound(tw(language, "unsupported")))
            return
        text = inbound.text.strip()
        if not text:
            return
        command, argument = parse_command(text, inbound.button_id)

        # Globales: funcionan en cualquier punto de la conversación, como en Telegram.
        if command == "language":
            await self._language_command(session, argument, emit)
            return
        if command == "cancel":
            await self._cancel(session, emit)
            return
        if command == "help":
            await emit(Outbound(tw(language, "help"), (vitals_button(language),)))
            return
        if session.awaiting_language:
            await self._language_choice(session, text, emit)
            return
        if command == "start":
            await self._start(session, emit)
            return
        if command == "emergency":
            await self._emergency(session, emit)
            return
        if command == "vitals":
            await self._begin_intake(session, emit)
            return
        if command == "status":
            await self._status(session, emit)
            return
        if command == "history":
            await self._history(session, emit)
            return
        if session.intake_step:
            await self._intake_answer(session, text, emit)
            return
        if session.awaiting_registration_name:
            await self._register_name(session, text, emit)
            return
        if session.awaiting_document:
            await self._link_document(session, text, emit)
            return

        profile = await self._linked_profile(session)
        if not profile:
            if looks_like_document_id(text) or extract_document_id(text):
                session.awaiting_document = True
                await self._link_document(session, text, emit)
                return
            if _mentions_emergency(_normalize_text(text)):
                # Igual que en Telegram: la emergencia se atiende aunque no haya cuenta.
                await emit(Outbound(build_carmen_free_text_response(text, None, language=language)))
                return
            await self._start(session, emit)
            return
        if looks_like_vital_report(text):
            await emit(Outbound(t(language, "analyzing_free_text")))
            state = await self._process_report(session, profile, raw_message=text, vital_signs={})
            await emit(Outbound(state.get("final_response") or t(language, "received")))
            return
        await self._free_text(session, profile, text, emit)

    # ------------------------------------------------------------------ saludo e idioma

    async def _start(self, session: WhatsAppSession, emit: Emit) -> None:
        profile = await self._linked_profile(session)
        language = self._language(session)
        if profile:
            await emit(
                Outbound(
                    t(language, "start_linked", name=profile.get("full_name", "")),
                    (vitals_button(language),),
                )
            )
            return
        session.awaiting_language = True
        session.awaiting_document = False
        await emit(Outbound(CHOOSE_LANGUAGE, LANGUAGE_BUTTONS))

    async def _language_command(self, session: WhatsAppSession, argument: str, emit: Emit) -> None:
        choice = parse_language_choice(argument) if argument else None
        if choice:
            await self._apply_language(session, choice, emit)
            return
        session.awaiting_language = True
        await emit(Outbound(CHOOSE_LANGUAGE, LANGUAGE_BUTTONS))

    async def _language_choice(self, session: WhatsAppSession, text: str, emit: Emit) -> None:
        choice = parse_language_choice(text)
        if choice is None:
            if looks_like_document_id(text) or extract_document_id(text):
                # Saltó la pregunta y mandó su documento: seguimos con el idioma actual.
                session.awaiting_language = False
                session.awaiting_document = True
                await self._link_document(session, text, emit)
                return
            await emit(Outbound(LANGUAGE_NOT_UNDERSTOOD, LANGUAGE_BUTTONS))
            return
        await self._apply_language(session, choice, emit)

    async def _apply_language(self, session: WhatsAppSession, language: str, emit: Emit) -> None:
        session.awaiting_language = False
        session.language = language
        profile = await self._linked_profile(session)
        if profile:
            await self._persist_language(session, profile, language)
            await emit(Outbound(t(language, "language_set"), (vitals_button(language),)))
            return
        if session.awaiting_registration_name:
            await emit(Outbound(t(language, "language_set")))
            return
        session.awaiting_document = True
        await emit(Outbound(t(language, "language_set") + "\n\n" + t(language, "ask_document")))

    async def _persist_language(
        self, session: WhatsAppSession, profile: dict[str, Any], language: str
    ) -> None:
        """Guarda el idioma en el perfil; si falla (migración pendiente) queda en memoria."""
        session.language = language
        profile["language"] = language
        repository = self.deps.repository
        if profile.get("id") and hasattr(repository, "update_profile_language"):
            await repository.update_profile_language(str(profile["id"]), language)

    # ------------------------------------------------------------- vinculación y registro

    async def _link_document(self, session: WhatsAppSession, text: str, emit: Emit) -> None:
        language = self._language(session)
        document_id = text.strip()
        pending_name: str | None = None
        if not looks_like_document_id(document_id):
            extracted = extract_document_id(text)
            if extracted is None:
                await emit(Outbound(t(language, "doc_invalid")))
                return
            document_id = extracted
            pending_name = extract_full_name(text)
        profile = await self.deps.repository.link_whatsapp_account(document_id, session.wa_id)
        if not profile:
            if pending_name:
                await self._create_account(session, pending_name, document_id, emit)
                return
            session.awaiting_document = False
            session.registration_document = document_id
            session.awaiting_registration_name = True
            await emit(Outbound(t(language, "doc_unknown_offer_registration")))
            return
        session.awaiting_document = False
        self._cache_profile(session, profile)
        await self._persist_language(session, profile, language)
        await emit(
            Outbound(
                tw(language, "linked_ok", name=profile.get("full_name", "")),
                (vitals_button(language),),
            )
        )

    async def _register_name(self, session: WhatsAppSession, text: str, emit: Emit) -> None:
        language = self._language(session)
        if _normalize_text(text) in {"cancelar", "no", "no gracias", "no quiero", "cancel", "no thanks"}:
            session.clear_registration()
            await emit(Outbound(t(language, "registration_cancelled")))
            return

        document_in_text = extract_document_id(text)
        if document_in_text:
            existing = await self.deps.repository.link_whatsapp_account(document_in_text, session.wa_id)
            if existing:
                session.clear_registration()
                self._cache_profile(session, existing)
                await self._persist_language(session, existing, language)
                await emit(
                    Outbound(
                        t(language, "already_had_account", name=existing.get("full_name", "")),
                        (vitals_button(language),),
                    )
                )
                return
            session.registration_document = document_in_text

        full_name = extract_full_name(text)
        if full_name is None:
            await emit(Outbound(t(language, "need_full_name")))
            return
        document_id = str(session.registration_document or "")
        await self._create_account(session, full_name, document_id, emit)

    async def _create_account(
        self, session: WhatsAppSession, full_name: str, document_id: str, emit: Emit
    ) -> None:
        language = self._language(session)
        repository = self.deps.repository
        doctor = await pick_doctor_for_new_patient(repository)
        profile = await repository.create_patient_account(
            full_name=full_name,
            document_id=document_id,
            whatsapp_phone=session.wa_id,
            assigned_doctor_id=str(doctor["id"]) if doctor else None,
        )
        if not profile:
            await emit(Outbound(t(language, "account_create_failed")))
            return
        session.clear_registration()
        self._cache_profile(session, profile)
        await self._persist_language(session, profile, language)
        doctor_note = t(language, "doctor_note", doctor=doctor.get("full_name")) if doctor else ""
        await emit(
            Outbound(
                t(language, "account_created", name=profile.get("full_name", ""), doctor_note=doctor_note),
                (vitals_button(language),),
            )
        )
        if doctor:
            await notify_doctor_new_patient(doctor, profile)

    async def _ensure_patient(self, session: WhatsAppSession, emit: Emit) -> dict[str, Any] | None:
        profile = await self._linked_profile(session)
        if profile and profile.get("role") == "patient":
            return profile
        language = self._language(session)
        if profile:
            await emit(Outbound(t(language, "only_patients")))
            return None
        session.awaiting_document = True
        await emit(Outbound(t(language, "need_link_first")))
        return None

    # ------------------------------------------------------------------- intake guiado

    async def _begin_intake(self, session: WhatsAppSession, emit: Emit) -> None:
        profile = await self._ensure_patient(session, emit)
        if not profile:
            return
        session.clear_intake()
        result = await start_intake(self._intake_context(session))
        session.intake_step = result.next_step
        session.intake_started_at = utcnow()
        for reply in result.replies:
            await emit(reply)

    async def _intake_answer(self, session: WhatsAppSession, text: str, emit: Emit) -> None:
        ctx = self._intake_context(session)
        result = await advance_intake(ctx, str(session.intake_step), session.vitals_draft, text)
        for reply in result.replies:
            await emit(reply)
        if result.completed:
            draft = dict(session.vitals_draft)
            session.clear_intake()
            profile = await self._ensure_patient(session, emit)
            if not profile:
                return
            await emit(Outbound(t(ctx.language, "analyzing")))
            state = await self._process_report(
                session,
                profile,
                raw_message=build_raw_message_from_draft(draft),
                vital_signs=draft,
            )
            await emit(Outbound(state.get("final_response") or t(ctx.language, "final_response_missing")))
            return
        if result.aborted:
            session.clear_intake()
            return
        session.intake_step = result.next_step

    async def _cancel(self, session: WhatsAppSession, emit: Emit) -> None:
        language = self._language(session)
        session.clear_intake()
        session.clear_registration()
        await emit(Outbound(t(language, "cancelled")))

    # --------------------------------------------------------- estado, historial, emergencia

    async def _status(self, session: WhatsAppSession, emit: Emit) -> None:
        profile = await self._ensure_patient(session, emit)
        if not profile:
            return
        language = self._language(session)
        prediction = await self.deps.repository.get_latest_risk_prediction(str(profile["id"]))
        draft = format_latest_status_message(prediction, language)
        await emit(Outbound(await self._voiced(language, "consulta_de_estado", draft)))

    async def _history(self, session: WhatsAppSession, emit: Emit) -> None:
        profile = await self._ensure_patient(session, emit)
        if not profile:
            return
        language = self._language(session)
        rows = await self.deps.repository.get_recent_vital_signs(str(profile["id"]), limit=5)
        draft = format_vital_history_message(rows, language)
        await emit(Outbound(await self._voiced(language, "consulta_de_historial", draft)))

    async def _emergency(self, session: WhatsAppSession, emit: Emit) -> None:
        profile = await self._ensure_patient(session, emit)
        if not profile:
            return
        session.clear_intake()
        language = self._language(session)
        patient_id = str(profile["id"])
        message = (
            f"Alerta manual HomecareCCV: el paciente {profile.get('full_name') or patient_id} "
            "activó emergencia desde WhatsApp."
        )
        recipients = await self._alert_recipients(patient_id)
        payload = {
            **recipients,
            "patient_id": patient_id,
            "patient_name": profile.get("full_name"),
            "risk_level": "critical",
            "message": message,
            "recommendations": "Contactar al paciente de inmediato y orientar urgencias si hay signos de alarma.",
            "vital_signs": {},
        }
        telegram_sent = await send_telegram_risk_alert(payload)
        email_sent = await send_risk_email_alert(payload)
        await self.deps.repository.save_alert(
            {
                "patient_id": patient_id,
                "risk_level": "critical",
                "message": message,
                "sent_to_patient": True,  # la confirmación sale por este mismo chat
                "sent_to_doctor": bool(
                    (recipients.get("doctor_telegram_chat_id") and telegram_sent)
                    or (recipients.get("doctor_email") and email_sent)
                ),
                "email_sent": email_sent,
                "telegram_sent": telegram_sent,
            }
        )
        await emit(Outbound(t(language, "emergency_reply")))

    # ---------------------------------------------------------------------- texto libre

    async def _free_text(
        self, session: WhatsAppSession, profile: dict[str, Any], text: str, emit: Emit
    ) -> None:
        language = self._language(session)
        repository = self.deps.repository
        latest_prediction = None
        recent_vitals: list[dict[str, Any]] = []
        if wants_status_context(text):
            latest_prediction = await repository.get_latest_risk_prediction(str(profile["id"]))
        if wants_history_context(text):
            recent_vitals = await repository.get_recent_vital_signs(str(profile["id"]), limit=5)
        draft = build_carmen_free_text_response(text, profile, latest_prediction, recent_vitals, language)
        if _mentions_emergency(_normalize_text(text)):
            # Determinista, nunca pasa por el LLM; el botón reemplaza al comando /emergencia.
            await emit(Outbound(draft, (emergency_button(language),)))
            return
        if self.deps.voice is not None:
            draft = await self.deps.voice(
                "conversacion_libre",
                {
                    "idioma": language,
                    "mensaje_del_paciente": text,
                    "paciente": _first_name(profile),
                    "es_emergencia": False,
                },
                draft,
            )
        await emit(Outbound(draft))

    # -------------------------------------------------------------------------- pipeline

    async def _process_report(
        self,
        session: WhatsAppSession,
        profile: dict[str, Any],
        *,
        raw_message: str,
        vital_signs: dict[str, Any],
    ) -> dict[str, Any]:
        language = self._language(session)
        try:
            return await self.deps.nurse_agent.process_vital_report(
                {
                    "patient_id": str(profile["id"]),
                    "language": language,
                    "raw_message": raw_message,
                    "vital_signs": vital_signs,
                    "source": "whatsapp",
                }
            )
        except Exception:  # noqa: BLE001 - falla ruidosa en logs, respuesta segura al paciente
            logger.exception("WhatsApp: falló el pipeline del reporte del paciente %s", profile.get("id"))
            return {"final_response": tw(language, "report_failed")}

    # --------------------------------------------------------------------------- helpers

    async def _voiced(self, language: str, kind: str, draft: str) -> str:
        """Texto determinista en español: se traduce con la voz solo si el paciente eligió otro idioma."""
        if language == "es" or self.deps.voice is None:
            return draft
        return await self.deps.voice(kind, {"idioma": language}, draft)

    def _language(self, session: WhatsAppSession) -> str:
        """Elección explícita > perfil guardado > español (WhatsApp no manda language_code)."""
        if session.language:
            return normalize_language(session.language)
        profile = session.profile or {}
        return normalize_language(profile.get("language"))

    def _intake_context(self, session: WhatsAppSession) -> IntakeContext:
        return IntakeContext(
            language=self._language(session),
            first_name=_first_name(session.profile),
            voice=self.deps.voice,
        )

    async def _linked_profile(self, session: WhatsAppSession) -> dict[str, Any] | None:
        if session.profile:
            return session.profile
        profile = await self.deps.repository.find_profile_by_whatsapp_phone(session.wa_id)
        if profile:
            self._cache_profile(session, profile)
        return profile

    def _cache_profile(self, session: WhatsAppSession, profile: dict[str, Any]) -> None:
        session.profile = profile
        # El idioma guardado en el perfil manda, salvo que el paciente ya lo haya cambiado en esta sesión.
        if profile.get("language") and not session.language:
            session.language = normalize_language(profile["language"])

    async def _alert_recipients(self, patient_id: str) -> dict[str, Any]:
        repository = self.deps.repository
        if hasattr(repository, "get_alert_recipients"):
            return await repository.get_alert_recipients(patient_id)
        return {}
