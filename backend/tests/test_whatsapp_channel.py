"""Canal WhatsApp: parseo del webhook, firma, motor de intake, conversación, servicio y rutas.

Todo con fakes: sin red, sin Supabase, sin OpenAI. Telegram no se toca."""
import hashlib
import hmac
import json
import sys
import unittest
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.state import HomecareAgentState
from api.routes.whatsapp import router as whatsapp_router
from bot.i18n import CHOOSE_LANGUAGE, LANGUAGE_NOT_UNDERSTOOD, t
from channels import intake
from channels.intake import IntakeContext, advance_intake, start_intake
from channels.messages import Outbound
from channels.whatsapp.client import WhatsAppClient, split_text
from channels.whatsapp.conversation import (
    LANGUAGE_BUTTONS,
    WhatsAppConversation,
    WhatsAppDependencies,
    parse_command,
    tw,
)
from channels.whatsapp.service import WhatsAppService
from channels.whatsapp.session import INTAKE_TTL, InMemorySessionStore, WhatsAppSession, utcnow
from channels.whatsapp.webhook import InboundMessage, parse_webhook_payload, verify_signature


WA_ID = "573001112233"
DOCTORS = [
    {"id": "doc-pablo", "full_name": "Pablo Benjumea", "telegram_chat_id": 111, "role": "ips"},
    {"id": "doc-juan", "full_name": "Juan Camilo Arias", "telegram_chat_id": 222, "role": "ips"},
]
PATIENT = {"id": "patient-1", "full_name": "Ana María Pérez", "role": "patient", "whatsapp_phone": WA_ID}


