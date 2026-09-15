"""Carmen bilingüe (es/en): detección por language_code, confirmación en el saludo,
/idioma, voz en inglés y guardas de seguridad en ambos idiomas."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents import nurse_voice
from agents.nurse_voice import _loses_urgency, compose_patient_message
from bot.handlers import (
    BotDependencies,
    _mentions_emergency,
    _normalize_text,
    _speak,
    build_carmen_free_text_response,
    document_or_free_text_message,
    help_message,
    language_callback,
    language_command,
    start_command,
)
from bot.i18n import CHOOSE_LANGUAGE, language_from_telegram, parse_language_choice, t
from bot.telegram_bot import send_monitoring_reminders
from bot.validators import is_affirmative, is_negative, is_skip_value


class FakeRepository:
    def __init__(self, profiles_by_chat=None):
        self.profiles_by_chat = profiles_by_chat or {}
        self.saved_languages = []

    async def find_profile_by_telegram_chat_id(self, chat_id):
        return self.profiles_by_chat.get(chat_id)

    async def update_profile_language(self, profile_id, language):
        self.saved_languages.append((profile_id, language))
        return True

    async def link_telegram_account(self, document_id, chat_id):
        return None

    async def get_monitoring_patients(self):
        return [
            {"id": "p-en", "full_name": "Ana Perez", "telegram_chat_id": 101, "role": "patient", "language": "en"},
            {"id": "p-es", "full_name": "Luis Rojas", "telegram_chat_id": 102, "role": "patient"},
        ]


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.replies = []
        self.kwargs = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)
        self.kwargs.append(kwargs)


async def _noop():
    return None


def make_update(text="", chat_id=999, language_code=None, callback_data=None):
    query = SimpleNamespace(data=callback_data, answer=_noop) if callback_data else None
    return SimpleNamespace(
        effective_message=FakeMessage(text),
        effective_chat=SimpleNamespace(id=chat_id),
        effective_user=SimpleNamespace(language_code=language_code),
        callback_query=query,
    )


def make_context(deps, user_data=None, args=None):
    return SimpleNamespace(
        user_data=user_data if user_data is not None else {},
        application=SimpleNamespace(bot_data={"homecare_dependencies": deps}),
        args=args or [],
    )


class LanguageResolutionTest(unittest.TestCase):
    def test_telegram_language_code_maps_to_supported_language(self):
        self.assertEqual(language_from_telegram("en"), "en")
        self.assertEqual(language_from_telegram("en-GB"), "en")
        self.assertEqual(language_from_telegram("es-CO"), "es")
        self.assertEqual(language_from_telegram("fr"), "es")
        self.assertEqual(language_from_telegram(None), "es")

    def test_language_choice_parsing(self):
        self.assertEqual(parse_language_choice("English 🇬🇧"), "en")
        self.assertEqual(parse_language_choice("inglés"), "en")
        self.assertEqual(parse_language_choice("Español 🇨🇴"), "es")
        self.assertEqual(parse_language_choice("spanish"), "es")
        self.assertIsNone(parse_language_choice("hola"))

    def test_catalog_has_both_languages_and_help_lists_idioma(self):
        self.assertIn("/idioma", help_message("es"))
        self.assertIn("/idioma", help_message("en"))
        self.assertIn("commands", help_message("en").lower())


class GreetingAndLanguageFlowTest(unittest.IsolatedAsyncioTestCase):
    async def test_new_user_gets_bilingual_greeting_with_buttons(self):
        deps = BotDependencies(repository=FakeRepository(), nurse_agent=None)
        context = make_context(deps)
        update = make_update("/start", language_code="en")
        await start_command(update, context)
        self.assertEqual(update.effective_message.replies, [CHOOSE_LANGUAGE])
        self.assertIn("reply_markup", update.effective_message.kwargs[0])
        self.assertTrue(context.user_data["awaiting_language"])
        self.assertEqual(context.user_data["language"], "en")

    async def test_typed_choice_sets_language_and_asks_for_document(self):
        deps = BotDependencies(repository=FakeRepository(), nurse_agent=None)
        context = make_context(deps, {"awaiting_language": True, "language": "es"})
        update = make_update("English")
        await document_or_free_text_message(update, context)
        self.assertEqual(context.user_data["language"], "en")
        self.assertNotIn("awaiting_language", context.user_data)
        self.assertTrue(context.user_data["awaiting_document"])
        self.assertIn("document", update.effective_message.replies[0])
        self.assertIn(t("en", "language_set"), update.effective_message.replies[0])

    async def test_unrecognized_choice_reprompts_bilingually(self):
        deps = BotDependencies(repository=FakeRepository(), nurse_agent=None)
        context = make_context(deps, {"awaiting_language": True})
        update = make_update("hola")
        await document_or_free_text_message(update, context)
        self.assertTrue(context.user_data["awaiting_language"])
        self.assertIn("english", update.effective_message.replies[0].lower())

    async def test_button_choice_persists_for_linked_patient(self):
        repo = FakeRepository({999: {"id": "p1", "full_name": "Ana Perez", "role": "patient"}})
        deps = BotDependencies(repository=repo, nurse_agent=None)
        context = make_context(deps)
        update = make_update(callback_data="lang:en")
        await language_callback(update, context)
        self.assertEqual(repo.saved_languages, [("p1", "en")])
        self.assertEqual(context.user_data["language"], "en")
        self.assertEqual(update.effective_message.replies, [t("en", "language_set")])

    async def test_idioma_command_shows_selector_and_accepts_inline_argument(self):
        repo = FakeRepository({999: {"id": "p1", "full_name": "Ana Perez", "role": "patient"}})
        deps = BotDependencies(repository=repo, nurse_agent=None)
        context = make_context(deps)
        update = make_update("/idioma")
        await language_command(update, context)
        self.assertTrue(context.user_data["awaiting_language"])
        self.assertEqual(update.effective_message.replies[0], CHOOSE_LANGUAGE)

        context = make_context(deps, args=["en"])
        update = make_update("/idioma en")
        await language_command(update, context)
        self.assertEqual(repo.saved_languages[-1], ("p1", "en"))
        self.assertEqual(update.effective_message.replies, [t("en", "language_set")])

    async def test_linked_patient_is_greeted_in_saved_language(self):
        repo = FakeRepository({999: {"id": "p1", "full_name": "Ana Perez", "role": "patient", "language": "en"}})
        deps = BotDependencies(repository=repo, nurse_agent=None)
        context = make_context(deps)
        update = make_update("/start", language_code="es")
        await start_command(update, context)
        self.assertTrue(update.effective_message.replies[0].startswith("Hi Ana Perez"))
        self.assertIn("/idioma", update.effective_message.replies[0])


class VoiceLanguageTest(unittest.IsolatedAsyncioTestCase):
    async def test_intake_questions_carry_language_to_voice(self):
        captured = {}

        async def fake_voice(kind, payload, fallback):
            captured.update(payload)
            return fallback

        deps = BotDependencies(repository=FakeRepository(), nurse_agent=None, voice=fake_voice)
        context = make_context(deps, {"language": "en"})
        await _speak(make_update("hi"), context, "¿Cuál es tu temperatura?", step="temperatura")
        self.assertEqual(captured["idioma"], "en")

    async def test_voice_prompt_gets_english_instruction_only_for_english(self):
        class FakeClient:
            def __init__(self, reply="ok 👵"):
                self.captured = None
                self.reply = reply
                self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

            async def _create(self, **kwargs):
                self.captured = kwargs
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.reply))])

        fake_settings = SimpleNamespace(openai_api_key="sk-test", openai_model="gpt-test", openai_reasoning_effort="low")
        client = FakeClient()
        with patch.object(nurse_voice, "settings", fake_settings):
            await compose_patient_message("chat", {"idioma": "en"}, "borrador", client=client)
        self.assertIn("INGLÉS", client.captured["messages"][0]["content"])

        client = FakeClient(reply="Your risk is **CRITICAL**: call 123 now.")
        with patch.object(nurse_voice, "settings", fake_settings):
            text = await compose_patient_message("chat", {"idioma": "en", "risk_level": "critical"}, "borrador", client=client)
        self.assertEqual(text, "Your risk is CRITICAL: call 123 now.")

        client = FakeClient()
        with patch.object(nurse_voice, "settings", fake_settings):
            await compose_patient_message("chat", {}, "borrador", client=client)
        self.assertNotIn("INGLÉS", client.captured["messages"][0]["content"])

    def test_urgency_guard_understands_english(self):
        critical = {"risk_level": "critical"}
        self.assertFalse(_loses_urgency(critical, "x", "Sweetie, go to the emergency room or call 123 now."))
        self.assertFalse(_loses_urgency(critical, "x", "Please call 123 right away."))
        self.assertTrue(_loses_urgency(critical, "x", "Everything looks fine, dear."))
        self.assertFalse(_loses_urgency({"risk_level": "high"}, "x", "Please contact your doctor today."))
        self.assertTrue(_loses_urgency({"risk_level": "high"}, "x", "All good, keep resting."))


class EnglishInputTest(unittest.IsolatedAsyncioTestCase):
    def test_validators_accept_english_quick_answers(self):
        self.assertTrue(is_skip_value("didn't measure"))
        self.assertTrue(is_skip_value("I didn’t measure"))  # apóstrofo curvo de iOS
        self.assertTrue(is_affirmative("Yes"))
        self.assertTrue(is_negative("not now"))

    def test_english_emergency_is_deterministic_and_in_english(self):
        self.assertTrue(_mentions_emergency(_normalize_text("I have chest pain right now")))
        self.assertTrue(_mentions_emergency(_normalize_text("I can’t breathe")))
        reply = build_carmen_free_text_response(
            "I have chest pain",
            {"id": "p1", "full_name": "Ana Perez", "role": "patient"},
            language="en",
        )
        self.assertTrue(reply.startswith("Ana, I hear you."))
        self.assertIn("call 123", reply)
        self.assertIn("/emergencia", reply)

    def test_spanish_emergency_text_is_unchanged(self):
        reply = build_carmen_free_text_response(
            "tengo dolor en el pecho", {"id": "p1", "full_name": "Ana Perez", "role": "patient"}
        )
        self.assertTrue(reply.startswith("Ana, te leo. Si esto está pasando ahora mismo"))
        self.assertIn("llama al 123", reply)

    async def test_reminders_follow_patient_language(self):
        class FakeBot:
            def __init__(self):
                self.messages = []

            async def send_message(self, chat_id, text):
                self.messages.append((chat_id, text))

        app = SimpleNamespace(bot=FakeBot())
        sent = await send_monitoring_reminders(app, FakeRepository())
        self.assertEqual(sent, 2)
        self.assertTrue(app.bot.messages[0][1].startswith("Hi Ana Perez"))
        self.assertTrue(app.bot.messages[1][1].startswith("Hola Luis Rojas"))


if __name__ == "__main__":
    unittest.main()
