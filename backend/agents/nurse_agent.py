from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from agents.doctor_agent import DoctorAgent
from agents.state import HomecareAgentState
from config import settings
from db.repository import HomecareRepository
from notifications.email import send_risk_email_alert
from notifications.telegram_alerts import send_telegram_risk_alert
from utils.risk_levels import RISK_LEVELS, estimate_rule_based_risk, normalize_risk_level, should_alert_staff


MlPredictor = Callable[[dict[str, Any]], dict[str, Any] | Awaitable[dict[str, Any]]]


class NurseAgent:
    def __init__(
        self,
        repository: HomecareRepository | None = None,
        doctor_agent: DoctorAgent | None = None,
        ml_predictor: MlPredictor | None = None,
    ) -> None:
        self.repository = repository or HomecareRepository()
        self.doctor_agent = doctor_agent or DoctorAgent()
        self.ml_predictor = ml_predictor

    async def process_vital_report(self, state: HomecareAgentState) -> HomecareAgentState:
        from agents.graph import build_homecare_graph

        graph = build_homecare_graph(self)
        return await graph.ainvoke(state)

    async def validate_vitals(self, state: HomecareAgentState) -> HomecareAgentState:
        vital_signs = dict(state.get("vital_signs") or {})
        if state.get("raw_message") and not vital_signs:
            vital_signs = parse_vital_signs_message(state["raw_message"])
        validation_errors = validate_vital_signs(vital_signs)
        return {
            **state,
            "vital_signs": vital_signs,
            "validation_errors": validation_errors,
        }

    async def save_to_db(self, state: HomecareAgentState) -> HomecareAgentState:
        patient_id = state["patient_id"]
        vital_sign_id = await self.repository.save_vital_signs(
            patient_id=patient_id,
            vital_signs=state.get("vital_signs", {}),
            raw_message=state.get("raw_message", ""),
            source=state.get("source", "telegram"),
        )
        clinical_info = await self.repository.get_patient_clinical_info(patient_id)
        return {
            **state,
            "vital_sign_id": vital_sign_id,
            "patient_clinical_info": clinical_info,
        }

    async def call_ml_script(self, state: HomecareAgentState) -> HomecareAgentState:
        if _has_blocking_validation_errors(state):
            return state

        payload = {
            "patient_id": state["patient_id"],
            "vital_sign_id": state["vital_sign_id"],
            "features": build_ml_features(
                state.get("vital_signs", {}),
                state.get("patient_clinical_info", {}),
            ),
        }
        prediction = await self._predict_with_ml(payload, state)
        risk_level = normalize_risk_level(prediction.get("risk_level"))
        prediction_payload = {
            "patient_id": state["patient_id"],
            "vital_sign_id": state.get("vital_sign_id"),
            "risk_level": risk_level,
            "risk_probability": float(prediction.get("risk_probability") or 0),
            "model_used": str(prediction.get("model_used") or "unknown"),
            "shap_values": prediction.get("shap_values") or {},
            "top_risk_factors": prediction.get("top_risk_factors") or [],
            "confidence_score": prediction.get("confidence_score"),
        }
        prediction_id = await self.repository.save_risk_prediction(prediction_payload)
        return {
            **state,
            "prediction_id": prediction_id,
            "risk_level": risk_level,
            "risk_probability": prediction_payload["risk_probability"],
            "probabilities": prediction.get("probabilities") or {},
            "shap_values": prediction_payload["shap_values"],
            "top_risk_factors": prediction_payload["top_risk_factors"],
            "model_used": prediction_payload["model_used"],
            "confidence_score": prediction_payload.get("confidence_score") or 0,
        }

    async def call_doctor_agent(self, state: HomecareAgentState) -> HomecareAgentState:
        if _has_blocking_validation_errors(state):
            return state

        report = await self.doctor_agent.generate_report(
            {
                "vital_signs": state.get("vital_signs", {}),
                "risk_level": state.get("risk_level"),
                "risk_probability": state.get("risk_probability"),
                "shap_values": state.get("shap_values", {}),
                "top_risk_factors": state.get("top_risk_factors", []),
                "patient_clinical_info": state.get("patient_clinical_info", {}),
            }
        )
        clinical_report_id = await self.repository.save_clinical_report(
            {
                "patient_id": state["patient_id"],
                "vital_sign_id": state.get("vital_sign_id"),
                "prediction_id": state.get("prediction_id"),
                "interpretation": report.get("interpretation", ""),
                "recommendations": report.get("recommendations", ""),
                "follow_up_actions": report.get("follow_up_actions", ""),
                "rag_sources": report.get("rag_sources", []),
                "agent_response_full": report.get("agent_response_full", ""),
            }
        )
        return {
            **state,
            "clinical_report_id": clinical_report_id,
            "clinical_report": report.get("agent_response_full", ""),
            "interpretation": report.get("interpretation", ""),
            "recommendations": report.get("recommendations", ""),
            "follow_up_actions": report.get("follow_up_actions", ""),
            "rag_sources": report.get("rag_sources", []),
        }

    async def check_alert_needed(self, state: HomecareAgentState) -> HomecareAgentState:
        risk_level = normalize_risk_level(state.get("risk_level"))
        return {
            **state,
            "risk_level": risk_level,
            "alert_needed": should_alert_staff(risk_level),
        }

    async def send_alerts(self, state: HomecareAgentState) -> HomecareAgentState:
        if not state.get("alert_needed"):
            return {**state, "alert_sent": False}
        risk = RISK_LEVELS[normalize_risk_level(state.get("risk_level"))]
        recipients = await _get_alert_recipients(self.repository, state["patient_id"])
        patient = recipients.get("patient") or {}
        message = (
            f"Alerta HomecareCCV: paciente {patient.get('full_name') or state['patient_id']} "
            f"con riesgo {risk['label']}. "
            f"{risk['description']} Signos: {state.get('vital_signs', {})}"
        )
        notification_payload = {
            **recipients,
            "patient_id": state["patient_id"],
            "patient_name": patient.get("full_name"),
            "risk_level": normalize_risk_level(state.get("risk_level")),
            "message": message,
            "vital_signs": state.get("vital_signs", {}),
            "recommendations": state.get("recommendations") or risk["action"],
        }
        telegram_sent = await send_telegram_risk_alert(notification_payload)
        email_sent = await send_risk_email_alert(notification_payload)
        await self.repository.save_alert(
            {
                "patient_id": state["patient_id"],
                "prediction_id": state.get("prediction_id"),
                "risk_level": normalize_risk_level(state.get("risk_level")),
                "message": message,
                "sent_to_patient": bool(recipients.get("patient_telegram_chat_id") and telegram_sent),
                "sent_to_doctor": bool(
                    (recipients.get("doctor_telegram_chat_id") and telegram_sent)
                    or (recipients.get("doctor_email") and email_sent)
                ),
                "email_sent": email_sent,
                "telegram_sent": telegram_sent,
            }
        )
        return {**state, "alert_sent": True}

    async def build_response(self, state: HomecareAgentState) -> HomecareAgentState:
        if _has_blocking_validation_errors(state):
            missing = "\n".join(f"- {error}" for error in state.get("validation_errors", []))
            response = (
                "Gracias por escribirme. Para analizar tus signos con seguridad necesito "
                "que me confirmes estos datos:\n"
                f"{missing}\n\n"
                "Puedes enviarlos, por ejemplo, así: presión 120/80, pulso 75, "
                "saturación 97, glucosa 110."
            )
            return {**state, "final_response": response}

        risk_level = normalize_risk_level(state.get("risk_level"))
        risk = RISK_LEVELS[risk_level]
        probability = float(state.get("risk_probability") or 0)
        alert_text = (
            " Ya dejé registrada una alerta para el equipo de salud."
            if state.get("alert_sent")
            else ""
        )
        response = (
            f"Listo, recibí tus signos vitales.\n\n"
            f"Nivel de riesgo: {risk['label']} ({probability:.0%}).\n"
            f"{risk['description']}{alert_text}\n\n"
            f"Recomendación del médico:\n{state.get('recommendations') or risk['action']}\n\n"
            f"Seguimiento:\n{state.get('follow_up_actions') or risk['action']}\n\n"
            "Recuerda: no cambies tus medicamentos sin indicación de tu médico tratante."
        )
        return {**state, "final_response": response}

    async def respond_to_patient(self, state: HomecareAgentState) -> HomecareAgentState:
        return state

    async def _predict_with_ml(
        self,
        payload: dict[str, Any],
        state: HomecareAgentState,
    ) -> dict[str, Any]:
        if self.ml_predictor is not None:
            result = self.ml_predictor(payload)
            if inspect.isawaitable(result):
                return await result
            return result

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(f"{settings.ml_api_url.rstrip('/')}/ml/predict", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception:
            return estimate_rule_based_risk(
                state.get("vital_signs", {}),
                state.get("patient_clinical_info", {}),
            )


def parse_vital_signs_message(message: str) -> dict[str, Any]:
    text = message.lower()
    vital_signs: dict[str, Any] = {}

    pressure_match = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", text)
    if pressure_match:
        vital_signs["systolic_bp"] = int(pressure_match.group(1))
        vital_signs["diastolic_bp"] = int(pressure_match.group(2))

    keyword_patterns = {
        "heart_rate": r"(?:pulso|frecuencia|fc|cardiaca|cardíaca)\D{0,12}(\d{2,3})",
        "oxygen_saturation": r"(?:saturacion|saturación|sat|oxigeno|oxígeno)\D{0,12}(\d{2,3})",
        "glucose": r"(?:glucosa|azucar|azúcar)\D{0,12}(\d{2,3})",
        "temperature": r"(?:temperatura|temp|fiebre)\D{0,12}(\d{2}(?:[\.,]\d)?)",
        "pain_score": r"(?:dolor)\D{0,12}(\d{1,2})",
        "dizziness_score": r"(?:mareo|mareos|inestabilidad)\D{0,12}(\d{1,2})",
        "dyspnea_score": r"(?:disnea|respirar|respiracion|respiración|ahogo)\D{0,12}(\d{1,2})",
    }
    for field, pattern in keyword_patterns.items():
        match = re.search(pattern, text)
        if match:
            raw_value = match.group(1).replace(",", ".")
            value: float | int = float(raw_value) if "." in raw_value else int(raw_value)
            vital_signs[field] = value

    return vital_signs


def validate_vital_signs(vital_signs: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = {
        "systolic_bp": "presión sistólica",
        "diastolic_bp": "presión diastólica",
        "heart_rate": "frecuencia cardíaca",
    }
    for field, label in required_fields.items():
        if vital_signs.get(field) is None:
            errors.append(f"Falta {label}.")

    ranges = {
        "systolic_bp": (50, 260, "presión sistólica"),
        "diastolic_bp": (30, 160, "presión diastólica"),
        "heart_rate": (25, 220, "frecuencia cardíaca"),
        "oxygen_saturation": (1, 100, "saturación de oxígeno"),
        "temperature": (30, 43, "temperatura"),
        "glucose": (20, 600, "glucosa"),
        "pain_score": (0, 10, "dolor"),
        "dizziness_score": (0, 10, "mareo"),
        "dyspnea_score": (0, 10, "dificultad para respirar"),
    }
    for field, (minimum, maximum, label) in ranges.items():
        value = vital_signs.get(field)
        if value is None:
            continue
        numeric_value = float(value)
        if numeric_value < minimum or numeric_value > maximum:
            errors.append(f"El valor de {label} parece fuera del rango reportable.")
    return errors


def build_ml_features(
    vital_signs: dict[str, Any],
    clinical_info: dict[str, Any],
) -> dict[str, Any]:
    systolic = _to_float(vital_signs.get("systolic_bp"))
    diastolic = _to_float(vital_signs.get("diastolic_bp"))
    height_cm = _to_float(clinical_info.get("height_cm"))
    weight_kg = _to_float(vital_signs.get("weight_kg") or clinical_info.get("weight_kg"))
    bmi = _to_float(clinical_info.get("bmi"))
    if bmi is None and height_cm and weight_kg:
        bmi = weight_kg / ((height_cm / 100) ** 2)
    pulse_pressure = systolic - diastolic if systolic is not None and diastolic is not None else None
    mean_arterial_pressure = (
        diastolic + (pulse_pressure / 3)
        if diastolic is not None and pulse_pressure is not None
        else None
    )
    return {
        "age": clinical_info.get("age"),
        "gender_encoded": _encode_gender(clinical_info.get("gender")),
        "systolic_bp": systolic,
        "diastolic_bp": diastolic,
        "heart_rate": _to_float(vital_signs.get("heart_rate")),
        "oxygen_saturation": _to_float(vital_signs.get("oxygen_saturation")),
        "glucose": _to_float(vital_signs.get("glucose")),
        "bmi": bmi,
        "cholesterol_level": clinical_info.get("cholesterol_level"),
        "hypertension_history": clinical_info.get("hypertension_history", False),
        "heart_disease_history": clinical_info.get("heart_disease_history", False),
        "stroke_history": clinical_info.get("stroke_history", False),
        "diabetes_history": clinical_info.get("diabetes_history", False),
        "smoking_encoded": _encode_smoking(clinical_info.get("smoking")),
        "alcohol_intake": clinical_info.get("alcohol_intake", False),
        "physical_activity": clinical_info.get("physical_activity", True),
        "pain_score": vital_signs.get("pain_score", 0),
        "dizziness_score": vital_signs.get("dizziness_score", 0),
        "dyspnea_score": vital_signs.get("dyspnea_score", 0),
        "pulse_pressure": pulse_pressure,
        "map": mean_arterial_pressure,
        "bmi_category": _bmi_category(bmi),
    }


def _has_blocking_validation_errors(state: HomecareAgentState) -> bool:
    return bool(state.get("validation_errors"))


async def _get_alert_recipients(repository: HomecareRepository, patient_id: str) -> dict[str, Any]:
    if hasattr(repository, "get_alert_recipients"):
        return await repository.get_alert_recipients(patient_id)
    return {}


def _encode_gender(value: Any) -> int | None:
    if value == "female":
        return 0
    if value == "male":
        return 1
    return None


def _encode_smoking(value: Any) -> int:
    return {"never": 0, "former": 1, "current": 2}.get(str(value or "never"), 0)


def _bmi_category(bmi: float | None) -> int | None:
    if bmi is None:
        return None
    if bmi < 18.5:
        return 0
    if bmi < 25:
        return 1
    if bmi < 30:
        return 2
    return 3


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
