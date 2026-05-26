"""Agent 2: clinical consultant with RAG support."""

from typing import Any


class DoctorAgent:
    """Clinical interpretation agent.

    RAG retrieval and OpenAI generation are implemented in Sprint 3.
    """

    async def generate_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Doctor agent flow belongs to Sprint 3.")
