import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bot.handlers import (
    BotDependencies,
    link_document_message,
    looks_like_document_id,
    pick_doctor_for_new_patient,
    register_new_patient_message,
)


DOCTORS = [
    {"id": "doc-pablo", "full_name": "Pablo Benjumea", "telegram_chat_id": 111, "role": "ips"},
    {"id": "doc-juan", "full_name": "Juan Camilo Arias", "telegram_chat_id": 222, "role": "ips"},
    {"id": "doc-carlos", "full_name": "Carlos Orrego", "telegram_chat_id": 333, "role": "ips"},
]


class FakeRepository:
    def __init__(self, counts=None, create_result="profile"):
        self.counts = counts or {}
        self.create_result = create_result
        self.created = []

    async def link_telegram_account(self, document_id, chat_id):
        return None

    async def get_doctor_roster(self):
        return list(DOCTORS)

    async def count_assigned_patients(self, doctor_id):
        return self.counts.get(doctor_id, 0)

    async def create_patient_account(self, **kwargs):
        self.created.append(kwargs)
        if self.create_result == "profile":
            return {"id": "patient-1", "role": "patient", **kwargs}
        return None


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


def make_update(text, chat_id=999):
    message = FakeMessage(text)
    return SimpleNamespace(effective_message=message, effective_chat=SimpleNamespace(id=chat_id))


def make_context(user_data=None):
    return SimpleNamespace(user_data=user_data if user_data is not None else {})


class BotRegistrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_document_offers_registration(self):
        deps = BotDependencies(repository=FakeRepository(), nurse_agent=None)
        update = make_update("cc123999")
        context = make_context({"awaiting_document": True})
        await link_document_message(update, context, deps)
        self.assertTrue(context.user_data["awaiting_registration_name"])
        self.assertEqual(context.user_data["registration_document"], "cc123999")
        self.assertIn("nombre completo", update.effective_message.replies[0])

    async def test_registration_creates_account_and_assigns_doctor(self):
        repository = FakeRepository(counts={"doc-pablo": 2, "doc-juan": 1, "doc-carlos": 1})
        deps = BotDependencies(repository=repository, nurse_agent=None)
        update = make_update("ana maria perez")
        context = make_context(
            {"awaiting_registration_name": True, "registration_document": "cc123999"}
        )
        await register_new_patient_message(update, context, deps)
        self.assertEqual(len(repository.created), 1)
        created = repository.created[0]
        self.assertEqual(created["full_name"], "Ana Maria Perez")
        self.assertEqual(created["document_id"], "cc123999")
        self.assertEqual(created["telegram_chat_id"], 999)
        self.assertEqual(created["assigned_doctor_id"], "doc-juan")
        self.assertNotIn("awaiting_registration_name", context.user_data)
        self.assertIn("Juan Camilo Arias", update.effective_message.replies[0])

    async def test_registration_can_be_cancelled(self):
        repository = FakeRepository()
        deps = BotDependencies(repository=repository, nurse_agent=None)
        update = make_update("cancelar")
        context = make_context(
            {"awaiting_registration_name": True, "registration_document": "cc123999"}
        )
        await register_new_patient_message(update, context, deps)
        self.assertEqual(repository.created, [])
        self.assertNotIn("awaiting_registration_name", context.user_data)

    async def test_registration_rejects_incomplete_name(self):
        repository = FakeRepository()
        deps = BotDependencies(repository=repository, nurse_agent=None)
        update = make_update("Ana")
        context = make_context(
            {"awaiting_registration_name": True, "registration_document": "cc123999"}
        )
        await register_new_patient_message(update, context, deps)
        self.assertEqual(repository.created, [])
        self.assertTrue(context.user_data["awaiting_registration_name"])

    async def test_registration_failure_degrades_gracefully(self):
        repository = FakeRepository(create_result=None)
        deps = BotDependencies(repository=repository, nurse_agent=None)
        update = make_update("ana maria perez")
        context = make_context(
            {"awaiting_registration_name": True, "registration_document": "cc123999"}
        )
        await register_new_patient_message(update, context, deps)
        self.assertIn("No pude crear tu cuenta", update.effective_message.replies[0])
        self.assertTrue(context.user_data["awaiting_registration_name"])

    async def test_round_robin_prefers_least_loaded_doctor(self):
        repository = FakeRepository(counts={"doc-pablo": 0, "doc-juan": 0, "doc-carlos": 5})
        doctor = await pick_doctor_for_new_patient(repository)
        self.assertEqual(doctor["id"], "doc-pablo")

    def test_document_detection_accepts_cc_prefix(self):
        self.assertTrue(looks_like_document_id("cc123456"))
        self.assertTrue(looks_like_document_id("CC 1.234.567"))
        self.assertTrue(looks_like_document_id("1234567"))
        self.assertFalse(looks_like_document_id("ana maria"))


if __name__ == "__main__":
    unittest.main()
