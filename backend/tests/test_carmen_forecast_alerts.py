import sys
import unittest
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.carmen_forecast.alerts import build_carmen_alert
from ml.carmen_forecast.baselines import rule_based_forecast_baseline


class CarmenForecastAlertsTest(unittest.TestCase):
    def test_alert_contains_safety_note_and_risk_tier(self):
        feature_row = pd.Series(
            {
                "oxygen_saturation__slope": -0.6,
                "heart_rate__slope": 1.4,
                "medication_adherence__mean": 0.58,
            }
        )
        alert = build_carmen_alert(
            patient_id="P001",
            prediction_time="2026-06-26T14:00:00",
            horizon_hours=6,
            risk_probability=0.82,
            feature_row=feature_row,
        )
        self.assertEqual(alert.risk_tier, "critical")
        self.assertIn("Human clinical review is required", alert.safety_note)

    def test_rule_based_override_flags_critical_case(self):
        feature_row = pd.Series(
            {
                "systolic_bp__last": 190,
                "heart_rate__last": 138,
                "oxygen_saturation__last": 86,
                "glucose__last": 120,
                "pain_score__max": 4,
                "dizziness_score__max": 4,
                "dyspnea_score__max": 5,
            }
        )
        baseline = rule_based_forecast_baseline(feature_row)
        self.assertTrue(baseline["override"])
        self.assertEqual(baseline["risk_tier"], "critical")


if __name__ == "__main__":
    unittest.main()
