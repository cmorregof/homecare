import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.etl.unify_datasets import generate_synthetic_dataset, split_and_balance_dataset
from ml.predict import predict_risk
from ml.preprocessing import FEATURES, TARGET, normalize_feature_payload
from ml.train import train_all_models


class MlPipelineTest(unittest.TestCase):
    def test_feature_normalization_adds_derived_values(self):
        features = normalize_feature_payload(
            {
                "systolic_bp": 150,
                "diastolic_bp": 90,
                "heart_rate": 82,
            }
        )
        self.assertEqual(set(FEATURES), set(features.keys()))
        self.assertEqual(features["pulse_pressure"], 60)
        self.assertAlmostEqual(features["map"], 110)

    def test_synthetic_etl_outputs_split_and_balanced_train(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "unified_dataset.csv"
            train_resampled = Path(tmp) / "train_resampled.csv"
            data = generate_synthetic_dataset(rows=120)
            unified, balanced = split_and_balance_dataset(data, output, train_resampled)

            self.assertTrue(output.exists())
            self.assertTrue(train_resampled.exists())
            self.assertTrue(set(FEATURES + [TARGET, "split"]).issubset(unified.columns))
            self.assertIn("train_resampled", set(balanced["split"]))

    def test_prediction_fallback_without_model(self):
        result = predict_risk(
            {
                "systolic_bp": 182,
                "diastolic_bp": 94,
                "heart_rate": 88,
            },
            model_path="/tmp/homecareccv-nonexistent-model.pkl",
        )
        self.assertEqual(result["risk_level"], "critical")
        self.assertEqual(result["model_used"], "clinical_rules_fallback")
        self.assertTrue(result["top_risk_factors"])

    def test_training_smoke_with_fast_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dataset_path = tmp_path / "unified_dataset.csv"
            model_path = tmp_path / "best_model.pkl"
            results_path = tmp_path / "comparison_results.json"
            metadata_path = tmp_path / "training_metadata.json"
            data = generate_synthetic_dataset(rows=180)
            unified, _ = split_and_balance_dataset(data, dataset_path, tmp_path / "train_resampled.csv")
            report = train_all_models(
                dataset_path=dataset_path,
                model_path=model_path,
                results_path=results_path,
                metadata_path=metadata_path,
                only_models=["logistic_regression"],
            )

            self.assertTrue(model_path.exists())
            self.assertTrue(results_path.exists())
            self.assertTrue(metadata_path.exists())
            self.assertEqual(report["best_model"], "logistic_regression")
            self.assertEqual(len(unified), 180)


if __name__ == "__main__":
    unittest.main()
