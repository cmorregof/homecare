from __future__ import annotations

from typing import Any
from uuid import uuid4

from db.supabase_client import get_supabase_admin_client


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

    async def link_telegram_account(self, document_id: str, telegram_chat_id: int) -> dict[str, Any] | None:
        client = self.client
        if client is None:
            return None
        result = (
            client.table("profiles")
            .select("*")
            .eq("document_id", document_id.strip())
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        profile = dict(result.data[0])
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
            .select("id, full_name, telegram_chat_id, role")
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
