from __future__ import annotations

import logging
import secrets
from typing import Any
from uuid import uuid4

from db.supabase_client import get_supabase_admin_client

logger = logging.getLogger(__name__)


class HomecareRepository:
    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    @property
    def client(self) -> Any | None:
        if self._client is not None:
            return self._client
        try:
            self._client = get_supabase_admin_client()
        except RuntimeError:
            self._client = None
        return self._client

    async def save_vital_signs(
        self,
        patient_id: str,
        vital_signs: dict[str, Any],
        raw_message: str,
        source: str = "telegram",
    ) -> str:
        payload = {
            "patient_id": patient_id,
            "source": source,
            "raw_message": raw_message,
            "validated": True,
            **_filter_none(vital_signs),
        }
        return self._insert_and_get_id("vital_signs", payload)

    async def get_patient_clinical_info(self, patient_id: str) -> dict[str, Any]:
        client = self.client
        if client is None:
            return {}
        result = (
            client.table("patient_clinical_info")
            .select("*")
            .eq("patient_id", patient_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return {}
        return dict(result.data[0])

    async def find_profile_by_telegram_chat_id(self, telegram_chat_id: int) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        result = (
            client.table("profiles")
            .select("*")
            .eq("telegram_chat_id", telegram_chat_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return dict(result.data[0])

    def _find_profile_by_document(self, client: Any, document_id: str) -> dict[str, Any] | None:
        """Perfil por documento en cualquiera de sus formas equivalentes; el literal manda."""
        variants = document_id_variants(document_id)
        if not variants:
            return None
        result = (
            client.table("profiles")
            .select("*")
            .in_("document_id", variants)
            .limit(len(variants))
            .execute()
        )
        rows = [dict(row) for row in (result.data or [])]
        if not rows:
            return None
        for variant in variants:
            for row in rows:
                if row.get("document_id") == variant:
                    return row
        return rows[0]

    async def link_telegram_account(self, document_id: str, telegram_chat_id: int) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        profile = self._find_profile_by_document(client, document_id)
        if not profile:
            return None
        update_result = (
            client.table("profiles")
            .update({"telegram_chat_id": telegram_chat_id})
            .eq("id", profile["id"])
            .execute()
        )
        if update_result.data:
            return dict(update_result.data[0])
        profile["telegram_chat_id"] = telegram_chat_id
        return profile

    async def find_profile_by_whatsapp_phone(self, whatsapp_phone: str) -> dict[str, Any] | None:
        """Perfil vinculado a un número de WhatsApp (wa_id de Meta: E.164 sin '+').

        Tolerante a la migración 20260909 pendiente: si la columna no existe, deja
        WARNING y devuelve None; el canal conserva el vínculo en memoria."""
        client = self.client
        if client is None or not whatsapp_phone:
            return None
        try:
            result = (
                client.table("profiles")
                .select("*")
                .eq("whatsapp_phone", whatsapp_phone)
                .limit(1)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001 - el cliente Supabase lanza tipos variados
            logger.warning(
                "No se pudo buscar el perfil por WhatsApp %s (¿migración 20260909 pendiente?): %s",
                whatsapp_phone,
                exc,
            )
            return None
        if not result.data:
            return None
        return dict(result.data[0])

    async def link_whatsapp_account(self, document_id: str, whatsapp_phone: str) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        profile = self._find_profile_by_document(client, document_id)
        if not profile:
            return None
        try:
            update_result = (
                client.table("profiles")
                .update({"whatsapp_phone": whatsapp_phone})
                .eq("id", profile["id"])
                .execute()
            )
        except Exception as exc:  # noqa: BLE001 - migración 20260909 pendiente: vínculo en memoria
            logger.warning(
                "No se pudo guardar el WhatsApp del perfil %s (¿migración 20260909 pendiente?): %s",
                profile["id"],
                exc,
            )
            update_result = None
        if update_result is not None and update_result.data:
            return dict(update_result.data[0])
        profile["whatsapp_phone"] = whatsapp_phone
        return profile

    async def update_profile_language(self, profile_id: str, language: str) -> bool:
        """Guarda el idioma en que Carmen habla al paciente (es|en).

        Tolerante a fallos: si la columna aún no existe en producción (migración
        20260908 pendiente) devuelve False y el bot conserva el idioma en memoria."""
        client = self.client
        if client is None:
            return False
        try:
            result = (
                client.table("profiles")
                .update({"language": language})
                .eq("id", profile_id)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001 - el cliente Supabase lanza tipos variados
            logger.warning("No se pudo guardar el idioma del paciente %s (%s)", profile_id, exc)
            return False
        return bool(result.data)

    async def get_profile(self, profile_id: str) -> dict[str, Any] | None:
        return await self._get_profile(profile_id)

    async def get_doctor_roster(self) -> list[dict[str, Any]]:
        client = self.client
        if client is None:
            return []
        result = (
            client.table("profiles")
            .select("*")
            .eq("role", "ips")
            .order("created_at")
            .execute()
        )
        return list(result.data or [])

    async def count_assigned_patients(self, doctor_id: str) -> int:
        client = self.client
        if client is None:
            return 0
        result = (
            client.table("profiles")
            .select("id", count="exact")
            .eq("role", "patient")
            .eq("assigned_doctor_id", doctor_id)
            .execute()
        )
        return int(result.count or 0)

    async def create_patient_account(
        self,
        *,
        full_name: str,
        document_id: str,
        telegram_chat_id: int | None = None,
        assigned_doctor_id: str | None = None,
        whatsapp_phone: str | None = None,
    ) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        document_id = normalize_document_id(document_id) or document_id
        email = f"paciente.{_document_slug(document_id)}@homecareccv.demo"
        try:
            created = client.auth.admin.create_user(
                {
                    "email": email,
                    "password": secrets.token_urlsafe(24),
                    "email_confirm": True,
                    "user_metadata": {"full_name": full_name, "document_id": document_id},
                }
            )
        except Exception as exc:  # noqa: BLE001 - gotrue lanza AuthApiError; el mensaje es lo útil
            # Caso típico: el documento ya tenía cuenta pero se escribió en otro formato
            # (con puntos) y la búsqueda no la encontró. Vinculamos la existente en vez
            # de dejar al paciente sin respuesta.
            logger.warning("No se pudo crear el usuario de Auth para el documento %s: %s", document_id, exc)
            existing = self._find_profile_by_document(client, document_id)
            if not existing:
                return None
            return self._link_existing_profile(
                client, existing, telegram_chat_id=telegram_chat_id, whatsapp_phone=whatsapp_phone
            )
        user = getattr(created, "user", None) or created
        user_id = getattr(user, "id", None)
        if user_id is None:
            return None
        payload = _filter_none(
            {
                "id": str(user_id),
                "role": "patient",
                "full_name": full_name,
                "document_id": document_id,
                "telegram_chat_id": telegram_chat_id,
                "whatsapp_phone": whatsapp_phone,
                "assigned_doctor_id": assigned_doctor_id,
            }
        )
        try:
            result = client.table("profiles").insert(payload).execute()
        except Exception as exc:  # noqa: BLE001 - el cliente Supabase lanza tipos variados
            if "whatsapp_phone" not in payload:
                raise
            # Migración 20260909 pendiente: la cuenta se crea igual y el canal conserva el
            # vínculo en memoria (WARNING). El usuario de Auth ya existe; no se duplica.
            logger.warning(
                "No se pudo guardar whatsapp_phone al crear el perfil %s (%s); reintento sin la columna.",
                user_id,
                exc,
            )
            fallback = {key: value for key, value in payload.items() if key != "whatsapp_phone"}
            result = client.table("profiles").insert(fallback).execute()
            rows = result.data or []
            created = dict(rows[0]) if rows else dict(fallback)
            created["whatsapp_phone"] = whatsapp_phone
            return created
        rows = result.data or []
        return rows[0] if rows else payload

    def _link_existing_profile(
        self,
        client: Any,
        profile: dict[str, Any],
        *,
        telegram_chat_id: int | None,
        whatsapp_phone: str | None,
    ) -> dict[str, Any]:
        """Guarda el id de canal en un perfil existente; si la columna falta, queda en memoria."""
        changes = _filter_none({"telegram_chat_id": telegram_chat_id, "whatsapp_phone": whatsapp_phone})
        if not changes:
            return profile
        try:
            result = client.table("profiles").update(changes).eq("id", profile["id"]).execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo vincular el canal al perfil %s: %s", profile.get("id"), exc)
            return {**profile, **changes}
        rows = result.data or []
        return dict(rows[0]) if rows else {**profile, **changes}

    async def get_latest_risk_prediction(self, patient_id: str) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        result = (
            client.table("risk_predictions")
            .select("*")
            .eq("patient_id", patient_id)
            .order("predicted_at", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return dict(result.data[0])

    async def get_recent_vital_signs(self, patient_id: str, limit: int = 5) -> list[dict[str, Any]]:
        client = self.client
        if client is None:
            return []
        result = (
            client.table("vital_signs")
            .select("*")
            .eq("patient_id", patient_id)
            .order("recorded_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [dict(row) for row in (result.data or [])]

    async def get_vital_history(self, patient_id: str, limit: int = 250) -> list[dict[str, Any]]:
        client = self.client
        if client is None:
            return []
        result = (
            client.table("vital_signs")
            .select("*")
            .eq("patient_id", patient_id)
            .order("recorded_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = list(result.data or [])
        rows.reverse()
        return rows

    async def get_alert_recipients(self, patient_id: str) -> dict[str, Any]:
        client = self.client
        if client is None:
            return {}
        patient = await self._get_profile(patient_id)
        doctor: dict[str, Any] | None = None
        if patient and patient.get("assigned_doctor_id"):
            doctor = await self._get_profile(str(patient["assigned_doctor_id"]))
        ips: dict[str, Any] | None = None
        if patient and patient.get("ips_id"):
            ips = await self._get_ips(str(patient["ips_id"]))
        doctor_email = None
        if doctor:
            doctor_email = doctor.get("email") or doctor.get("contact_email")
        if not doctor_email and ips:
            doctor_email = ips.get("contact_email")
        return {
            "patient": patient,
            "doctor": doctor,
            "ips": ips,
            "patient_telegram_chat_id": patient.get("telegram_chat_id") if patient else None,
            "doctor_telegram_chat_id": doctor.get("telegram_chat_id") if doctor else None,
            "doctor_email": doctor_email,
        }

    async def get_monitoring_patients(self) -> list[dict[str, Any]]:
        client = self.client
        if client is None:
            return []
        result = (
            client.table("profiles")
            .select("*")
            .eq("role", "patient")
            .limit(1000)
            .execute()
        )
        return [dict(row) for row in (result.data or []) if row.get("telegram_chat_id")]

    async def save_risk_prediction(self, payload: dict[str, Any]) -> str:
        return self._insert_and_get_id("risk_predictions", _filter_none(payload))

    async def save_clinical_report(self, payload: dict[str, Any]) -> str:
        return self._insert_and_get_id("clinical_reports", _filter_none(payload))

    async def save_alert(self, payload: dict[str, Any]) -> str:
        return self._insert_and_get_id("alerts", _filter_none(payload))

    async def _get_profile(self, profile_id: str) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        result = (
            client.table("profiles")
            .select("*")
            .eq("id", profile_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return dict(result.data[0])

    async def _get_ips(self, ips_id: str) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        result = (
            client.table("ips")
            .select("*")
            .eq("id", ips_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return dict(result.data[0])

    def _insert_and_get_id(self, table: str, payload: dict[str, Any]) -> str:
        client = self.client
        if client is None:
            return str(uuid4())
        result = client.table(table).insert(payload).execute()
        if not result.data:
            return str(uuid4())
        return str(result.data[0]["id"])


def _filter_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def normalize_document_id(document_id: str) -> str:
    """Forma compacta con la que se guarda un documento: solo dígitos, o 'cc' + dígitos.

    '1.002.652.750' → '1002652750'; 'CC 1.002.652.750' → 'cc1002652750'."""
    compact = "".join(ch for ch in str(document_id or "").strip().lower() if ch.isalnum())
    if compact.startswith("cc") and compact[2:].isdigit():
        return f"cc{compact[2:]}"
    return compact


def document_id_variants(document_id: str) -> list[str]:
    """Formas equivalentes de un documento tal como puede estar guardado en `profiles`:
    literal, solo dígitos, 'cc'+dígitos y con puntos de miles (1.002.652.750).

    Los pacientes escriben el documento con puntos y las IPS lo guardan sin ellos; una
    búsqueda literal no encontraba la cuenta y ofrecía registrar un duplicado."""
    raw = str(document_id or "").strip()
    normalized = normalize_document_id(raw)
    digits = normalized[2:] if normalized.startswith("cc") else normalized
    variants = [raw, normalized]
    if digits:
        dotted = _dotted_thousands(digits) if digits.isdigit() else digits
        variants += [digits, f"cc{digits}", dotted, f"cc{dotted}"]
    unique: list[str] = []
    for variant in variants:
        if variant and variant not in unique:
            unique.append(variant)
    return unique


def _dotted_thousands(digits: str) -> str:
    groups: list[str] = []
    while len(digits) > 3:
        groups.insert(0, digits[-3:])
        digits = digits[:-3]
    groups.insert(0, digits)
    return ".".join(groups)


def _document_slug(document_id: str) -> str:
    compact = "".join(character for character in document_id.lower() if character.isalnum())
    return compact or uuid4().hex[:10]
