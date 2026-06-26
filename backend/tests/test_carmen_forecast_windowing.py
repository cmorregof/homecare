import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.carmen_forecast.baselines import patient_level_train_test_split
from ml.carmen_forecast.synthetic import generate_synthetic_carmen_data
from ml.carmen_forecast.windowing import make_prediction_windows


class CarmenForecastWindowingTest(unittest.TestCase):
    def test_windowing_returns_non_empty_outputs(self):
        frame = generate_synthetic_carmen_data(n_patients=10, observations_per_patient=6, random_state=11)
        X, y, metadata = make_prediction_windows(frame, lookback_hours=24, horizon_hours=6)
        self.assertFalse(X.empty)
        self.assertEqual(len(X), len(y))
        self.assertEqual(len(X), len(metadata))
        self.assertIn("systolic_bp__last", X.columns)
        self.assertIn("patient_id", metadata.columns)

    def test_windowing_excludes_censored_horizons_by_default(self):
        frame = generate_synthetic_carmen_data(n_patients=5, observations_per_patient=6, random_state=17)
        X, y, metadata = make_prediction_windows(frame)
        self.assertEqual(len(X), 25)
        self.assertFalse(y.isna().any())
        self.assertTrue(metadata["horizon_observed"].all())

    def test_patient_level_split_avoids_leakage(self):
        frame = generate_synthetic_carmen_data(n_patients=18, observations_per_patient=6, random_state=3)
        X, y, metadata = make_prediction_windows(frame)
        split = patient_level_train_test_split(metadata, y, test_size=0.3, random_state=5)
        self.assertTrue(split.train_patients.isdisjoint(split.test_patients))
        train_ids = set(metadata.iloc[split.train_indices]["patient_id"])
        test_ids = set(metadata.iloc[split.test_indices]["patient_id"])
        self.assertTrue(train_ids.isdisjoint(test_ids))


if __name__ == "__main__":
    unittest.main()
