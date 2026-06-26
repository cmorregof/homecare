import math
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.carmen_forecast.metrics import evaluate_binary_forecast


class CarmenForecastMetricsTest(unittest.TestCase):
    def test_metrics_return_expected_keys(self):
        metrics = evaluate_binary_forecast(
            y_true=[0, 1, 0, 1, 1, 0],
            y_prob=[0.05, 0.82, 0.20, 0.74, 0.33, 0.11],
            threshold=0.5,
        )
        expected_keys = {
            "auroc",
            "auprc",
            "brier",
            "sensitivity",
            "specificity",
            "precision",
            "f1",
            "confusion_matrix",
            "critical_miss_rate",
            "threshold",
        }
        self.assertTrue(expected_keys.issubset(metrics.keys()))
        self.assertFalse(math.isnan(metrics["auroc"]))
        self.assertIn("fn", metrics["confusion_matrix"])


if __name__ == "__main__":
    unittest.main()
