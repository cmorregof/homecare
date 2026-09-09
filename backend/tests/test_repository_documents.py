"""Documentos escritos con puntos ('1.002.652.750'): búsqueda tolerante, guardado compacto y
colisión en Auth al registrar un documento que ya tenía cuenta. Vale para Telegram y WhatsApp."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from db.repository import HomecareRepository, document_id_variants, normalize_document_id


class FakeQuery:
    """Subconjunto mínimo del builder de supabase-py sobre una lista de filas en memoria."""

    def __init__(self, table):
        self.table = table
        self.filters = []
        self.pending_update = None
        self.pending_insert = None
        self._limit = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, column, value):
        self.filters.append(lambda row: row.get(column) == value)
        return self

    def in_(self, column, values):
        self.filters.append(lambda row: row.get(column) in list(values))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def order(self, *args, **kwargs):
        return self

    def update(self, changes):
        self.pending_update = dict(changes)
        return self

    def insert(self, payload):
        self.pending_insert = dict(payload)
        return self

    def execute(self):
        if self.pending_insert is not None:
            self.table.rows.append(dict(self.pending_insert))
            return SimpleNamespace(data=[dict(self.pending_insert)], count=None)
        matched = [row for row in self.table.rows if all(f(row) for f in self.filters)]
        if self.pending_update is not None:
            for row in matched:
                row.update(self.pending_update)
            return SimpleNamespace(data=[dict(r) for r in matched], count=None)
        if self._limit is not None:
            matched = matched[: self._limit]
        return SimpleNamespace(data=[dict(r) for r in matched], count=len(matched))


class FakeTable:
    def __init__(self, rows):
        self.rows = rows


class FakeAdminAuth:
    def __init__(self, error=None):
        self.error = error
        self.created = []

    def create_user(self, payload):
        if self.error:
            raise self.error
        self.created.append(payload)
        return SimpleNamespace(user=SimpleNamespace(id="user-new"))


class FakeSupabase:
    def __init__(self, profiles, auth_error=None):
        self.tables = {"profiles": FakeTable(profiles)}
        self.auth = SimpleNamespace(admin=FakeAdminAuth(auth_error))

    def table(self, name):
        return FakeQuery(self.tables[name])


EXISTING = {"id": "p-1", "role": "patient", "full_name": "Carlos Orrego", "document_id": "1002652750"}


class DocumentHelpersTest(unittest.TestCase):
    def test_normalize_keeps_digits_and_cc_prefix(self):
        self.assertEqual(normalize_document_id("1.002.652.750"), "1002652750")
        self.assertEqual(normalize_document_id(" CC 1.002.652-750 "), "cc1002652750")
        self.assertEqual(normalize_document_id("cc123456"), "cc123456")
        self.assertEqual(normalize_document_id(""), "")

    def test_variants_cover_stored_formats(self):
        variants = document_id_variants("1.002.652.750")
        self.assertEqual(variants[0], "1.002.652.750")
        for expected in ("1002652750", "cc1002652750", "cc1.002.652.750"):
            self.assertIn(expected, variants)
        self.assertEqual(len(variants), len(set(variants)))
        self.assertEqual(document_id_variants("   "), [])


class LinkByDocumentTest(unittest.IsolatedAsyncioTestCase):
    async def test_dotted_document_links_existing_digits_only_profile_whatsapp(self):
        client = FakeSupabase([dict(EXISTING)])
        repo = HomecareRepository(client=client)
        profile = await repo.link_whatsapp_account("1.002.652.750", "573001112233")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["id"], "p-1")
        self.assertEqual(profile["whatsapp_phone"], "573001112233")
        self.assertEqual(client.tables["profiles"].rows[0]["whatsapp_phone"], "573001112233")

    async def test_dotted_document_links_existing_profile_telegram(self):
        client = FakeSupabase([dict(EXISTING)])
        repo = HomecareRepository(client=client)
        profile = await repo.link_telegram_account("1.002.652.750", 999)
        self.assertEqual(profile["id"], "p-1")
        self.assertEqual(profile["telegram_chat_id"], 999)

    async def test_literal_match_wins_over_variants(self):
        rows = [dict(EXISTING), {"id": "p-2", "role": "patient", "full_name": "Otro", "document_id": "cc1002652750"}]
        repo = HomecareRepository(client=FakeSupabase(rows))
        profile = await repo.link_telegram_account("cc1002652750", 1)
        self.assertEqual(profile["id"], "p-2")

    async def test_unknown_document_still_returns_none(self):
        repo = HomecareRepository(client=FakeSupabase([dict(EXISTING)]))
        self.assertIsNone(await repo.link_whatsapp_account("9.999.999", "573001112233"))


class CreateAccountTest(unittest.IsolatedAsyncioTestCase):
    async def test_new_account_stores_compact_document(self):
        client = FakeSupabase([])
        repo = HomecareRepository(client=client)
        profile = await repo.create_patient_account(
            full_name="Ana Pérez", document_id="1.234.567.890", whatsapp_phone="573001112233"
        )
        self.assertEqual(profile["document_id"], "1234567890")
        self.assertEqual(profile["whatsapp_phone"], "573001112233")
        self.assertNotIn("telegram_chat_id", profile)
        self.assertIn("paciente.1234567890@", client.auth.admin.created[0]["email"])

    async def test_auth_collision_links_existing_profile_instead_of_crashing(self):
        error = RuntimeError("A user with this email address has already been registered")
        client = FakeSupabase([dict(EXISTING)], auth_error=error)
        repo = HomecareRepository(client=client)
        with self.assertLogs("db.repository", level="WARNING"):
            profile = await repo.create_patient_account(
                full_name="Carlos Manuel Orrego", document_id="1.002.652.750", whatsapp_phone="573001112233"
            )
        self.assertEqual(profile["id"], "p-1")
        self.assertEqual(profile["whatsapp_phone"], "573001112233")
        self.assertEqual(len(client.tables["profiles"].rows), 1)

    async def test_auth_failure_without_existing_profile_returns_none(self):
        client = FakeSupabase([], auth_error=RuntimeError("boom"))
        repo = HomecareRepository(client=client)
        with self.assertLogs("db.repository", level="WARNING"):
            profile = await repo.create_patient_account(full_name="Ana Pérez", document_id="123456", telegram_chat_id=5)
        self.assertIsNone(profile)


if __name__ == "__main__":
    unittest.main()
