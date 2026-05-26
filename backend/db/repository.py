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

    async def save_risk_prediction(self, payload: dict[str, Any]) -> str:
        return self._insert_and_get_id("risk_predictions", _filter_none(payload))

    async def save_clinical_report(self, payload: dict[str, Any]) -> str:
        return self._insert_and_get_id("clinical_reports", _filter_none(payload))

    async def save_alert(self, payload: dict[str, Any]) -> str:
        return self._insert_and_get_id("alerts", _filter_none(payload))

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
