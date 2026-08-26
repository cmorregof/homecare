import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.forecast import forecast_deterioration, format_forecast_note, load_forecast_artifact


def _report(hours: float, **vitals):
    base = {
        "recorded_at": f"2026-08-25T{int(hours):02d}:00:00+00:00",
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "heart_rate": 75,
        "oxygen_saturation": 97,
        "respiratory_rate": 16,
        "temperature": 36.5,
        "weight_kg": 70,
    }
    base.update(vitals)
    return base


STABLE_HISTORY = [_report(0), _report(6), _report(12)]
DETERIORATING_HISTORY = [
    _report(0, oxygen_saturation=94, heart_rate=95),
    _report(6, oxygen_saturation=90, heart_rate=112, respiratory_rate=24),
    _report(12, oxygen_saturation=86, heart_rate=128, respiratory_rate=30, systolic_bp=88),
]

CLINICAL_INFO = {"age": 70, "gender": "female"}


class ForecastInferenceTest(unittest.TestCase):
    def test_artifact_loads(self):
        artifact = load_forecast_artifact("ml/models/carmen_forecast_tfm_home6h.pt")
        self.assertIsNotNone(artifact)
        self.assertEqual(len(artifact["config"]["concepts"]), 7)

    def test_forecast_returns_three_horizons(self):
        forecast = forecast_deterioration(STABLE_HISTORY, CLINICAL_INFO)
        self.assertIsNotNone(forecast)
        self.assertEqual(set(forecast["probabilities"]), {"6h", "12h", "24h"})
        for probability in forecast["probabilities"].values():
            self.assertGreaterEqual(probability, 0.0)
            self.assertLessEqual(probability, 1.0)
        self.assertEqual(forecast["n_reports"], 3)

    def test_deteriorating_patient_scores_higher_than_stable(self):
        stable = forecast_deterioration(STABLE_HISTORY, CLINICAL_INFO)
        worse = forecast_deterioration(DETERIORATING_HISTORY, CLINICAL_INFO)
        self.assertGreater(worse["probabilities"]["6h"], stable["probabilities"]["6h"])

    def test_single_report_still_produces_forecast(self):
        forecast = forecast_deterioration([_report(0)], CLINICAL_INFO)
        self.assertIsNotNone(forecast)
        self.assertEqual(forecast["n_reports"], 1)

    def test_missing_artifact_degrades_to_none(self):
        forecast = forecast_deterioration(
            STABLE_HISTORY, CLINICAL_INFO, model_path="no/existe.pt"
        )
        self.assertIsNone(forecast)

    def test_empty_history_returns_none(self):
        self.assertIsNone(forecast_deterioration([], CLINICAL_INFO))

    def test_note_is_doctor_facing_and_labeled_preliminary(self):
        forecast = forecast_deterioration(STABLE_HISTORY, CLINICAL_INFO)
        note = format_forecast_note(forecast)
        self.assertIn("preliminar", note)
        self.assertIn("no validado en domicilio", note)
        self.assertIn("equipo clínico", note)


if __name__ == "__main__":
    unittest.main()