def text_payload(body, wa_id=WA_ID, message_id="wamid.1", name="Ana"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "1555", "phone_number_id": "PNID"},
                            "contacts": [{"profile": {"name": name}, "wa_id": wa_id}],
                            "messages": [
                                {
                                    "from": wa_id,
                                    "id": message_id,
                                    "timestamp": "1757400000",
                                    "type": "text",
                                    "text": {"body": body},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def inbound(text, *, button_id=None, kind="text", message_id="wamid.x", wa_id=WA_ID):
    return InboundMessage(wa_id=wa_id, message_id=message_id, kind=kind, text=text, button_id=button_id)


class FakeRepository:
    def __init__(self, profiles_by_phone=None, known_documents=None):
        self.profiles_by_phone = dict(profiles_by_phone or {})
        self.known_documents = dict(known_documents or {})
        self.created = []
        self.saved_languages = []
        self.alerts = []
        self.linked = []

    async def find_profile_by_whatsapp_phone(self, phone):
        return self.profiles_by_phone.get(phone)

    async def link_whatsapp_account(self, document_id, phone):
        profile = self.known_documents.get(document_id)
        if not profile:
            return None
        linked = {**profile, "whatsapp_phone": phone}
        self.profiles_by_phone[phone] = linked
        self.linked.append((document_id, phone))
        return linked

    async def update_profile_language(self, profile_id, language):
        self.saved_languages.append((profile_id, language))
        return True

    async def get_doctor_roster(self):
        return list(DOCTORS)

    async def count_assigned_patients(self, doctor_id):
        return 0

    async def create_patient_account(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "patient-new", "role": "patient", **kwargs}

    async def get_latest_risk_prediction(self, patient_id):
        return {
            "risk_level": "low",
            "risk_probability": 0.12,
            "model_used": "lightgbm",
            "predicted_at": "2026-09-09T10:00:00Z",
        }

    async def get_recent_vital_signs(self, patient_id, limit=5):
        return [{"recorded_at": "2026-09-09T06:00:00Z", "systolic_bp": 120, "diastolic_bp": 80, "heart_rate": 75}]

    async def get_alert_recipients(self, patient_id):
        return {
            "patient": PATIENT,
            "doctor": DOCTORS[0],
            "patient_telegram_chat_id": None,
            "doctor_telegram_chat_id": 111,
            "doctor_email": "pablo@example.com",
        }

    async def save_alert(self, payload):
        self.alerts.append(payload)
        return "alert-1"


class FakeNurseAgent:
    def __init__(self, response="procesado"):
        self.calls = []
        self.response = response

    async def process_vital_report(self, payload):
        self.calls.append(payload)
        return {**payload, "final_response": self.response}


class FailingNurseAgent:
    async def process_vital_report(self, payload):
        raise RuntimeError("supabase caído")


class Collector:
    def __init__(self):
        self.sent = []

    async def __call__(self, outbound):
        self.sent.append(outbound)

    @property
    def texts(self):
        return [item.text for item in self.sent]

    @property
    def last(self):
        return self.sent[-1]


class FakeClient:
    def __init__(self):
        self.sent = []
        self.read = []

    async def send(self, to, outbound):
        self.sent.append((to, outbound))
        return True

    async def mark_read(self, message_id):
        self.read.append(message_id)
        return True


def make_conversation(repository=None, agent=None, voice=None):
    return WhatsAppConversation(
        WhatsAppDependencies(
            repository=repository if repository is not None else FakeRepository(),
            nurse_agent=agent if agent is not None else FakeNurseAgent(),
            voice=voice,
        )
    )


async def _true(*args, **kwargs):
    return True


class WebhookParsingTest(unittest.TestCase):
    def test_parses_text_message_with_contact_name(self):
        messages = parse_webhook_payload(text_payload("hola", name="Ana"))
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(message.kind, "text")
        self.assertEqual(message.text, "hola")
        self.assertEqual(message.wa_id, WA_ID)
        self.assertEqual(message.message_id, "wamid.1")
        self.assertEqual(message.profile_name, "Ana")
        self.assertEqual(message.phone_number_id, "PNID")

    def test_parses_button_reply(self):
        payload = text_payload("ignored")
        payload["entry"][0]["changes"][0]["value"]["messages"] = [
            {
                "from": WA_ID,
                "id": "wamid.btn",
                "type": "interactive",
                "interactive": {"type": "button_reply", "button_reply": {"id": "lang:en", "title": "English 🇬🇧"}},
            }
        ]
        message = parse_webhook_payload(payload)[0]
        self.assertEqual(message.kind, "button")
        self.assertEqual(message.button_id, "lang:en")
        self.assertEqual(message.text, "English 🇬🇧")

    def test_status_updates_and_foreign_objects_are_ignored(self):
        payload = text_payload("x")
        value = payload["entry"][0]["changes"][0]["value"]
        del value["messages"]
        value["statuses"] = [{"id": "wamid.1", "status": "delivered", "recipient_id": WA_ID}]
        self.assertEqual(parse_webhook_payload(payload), [])
        self.assertEqual(parse_webhook_payload({"object": "page", "entry": []}), [])
        self.assertEqual(parse_webhook_payload(None), [])

    def test_unsupported_types_are_flagged_not_dropped(self):
        payload = text_payload("x")
        payload["entry"][0]["changes"][0]["value"]["messages"] = [
            {"from": WA_ID, "id": "wamid.audio", "type": "audio", "audio": {"id": "media-1"}}
        ]
        message = parse_webhook_payload(payload)[0]
        self.assertEqual(message.kind, "unsupported")
        self.assertEqual(message.raw_type, "audio")


class SignatureTest(unittest.TestCase):
    def test_signature_roundtrip(self):
        body = b'{"object":"whatsapp_business_account"}'
        digest = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_signature("secret", body, f"sha256={digest}"))
        self.assertFalse(verify_signature("secret", body, "sha256=" + "0" * 64))
        self.assertFalse(verify_signature("otro", body, f"sha256={digest}"))
        self.assertFalse(verify_signature("secret", body, f"md5={digest}"))
        self.assertFalse(verify_signature("secret", body, None))
        self.assertFalse(verify_signature(None, body, f"sha256={digest}"))


class IntakeEngineTest(unittest.IsolatedAsyncioTestCase):
    async def test_happy_path_collects_all_fields_without_llm(self):
        ctx = IntakeContext(language="es", first_name="Ana")
        draft = {}
        started = await start_intake(ctx)
        self.assertEqual(started.next_step, intake.CONFIRM_TENSIOMETER)
        self.assertIn("tensiómetro", started.replies[0].text)
        self.assertEqual(started.replies[0].buttons, (("yes", "Sí"), ("no", "No")))

        answers = ["sí", "8", "75", "97", "120/80", "36.8", "68.5", "no medí", "0", "1", "0"]
        step = started.next_step
        result = None
        for answer in answers:
            result = await advance_intake(ctx, step, draft, answer)
            step = result.next_step
        self.assertTrue(result.completed)
        self.assertIsNone(result.next_step)
        self.assertEqual(
            draft,
            {
                "respiratory_rate": 16,
                "heart_rate": 75,
                "oxygen_saturation": 97,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "temperature": 36.8,
                "weight_kg": 68.5,
                "pain_score": 0,
                "dizziness_score": 1,
                "dyspnea_score": 0,
            },
        )

    async def test_no_tensiometer_aborts_and_unclear_answer_retries(self):
        ctx = IntakeContext()
        unclear = await advance_intake(ctx, intake.CONFIRM_TENSIOMETER, {}, "quizás")
        self.assertEqual(unclear.next_step, intake.CONFIRM_TENSIOMETER)
        self.assertEqual(unclear.replies[0].buttons, (("yes", "Sí"), ("no", "No")))
        aborted = await advance_intake(ctx, intake.CONFIRM_TENSIOMETER, {}, "no")
        self.assertTrue(aborted.aborted)
        self.assertIsNone(aborted.next_step)

    async def test_invalid_pressure_stays_on_step(self):
        ctx = IntakeContext()
        draft = {}
        result = await advance_intake(ctx, intake.BLOOD_PRESSURE, draft, "80/120")
        self.assertEqual(result.next_step, intake.BLOOD_PRESSURE)
        self.assertIn("sistólica", result.replies[0].text)
        self.assertEqual(draft, {})

    async def test_safety_warnings_are_deterministic_and_bypass_voice(self):
        async def voice(kind, payload, fallback):
            return "VOZ: " + fallback

        ctx = IntakeContext(language="es", voice=voice)
        draft = {}
        oxygen = await advance_intake(ctx, intake.OXYGEN, draft, "85")
        self.assertEqual(oxygen.next_step, intake.BLOOD_PRESSURE)
        self.assertEqual(draft["oxygen_saturation"], 85)
        self.assertNotIn("VOZ:", oxygen.replies[0].text)
        self.assertIn("123", oxygen.replies[0].text)

        respiratory = await advance_intake(ctx, intake.RESPIRATORY_RATE, draft, "16")
        self.assertEqual(draft["respiratory_rate"], 32)
        self.assertNotIn("VOZ:", respiratory.replies[0].text)
        self.assertIn("32", respiratory.replies[0].text)

        normal = await advance_intake(ctx, intake.HEART_RATE, draft, "70")
        self.assertTrue(normal.replies[0].text.startswith("VOZ:"))

    async def test_unknown_step_is_loud(self):
        with self.assertRaises(ValueError):
            await advance_intake(IntakeContext(), "no_existe", {}, "1")


class CommandParsingTest(unittest.TestCase):
    def test_words_slash_commands_and_buttons(self):
        self.assertEqual(parse_command("/vitales"), ("vitals", ""))
        self.assertEqual(parse_command("  Vitales "), ("vitals", ""))
        self.assertEqual(parse_command("Registrar signos"), ("vitals", ""))
        self.assertEqual(parse_command("menú"), ("help", ""))
        self.assertEqual(parse_command("/idioma en"), ("language", "en"))
        self.assertEqual(parse_command("Sí", button_id="yes"), (None, ""))
        self.assertEqual(parse_command("Español 🇨🇴", button_id="lang:es"), ("language", "es"))
        self.assertEqual(parse_command("Registrar signos", button_id="vitals"), ("vitals", ""))
        self.assertEqual(parse_command("me siento mal"), (None, ""))
        self.assertEqual(parse_command("mi estado de ánimo"), (None, ""))


class ConversationTest(unittest.IsolatedAsyncioTestCase):
    async def test_first_contact_asks_language_then_document_then_registers(self):
        repository = FakeRepository()
        conversation = make_conversation(repository)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()

        await conversation.handle(session, inbound("hola"), out)
        self.assertEqual(out.last.text, CHOOSE_LANGUAGE)
        self.assertEqual(out.last.buttons, LANGUAGE_BUTTONS)
        self.assertTrue(session.awaiting_language)

        await conversation.handle(session, inbound("Español 🇨🇴", button_id="lang:es"), out)
        self.assertFalse(session.awaiting_language)
        self.assertTrue(session.awaiting_document)
        self.assertEqual(session.language, "es")
        self.assertIn(t("es", "ask_document"), out.last.text)

        await conversation.handle(session, inbound("1002652750"), out)
        self.assertTrue(session.awaiting_registration_name)
        self.assertEqual(session.registration_document, "1002652750")
        self.assertEqual(out.last.text, t("es", "doc_unknown_offer_registration"))

        with patch("bot.handlers.send_telegram_message", _true) as _:
            await conversation.handle(session, inbound("Me llamo Ana María Pérez"), out)
        self.assertEqual(len(repository.created), 1)
        created = repository.created[0]
        self.assertEqual(created["whatsapp_phone"], WA_ID)
        self.assertEqual(created["full_name"], "Ana María Pérez")
        self.assertEqual(created["document_id"], "1002652750")
        self.assertNotIn("telegram_chat_id", created)
        self.assertIn("Pablo Benjumea", out.last.text)
        self.assertEqual(out.last.buttons, (("vitals", "Registrar signos"),))
        self.assertFalse(session.awaiting_registration_name)
        self.assertEqual(session.profile["id"], "patient-new")
        self.assertIn(("patient-new", "es"), repository.saved_languages)

    async def test_known_document_links_whatsapp(self):
        repository = FakeRepository(known_documents={"cc123456": {"id": "p-9", "full_name": "Luis Rojas", "role": "patient"}})
        conversation = make_conversation(repository)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("cc123456"), out)
        self.assertEqual(repository.linked, [("cc123456", WA_ID)])
        self.assertEqual(out.last.text, tw("es", "linked_ok", name="Luis Rojas"))
        self.assertEqual(session.profile["whatsapp_phone"], WA_ID)

    async def test_language_choice_by_text_and_not_understood(self):
        conversation = make_conversation()
        session = WhatsAppSession(wa_id=WA_ID, awaiting_language=True)
        out = Collector()
        await conversation.handle(session, inbound("qué?"), out)
        self.assertEqual(out.last.text, LANGUAGE_NOT_UNDERSTOOD)
        self.assertTrue(session.awaiting_language)
        await conversation.handle(session, inbound("english"), out)
        self.assertEqual(session.language, "en")
        self.assertIn(t("en", "ask_document"), out.last.text)

    async def test_linked_patient_runs_full_intake_through_pipeline(self):
        repository = FakeRepository(profiles_by_phone={WA_ID: PATIENT})
        agent = FakeNurseAgent(response="Listo, riesgo bajo.")
        conversation = make_conversation(repository, agent)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()

        await conversation.handle(session, inbound("vitales"), out)
        self.assertEqual(session.intake_step, intake.CONFIRM_TENSIOMETER)
        self.assertIn("Ana", out.last.text)
        self.assertEqual(out.last.buttons, (("yes", "Sí"), ("no", "No")))

        answers = [
            ("Sí", "yes"), ("7", None), ("72", None), ("96", None), ("118/76", None),
            ("no medí", None), ("no medí", None), ("110", None), ("0", None), ("0", None),
        ]
        for text, button_id in answers:
            await conversation.handle(session, inbound(text, button_id=button_id), out)
        self.assertEqual(session.intake_step, intake.DYSPNEA)
        self.assertEqual(agent.calls, [])

        await conversation.handle(session, inbound("2"), out)
        self.assertIsNone(session.intake_step)
        self.assertEqual(session.vitals_draft, {})
        self.assertEqual(len(agent.calls), 1)
        call = agent.calls[0]
        self.assertEqual(call["source"], "whatsapp")
        self.assertEqual(call["patient_id"], "patient-1")
        self.assertEqual(call["language"], "es")
        self.assertEqual(call["vital_signs"]["systolic_bp"], 118)
        self.assertEqual(call["vital_signs"]["respiratory_rate"], 14)
        self.assertEqual(call["vital_signs"]["glucose"], 110)
        self.assertEqual(call["vital_signs"]["dyspnea_score"], 2)
        self.assertIn("Presión 118/76", call["raw_message"])
        self.assertEqual(out.texts[-2], t("es", "analyzing"))
        self.assertEqual(out.texts[-1], "Listo, riesgo bajo.")

    async def test_free_text_vitals_go_straight_to_pipeline(self):
        repository = FakeRepository(profiles_by_phone={WA_ID: PATIENT})
        agent = FakeNurseAgent()
        conversation = make_conversation(repository, agent)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("presión 130/85, pulso 80"), out)
        self.assertEqual(len(agent.calls), 1)
        self.assertEqual(agent.calls[0]["raw_message"], "presión 130/85, pulso 80")
        self.assertEqual(agent.calls[0]["source"], "whatsapp")
        self.assertEqual(out.texts, [t("es", "analyzing_free_text"), "procesado"])

    async def test_pipeline_failure_is_loud_in_logs_and_safe_for_patient(self):
        repository = FakeRepository(profiles_by_phone={WA_ID: PATIENT})
        conversation = make_conversation(repository, FailingNurseAgent())
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        with self.assertLogs("channels.whatsapp.conversation", level="ERROR"):
            await conversation.handle(session, inbound("presión 130/85, pulso 80"), out)
        self.assertEqual(out.last.text, tw("es", "report_failed"))
        self.assertIn("123", out.last.text)

    async def test_emergency_phrase_gets_deterministic_reply_with_button_then_alerts(self):
        async def voice(kind, payload, fallback):
            raise AssertionError("la emergencia no debe pasar por la voz LLM")

        repository = FakeRepository(profiles_by_phone={WA_ID: PATIENT})
        conversation = make_conversation(repository, voice=voice)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("me ahogo y tengo dolor en el pecho"), out)
        self.assertIn("llama al 123", out.last.text)
        self.assertEqual(out.last.buttons, (("emergency", "🚨 Avisar al equipo"),))

        with patch("channels.whatsapp.conversation.send_telegram_risk_alert", _true), patch(
            "channels.whatsapp.conversation.send_risk_email_alert", _true
        ):
            await conversation.handle(session, inbound("🚨 Avisar al equipo", button_id="emergency"), out)
        self.assertEqual(len(repository.alerts), 1)
        alert = repository.alerts[0]
        self.assertEqual(alert["risk_level"], "critical")
        self.assertIn("WhatsApp", alert["message"])
        self.assertTrue(alert["sent_to_doctor"])
        self.assertEqual(out.last.text, t("es", "emergency_reply"))

    async def test_emergency_for_unknown_user_does_not_hide_behind_language_menu(self):
        conversation = make_conversation()
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("no puedo respirar"), out)
        self.assertIn("llama al 123", out.last.text)
        self.assertFalse(session.awaiting_language)

    async def test_status_history_help_and_cancel(self):
        repository = FakeRepository(profiles_by_phone={WA_ID: PATIENT})
        conversation = make_conversation(repository)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("estado"), out)
        self.assertIn("BAJO", out.last.text)
        await conversation.handle(session, inbound("historial"), out)
        self.assertIn("120/80", out.last.text)
        await conversation.handle(session, inbound("ayuda"), out)
        self.assertEqual(out.last.text, tw("es", "help"))
        self.assertEqual(out.last.buttons, (("vitals", "Registrar signos"),))

        await conversation.handle(session, inbound("vitales"), out)
        self.assertIsNotNone(session.intake_step)
        await conversation.handle(session, inbound("cancelar"), out)
        self.assertIsNone(session.intake_step)
        self.assertEqual(out.last.text, t("es", "cancelled"))

    async def test_free_text_uses_voice_in_patient_language(self):
        calls = []

        async def voice(kind, payload, fallback):
            calls.append((kind, payload))
            return "voz"

        profile = {**PATIENT, "language": "en"}
        repository = FakeRepository(profiles_by_phone={WA_ID: profile})
        conversation = make_conversation(repository, voice=voice)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("I feel a bit tired today"), out)
        self.assertEqual(out.last.text, "voz")
        self.assertEqual(calls[0][0], "conversacion_libre")
        self.assertEqual(calls[0][1]["idioma"], "en")
        self.assertEqual(session.language, "en")

    async def test_unsupported_media_gets_a_text_only_hint(self):
        conversation = make_conversation(FakeRepository(profiles_by_phone={WA_ID: PATIENT}))
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("", kind="unsupported"), out)
        self.assertEqual(out.last.text, tw("es", "unsupported"))

    async def test_stale_intake_expires(self):
        repository = FakeRepository(profiles_by_phone={WA_ID: PATIENT})
        conversation = make_conversation(repository)
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("vitales"), out)
        session.intake_started_at = utcnow() - INTAKE_TTL - timedelta(minutes=1)
        await conversation.handle(session, inbound("hola"), out)
        self.assertIsNone(session.intake_step)
        self.assertIn("Soy Carmen", out.last.text)

    async def test_only_patients_can_report(self):
        doctor = {"id": "doc-pablo", "full_name": "Pablo Benjumea", "role": "ips"}
        conversation = make_conversation(FakeRepository(profiles_by_phone={WA_ID: doctor}))
        session = WhatsAppSession(wa_id=WA_ID)
        out = Collector()
        await conversation.handle(session, inbound("vitales"), out)
        self.assertEqual(out.last.text, t("es", "only_patients"))
        self.assertIsNone(session.intake_step)


class ServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_deduplicates_retried_webhooks(self):
        service = WhatsAppService(conversation=make_conversation(), client=FakeClient())
        first = service.accept_payload(text_payload("hola", message_id="wamid.dup"))
        second = service.accept_payload(text_payload("hola", message_id="wamid.dup"))
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])

    async def test_handle_message_marks_read_sends_and_persists_session(self):
        client = FakeClient()
        store = InMemorySessionStore()
        service = WhatsAppService(conversation=make_conversation(), client=client, store=store)
        await service.handle_message(inbound("hola", message_id="wamid.7"))
        self.assertEqual(client.read, ["wamid.7"])
        self.assertEqual(client.sent[0][0], WA_ID)
        self.assertEqual(client.sent[0][1].text, CHOOSE_LANGUAGE)
        session = await store.get(WA_ID)
        self.assertTrue(session.awaiting_language)

    async def test_conversation_crash_is_logged_and_patient_gets_safe_message(self):
        class Broken:
            async def handle(self, session, inbound, emit):
                raise RuntimeError("boom")

        client = FakeClient()
        service = WhatsAppService(conversation=Broken(), client=client)
        with self.assertLogs("channels.whatsapp.service", level="ERROR"):
            await service.handle_message(inbound("hola"))
        self.assertEqual(client.sent[-1][1].text, tw("es", "generic_failed"))


