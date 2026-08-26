import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents import nurse_voice
from agents.nurse_voice import compose_patient_message


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        if isinstance(self.reply, Exception):
            raise self.reply
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.reply))]
        )


FALLBACK = (
    "Nivel de riesgo: 🚨 CRÍTICO (90%). Diríjase a urgencias o llame al 123."
)


class NurseVoiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_without_api_key_returns_fallback(self):
        with patch.object(nurse_voice, "settings", SimpleNamespace(openai_api_key=None)):
            result = await compose_patient_message("chat", {}, "borrador")
        self.assertEqual(result, "borrador")

    async def test_rewrites_with_llm_when_available(self):
        client = FakeClient("¡Hola! 🌿 Tus signos se ven muy bien, sigue así 💚")
        with patch.object(nurse_voice, "settings", SimpleNamespace(openai_api_key="sk-test")):
            result = await compose_patient_message(
                "chat", {"risk_level": "low"}, "borrador plano", client=client
            )
        self.assertIn("🌿", result)

    async def test_critical_rewrite_must_keep_urgency(self):
        client = FakeClient("Tranquilo, todo va a estar bien 💚")
        with patch.object(nurse_voice, "settings", SimpleNamespace(openai_api_key="sk-test")):
            result = await compose_patient_message(
                "reporte", {"risk_level": "critical"}, FALLBACK, client=client
            )
        self.assertEqual(result, FALLBACK)

    async def test_critical_rewrite_with_urgency_is_accepted(self):
        client = FakeClient(
            "⚠️ Tus signos requieren atención URGENTE: ve a urgencias o llama al 123 ya mismo."
        )
        with patch.object(nurse_voice, "settings", SimpleNamespace(openai_api_key="sk-test")):
            result = await compose_patient_message(
                "reporte", {"risk_level": "critical"}, FALLBACK, client=client
            )
        self.assertIn("123", result)
        self.assertNotEqual(result, FALLBACK)

    async def test_empty_reply_returns_fallback(self):
        client = FakeClient("")
        with patch.object(nurse_voice, "settings", SimpleNamespace(openai_api_key="sk-test")):
            result = await compose_patient_message("chat", {}, "borrador", client=client)
        self.assertEqual(result, "borrador")

    async def test_client_error_returns_fallback(self):
        client = FakeClient(ValueError("boom"))
        with patch.object(nurse_voice, "settings", SimpleNamespace(openai_api_key="sk-test")):
            result = await compose_patient_message("chat", {}, "borrador", client=client)
        self.assertEqual(result, "borrador")


if __name__ == "__main__":
    unittest.main()
