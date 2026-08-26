import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.predict import predict_risk
from utils.risk_levels import apply_hard_overrides, hard_override_tier


BASE_VITALS = {
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "heart_rate": 75,
    "oxygen_saturation": 97,
    "glucose": 110,
}


def _vitals(**overrides):
    vitals = dict(BASE_VITALS)
    vitals.update(overrides)
    return vitals


class HardOverrideTableATest(unittest.TestCase):
    """Tabla A: el override duro sube el tier a critical por encima de cualquier modelo."""

    def assert_critical_override(self, prediction, feature):
        self.assertEqual(prediction["risk_level"], "critical")
        self.assertTrue(prediction["override_applied"])
        triggered = {factor["feature"] for factor in prediction["override_factors"]}
        self.assertIn(feature, triggered)

    def test_caso_1_normal_sin_override(self):
        prediction = predict_risk(_vitals())
        self.assertEqual(prediction["risk_level"], "low")
        self.assertFalse(prediction["override_applied"])

    def test_caso_2_spo2_84_critical(self):
        prediction = predict_risk(_vitals(oxygen_saturation=84))
        self.assert_critical_override(prediction, "oxygen_saturation")

    def test_caso_3_spo2_88_borde_sin_override(self):
        prediction = predict_risk(_vitals(oxygen_saturation=88))
        self.assertFalse(prediction["override_applied"])

    def test_caso_4_sistolica_185_critical(self):
        prediction = predict_risk(_vitals(systolic_bp=185, diastolic_bp=95))
        self.assert_critical_override(prediction, "systolic_bp")

    def test_caso_5_sistolica_75_critical(self):
        prediction = predict_risk(_vitals(systolic_bp=75, diastolic_bp=50))
        self.assert_critical_override(prediction, "systolic_bp")

    def test_caso_6_fc_135_critical(self):
        prediction = predict_risk(_vitals(heart_rate=135))
        self.assert_critical_override(prediction, "heart_rate")

    def test_caso_7_fc_38_critical(self):
        prediction = predict_risk(_vitals(heart_rate=38))
        self.assert_critical_override(prediction, "heart_rate")

    def test_caso_8_glucosa_420_critical(self):
        prediction = predict_risk(_vitals(glucose=420))
        self.assert_critical_override(prediction, "glucose")

    def test_caso_9_glucosa_45_critical(self):
        prediction = predict_risk(_vitals(glucose=45))
        self.assert_critical_override(prediction, "glucose")

    def test_caso_10_glucosa_no_reportada_sin_override(self):
        vitals = _vitals()
        vitals.pop("glucose")
        prediction = predict_risk(vitals)
        self.assertFalse(prediction["override_applied"])


class HardOverrideSemanticsTest(unittest.TestCase):
    def test_override_solo_sube_nunca_baja(self):
        prediction = {"risk_level": "critical", "probabilities": {"critical": 0.8}}
        result = apply_hard_overrides(prediction, BASE_VITALS)
        self.assertEqual(result["risk_level"], "critical")

    def test_override_marca_probabilidad_minima(self):
        prediction = {"risk_level": "low", "probabilities": {"low": 1.0, "critical": 0.0}}
        result = apply_hard_overrides(prediction, _vitals(oxygen_saturation=84))
        self.assertEqual(result["risk_level"], "critical")
        self.assertGreaterEqual(result["risk_probability"], 0.9)

    def test_override_aplica_en_fallback_sin_modelo(self):
        prediction = predict_risk(_vitals(oxygen_saturation=84), model_path="no/existe.pkl")
        self.assertEqual(prediction["risk_level"], "critical")
        self.assertEqual(prediction["model_used"], "clinical_rules_fallback")

    def test_valores_no_numericos_no_disparan_override(self):
        self.assertIsNone(hard_override_tier({"systolic_bp": "bananas", "glucose": ""}))

    def test_factores_del_override_llegan_a_la_explicacion(self):
        prediction = predict_risk(_vitals(oxygen_saturation=84))
        top_features = [factor["feature"] for factor in prediction["top_risk_factors"]]
        self.assertIn("oxygen_saturation", top_features)


if __name__ == "__main__":
    unittest.main()