class ClientTest(unittest.IsolatedAsyncioTestCase):
    class FakeHttp:
        def __init__(self, status=200):
            self.posts = []
            self.status = status

        async def post(self, url, json=None, headers=None):
            self.posts.append((url, json, headers))
            return SimpleNamespace(status_code=self.status, text="")

    async def test_text_and_button_payloads(self):
        http = self.FakeHttp()
        client = WhatsAppClient(access_token="tok", phone_number_id="PNID", api_version="v25.0", http_client=http)
        self.assertTrue(await client.send(WA_ID, Outbound("hola")))
        self.assertTrue(
            await client.send(WA_ID, Outbound("¿Tensiómetro?", (("yes", "Sí"), ("no", "No"), ("x", "y" * 30), ("extra", "no cabe"))))
        )
        url, text_payload_sent, headers = http.posts[0]
        self.assertEqual(url, "https://graph.facebook.com/v25.0/PNID/messages")
        self.assertEqual(headers["Authorization"], "Bearer tok")
        self.assertEqual(text_payload_sent["type"], "text")
        self.assertEqual(text_payload_sent["text"]["body"], "hola")
        buttons = http.posts[1][1]["interactive"]["action"]["buttons"]
        self.assertEqual(len(buttons), 3)
        self.assertEqual(buttons[0]["reply"], {"id": "yes", "title": "Sí"})
        self.assertEqual(len(buttons[2]["reply"]["title"]), 20)

    async def test_long_text_is_chunked_and_4xx_is_not_retried(self):
        http = self.FakeHttp()
        client = WhatsAppClient(access_token="tok", phone_number_id="PNID", http_client=http)
        await client.send_text(WA_ID, "línea\n" * 1000)
        self.assertGreater(len(http.posts), 1)
        self.assertTrue(all(len(post[1]["text"]["body"]) <= 4096 for post in http.posts))

        failing = self.FakeHttp(status=400)
        client = WhatsAppClient(access_token="tok", phone_number_id="PNID", http_client=failing, attempts=3)
        with self.assertLogs("channels.whatsapp.client", level="WARNING"):
            self.assertFalse(await client.send_text(WA_ID, "x"))
        self.assertEqual(len(failing.posts), 1)

    def test_split_text_respects_limit(self):
        chunks = split_text("a" * 10 + "\n" + "b" * 10, 12)
        self.assertEqual(chunks, ["a" * 10 + "\n", "b" * 10])
        self.assertEqual(split_text("corto", 100), ["corto"])


