import unittest

from agents.doctor_agent import DoctorAgent
from agents.nurse_agent import NurseAgent, parse_vital_signs_message
from utils.risk_levels import estimate_rule_based_risk


class FakeRepository:
    def __init__(self) -> None:
        self.alerts: list[dict[str, object]] = []
        self.predictions: list[dict[str, object]] = []
        self.reports: list[dict[str, object]] = []
        self.vitals: list[dict[str, object]] = []

    async def save_vital_signs(self, patient_id, vital_signs, raw_message, source="telegram"):
        self.vitals.append(
            {
                "patient_id": patient_id,
                "vital_signs": vital_signs,
                "raw_message": raw_message,
                "source": source,
            }
        )
        return "vital-1"

    async def get_patient_clinical_info(self, patient_id):
        return {
            "age": 72,
            "gender": "male",
            "hypertension_history": True,
            "stroke_history": True,
            "cholesterol_level": 2,
        }

    async def save_risk_prediction(self, payload):
        self.predictions.append(payload)
        return "prediction-1"

    async def save_clinical_report(self, payload):
        self.reports.append(payload)
        return "report-1"

    async def save_alert(self, payload):
        self.alerts.append(payload)
        return "alert-1"


class FakeDoctorAgent:
    async def generate_report(self, payload):
        return {
            "interpretation": "Interpretación: presión elevada con síntomas leves.",
            "risk_evaluation": "Evaluación de riesgo: alto.",
            "recommendations": "Repetir medición y esperar contacto del equipo tratante.",
            "follow_up_actions": "Contactar al médico responsable.",
            "rag_sources": [{"title": "MEWS", "source": "fallback"}],
            "agent_response_full": "Reporte médico estructurado.",
        }


class AgentsFlowTest(unittest.IsolatedAsyncioTestCase):
    def test_parse_vital_signs_message(self):
        parsed = parse_vital_signs_message(
            "Presión 165/95, pulso 88, saturación 96, glucosa 130, dolor 2, mareo 1"
        )
        self.assertEqual(parsed["systolic_bp"], 165)
        self.assertEqual(parsed["diastolic_bp"], 95)
        self.assertEqual(parsed["heart_rate"], 88)
        self.assertEqual(parsed["oxygen_saturation"], 96)
        self.assertEqual(parsed["glucose"], 130)
        self.assertEqual(parsed["pain_score"], 2)
        self.assertEqual(parsed["dizziness_score"], 1)

    async def test_doctor_agent_fallback_report(self):
        report = await DoctorAgent().generate_report(
            {
                "vital_signs": {"systolic_bp": 165, "diastolic_bp": 95, "heart_rate": 88},
                "risk_level": "high",
                "risk_probability": 0.78,
                "top_risk_factors": [{"feature": "systolic_bp"}],
            }
        )
        self.assertIn("Interpretación", report["interpretation"])
        self.assertIn("Recomendaciones", report["recommendations"])
        self.assertTrue(report["rag_sources"])

    async def test_complete_nurse_agent_flow_with_alert(self):
        repository = FakeRepository()

        async def fake_ml_predictor(payload):
            return {
                "risk_level": "high",
                "risk_probability": 0.82,
                "probabilities": {"low": 0.02, "moderate": 0.16, "high": 0.82, "critical": 0.0},
                "model_used": "test_model",
                "shap_values": {"systolic_bp": 0.4},
                "top_risk_factors": [{"feature": "systolic_bp", "value": 165, "shap": 0.4}],
                "confidence_score": 0.9,
            }

        agent = NurseAgent(
            repository=repository,
            doctor_agent=FakeDoctorAgent(),
            ml_predictor=fake_ml_predictor,
        )
        state = await agent.process_vital_report(
            {
                "patient_id": "patient-1",
                "raw_message": "Presión 165/95, pulso 88, saturación 96, glucosa 130",
                "source": "telegram",
            }
        )

        self.assertEqual(state["vital_sign_id"], "vital-1")
        self.assertEqual(state["prediction_id"], "prediction-1")
        self.assertEqual(state["risk_level"], "high")
        self.assertTrue(state["alert_sent"])
        self.assertEqual(len(repository.alerts), 1)
        self.assertIn("Nivel de riesgo", state["final_response"])
        self.assertIn("no cambies tus medicamentos", state["final_response"])

    async def test_incomplete_report_asks_for_missing_data(self):
        agent = NurseAgent(repository=FakeRepository(), doctor_agent=FakeDoctorAgent())
        state = await agent.process_vital_report(
            {
                "patient_id": "patient-1",
                "raw_message": "Saturación 97",
                "source": "telegram",
            }
        )
        self.assertIn("necesito que me confirmes", state["final_response"])
        self.assertFalse(state.get("alert_sent"))

    def test_rule_based_fallback_escalates_immediate_critical_thresholds(self):
        prediction = estimate_rule_based_risk(
            {
                "systolic_bp": 182,
                "diastolic_bp": 95,
                "heart_rate": 86,
            }
        )
        self.assertEqual(prediction["risk_level"], "critical")

    async def test_ml_endpoint_contract_is_available(self):
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.post(
            "/ml/predict",
            json={
                "patient_id": "patient-1",
                "vital_sign_id": "vital-1",
                "features": {
                    "systolic_bp": 182,
                    "diastolic_bp": 95,
                    "heart_rate": 88,
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(body["risk_level"], {"low", "moderate", "high", "critical"})
        self.assertIn("probabilities", body)
        self.assertIn("top_risk_factors", body)


if __name__ == "__main__":
    unittest.main()
