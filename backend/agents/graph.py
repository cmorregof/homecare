from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agents.state import HomecareAgentState

if TYPE_CHECKING:
    from agents.nurse_agent import NurseAgent


class FallbackHomecareGraph:
    def __init__(self, nurse_agent: NurseAgent) -> None:
        self.nurse_agent = nurse_agent

    async def ainvoke(self, state: HomecareAgentState) -> HomecareAgentState:
        state = await self.nurse_agent.validate_vitals(state)
        state = await self.nurse_agent.save_to_db(state)
        state = await self.nurse_agent.call_ml_script(state)
        state = await self.nurse_agent.call_doctor_agent(state)
        state = await self.nurse_agent.check_alert_needed(state)
        if state.get("alert_needed"):
            state = await self.nurse_agent.send_alerts(state)
        else:
            state = {**state, "alert_sent": False}
        state = await self.nurse_agent.build_response(state)
        return await self.nurse_agent.respond_to_patient(state)


def build_homecare_graph(nurse_agent: NurseAgent | None = None) -> Any:
    from agents.nurse_agent import NurseAgent

    agent = nurse_agent or NurseAgent()
    try:
        from langgraph.graph import END, StateGraph
    except ModuleNotFoundError:
        return FallbackHomecareGraph(agent)

    workflow = StateGraph(HomecareAgentState)
    workflow.add_node("validate_vitals", agent.validate_vitals)
    workflow.add_node("save_to_db", agent.save_to_db)
    workflow.add_node("call_ml_script", agent.call_ml_script)
    workflow.add_node("call_doctor_agent", agent.call_doctor_agent)
    workflow.add_node("check_alert_needed", agent.check_alert_needed)
    workflow.add_node("send_alerts", agent.send_alerts)
    workflow.add_node("build_response", agent.build_response)
    workflow.add_node("respond_to_patient", agent.respond_to_patient)

    workflow.set_entry_point("validate_vitals")
    workflow.add_edge("validate_vitals", "save_to_db")
    workflow.add_edge("save_to_db", "call_ml_script")
    workflow.add_edge("call_ml_script", "call_doctor_agent")
    workflow.add_edge("call_doctor_agent", "check_alert_needed")
    workflow.add_conditional_edges(
        "check_alert_needed",
        _alert_route,
        {
            "send_alerts": "send_alerts",
            "build_response": "build_response",
        },
    )
    workflow.add_edge("send_alerts", "build_response")
    workflow.add_edge("build_response", "respond_to_patient")
    workflow.add_edge("respond_to_patient", END)
    return workflow.compile()


def _alert_route(state: HomecareAgentState) -> str:
    if state.get("alert_needed"):
        return "send_alerts"
    return "build_response"
