import unittest
from types import SimpleNamespace
from unittest.mock import patch

from api.routes.telegram import resolve_webhook_url
from bot.handlers import (
    BotDependencies,
    build_raw_message_from_draft,
    format_latest_status_message,
    format_vital_history_message,
    help_message,
    looks_like_vital_report,
)
from bot.telegram_bot import build_application, send_monitoring_reminders
from bot.validators import parse_blood_pressure, parse_optional_number, parse_score
from notifications.email import build_risk_email_html
from notifications.telegram_alerts import build_telegram_alert_message


class FakeRepository:
    async def get_monitoring_patients(self):
        return [
            {"id": "patient-1", "full_name": "Ana Perez", "telegram_chat_id": 101, "role": "patient"},
            {"id": "patient-2", "full_name": "Luis Rojas", "telegram_chat_id": None, "role": "patient"},
        ]


class FakeNurseAgent:
    async def process_vital_report(self, payload):
        return {"final_response": "procesado", **payload}


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text):
        self.messages.append({"chat_id": chat_id, "text": text})


class FakeApplication:
    def __init__(self):
        self.bot = FakeBot()


class FakeUrl:
    def __init__(self, value):
        self.value = value
        self.netloc = value.split("//", 1)[1].split("/", 1)[0]


class FakeRequest:
    def __init__(self, host):
        self.url = FakeUrl(f"https://{host}/telegram/webhook/setup")

    def url_for(self, route_name):
        if route_name != "telegram_webhook":
            raise KeyError(route_name)
        return f"https://{self.url.netloc}/webhook"


class BotSprint4Test(unittest.IsolatedAsyncioTestCase):
    def test_validators_parse_expected_values(self):
        self.assertEqual(parse_blood_pressure("120/80"), (120, 80))
        self.assertEqual(parse_optional_number("no medí", label="glucosa", minimum=20, maximum=600), None)
        self.assertEqual(parse_score("4", label="dolor"), 4)
        with self.assertRaises(ValueError):
            parse_blood_pressure("80/120")

    def test_formatters_and_free_text_detection(self):
        self.assertIn("/vitales", help_message())
        status = format_latest_status_message(
            {
                "risk_level": "high",
                "risk_probability": 0.82,
                "model_used": "lightgbm",
                "predicted_at": "2026-05-26T10:00:00Z",
            }
        )
        self.assertIn("ALTO", status)
        history = format_vital_history_message(
            [
                {
                    "recorded_at": "2026-05-26T10:00:00Z",
                    "systolic_bp": 120,
                    "diastolic_bp": 80,
                    "heart_rate": 75,
                }
            ]
        )
        self.assertIn("120/80", history)
        self.assertTrue(looks_like_vital_report("Presión 130/85, pulso 80"))

    def test_build_raw_message_from_guided_draft(self):
        raw_message = build_raw_message_from_draft(
            {
                "systolic_bp": 130,
                "diastolic_bp": 82,
                "heart_rate": 78,
                "oxygen_saturation": 97,
                "glucose": 115,
                "pain_score": 1,
                "dizziness_score": 0,
                "dyspnea_score": 0,
            }
        )
        self.assertIn("Presión 130/82", raw_message)
        self.assertIn("dificultad para respirar 0", raw_message)

    def test_build_application_registers_handlers(self):
        app = build_application(
            token="123456:ABCDEF",
            dependencies=BotDependencies(repository=FakeRepository(), nurse_agent=FakeNurseAgent()),
        )
        handler_count = sum(len(group) for group in app.handlers.values())
        self.assertGreaterEqual(handler_count, 7)

    async def test_monitoring_reminders_send_only_linked_patients(self):
        app = FakeApplication()
        sent = await send_monitoring_reminders(app, FakeRepository())
        self.assertEqual(sent, 1)
        self.assertEqual(app.bot.messages[0]["chat_id"], 101)
        self.assertIn("/vitales", app.bot.messages[0]["text"])

    def test_notification_templates_include_critical_context(self):
        payload = {
            "patient_id": "patient-1",
            "patient_name": "Ana Perez",
            "risk_level": "critical",
            "vital_signs": {"systolic_bp": 190, "diastolic_bp": 100},
            "recommendations": "Contactar de inmediato.",
        }
        self.assertIn("123 Colombia", build_risk_email_html(payload))
        self.assertIn("Alerta", build_telegram_alert_message(payload))

    def test_webhook_setup_prefers_current_railway_host_when_config_is_stale(self):
        request = FakeRequest("homecare-production-3065.up.railway.app")
        stale_settings = SimpleNamespace(telegram_webhook_url="https://homecare-ccv.up.railway.app/webhook")
        with patch("api.routes.telegram.settings", stale_settings):
            self.assertEqual(
                resolve_webhook_url(request),
                "https://homecare-production-3065.up.railway.app/webhook",
            )

    def test_webhook_setup_keeps_custom_configured_domain(self):
        request = FakeRequest("homecare-production-3065.up.railway.app")
        custom_settings = SimpleNamespace(telegram_webhook_url="https://api.homecareccv.co/webhook")
        with patch("api.routes.telegram.settings", custom_settings):
            self.assertEqual(resolve_webhook_url(request), "https://api.homecareccv.co/webhook")


if __name__ == "__main__":
    unittest.main()
