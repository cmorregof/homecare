import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.carmen_forecast.synthetic import generate_synthetic_carmen_data


class CarmenForecastSyntheticTest(unittest.TestCase):
    def test_synthetic_data_has_expected_columns(self):
        frame = generate_synthetic_carmen_data(n_patients=12, observations_per_patient=8, random_state=7)
        expected = {
            "patient_id",
            "timestamp",
            "age",
            "sex",
            "systolic_bp",
            "diastolic_bp",
            "heart_rate",
            "oxygen_saturation",
            "glucose",
            "temperature",
            "pain_score",
            "dizziness_score",
            "dyspnea_score",
            "medication_adherence",
            "activity_level",
            "previous_event_flag",
            "risk_state",
            "future_deterioration_6h",
            "horizon_observed",
            "is_censored",
        }
        self.assertTrue(expected.issubset(frame.columns))
        self.assertEqual(len(frame), 96)
        self.assertTrue(set(frame["risk_state"]).issubset({"low", "moderate", "high", "critical"}))

    def test_last_observation_is_censored_not_negative(self):
        frame = generate_synthetic_carmen_data(n_patients=4, observations_per_patient=5, random_state=13)
        last_rows = frame.sort_values(["patient_id", "timestamp"]).groupby("patient_id").tail(1)
        self.assertTrue(last_rows["future_deterioration_6h"].isna().all())
        self.assertFalse(last_rows["horizon_observed"].any())
        self.assertTrue(last_rows["is_censored"].all())


if __name__ == "__main__":
    unittest.main()
