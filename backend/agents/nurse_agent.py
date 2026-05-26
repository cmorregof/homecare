"""Agent 1: virtual nurse for patient-facing interactions."""

from agents.state import HomecareAgentState


class NurseAgent:
    """Carmen, the virtual nurse.

    The production LangGraph flow is implemented in Sprint 3. This class marks
    the public interface expected by the Telegram bot and web chat modules.
    """

    async def process_vital_report(self, state: HomecareAgentState) -> HomecareAgentState:
        raise NotImplementedError("Nurse agent flow belongs to Sprint 3.")