def _signed(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class RouteTest(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(whatsapp_router)
        self.http = TestClient(app)
        self.route_settings = SimpleNamespace(whatsapp_verify_token="verify-me", whatsapp_app_secret="s3cret")
        self.service_settings = SimpleNamespace(whatsapp_access_token="tok", whatsapp_phone_number_id="PNID")

    def test_verification_handshake(self):
        with patch("api.routes.whatsapp.settings", self.route_settings):
            ok = self.http.get(
                "/whatsapp/webhook",
                params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "12345"},
            )
            self.assertEqual(ok.status_code, 200)
            self.assertEqual(ok.text, "12345")
            bad = self.http.get(
                "/whatsapp/webhook",
                params={"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "1"},
            )
            self.assertEqual(bad.status_code, 403)
        with patch("api.routes.whatsapp.settings", SimpleNamespace(whatsapp_verify_token=None, whatsapp_app_secret=None)):
            unconfigured = self.http.get("/whatsapp/webhook", params={"hub.mode": "subscribe"})
            self.assertEqual(unconfigured.status_code, 503)

    def test_post_without_configuration_is_503(self):
        with patch("api.routes.whatsapp.settings", self.route_settings), patch(
            "channels.whatsapp.service.settings",
            SimpleNamespace(whatsapp_access_token=None, whatsapp_phone_number_id=None),
        ):
            response = self.http.post("/whatsapp/webhook", content=b"{}")
        self.assertEqual(response.status_code, 503)

    def test_post_rejects_bad_signature_and_processes_good_one(self):
        client = FakeClient()
        service = WhatsAppService(conversation=make_conversation(), client=client)
        body = json.dumps(text_payload("hola", message_id="wamid.route")).encode()
        with patch("api.routes.whatsapp.settings", self.route_settings), patch(
            "channels.whatsapp.service.settings", self.service_settings
        ), patch("channels.whatsapp.service._SERVICE", service):
            rejected = self.http.post(
                "/whatsapp/webhook", content=body, headers={"X-Hub-Signature-256": "sha256=deadbeef"}
            )
            self.assertEqual(rejected.status_code, 403)
            self.assertEqual(client.sent, [])

            accepted = self.http.post(
                "/whatsapp/webhook", content=body, headers={"X-Hub-Signature-256": _signed(body, "s3cret")}
            )
            self.assertEqual(accepted.status_code, 200)
            self.assertEqual(accepted.json(), {"ok": True, "queued": 1})
            # BackgroundTasks corre dentro del ciclo del TestClient: la respuesta ya salió.
            self.assertEqual(client.sent[0][1].text, CHOOSE_LANGUAGE)

            duplicate = self.http.post(
                "/whatsapp/webhook", content=body, headers={"X-Hub-Signature-256": _signed(body, "s3cret")}
            )
            self.assertEqual(duplicate.json(), {"ok": True, "queued": 0})


class AgentStateTest(unittest.TestCase):
    def test_source_is_declared_so_langgraph_keeps_it(self):
        self.assertIn("source", HomecareAgentState.__annotations__)


if __name__ == "__main__":
    unittest.main()
