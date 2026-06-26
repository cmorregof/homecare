from __future__ import annotations

import argparse
import json

from ml.carmen_forecast.alerts import build_carmen_alert
from ml.carmen_forecast.baselines import compare_rule_based_baseline, run_baseline_experiment
from ml.carmen_forecast.calibration import summarize_calibration
from ml.carmen_forecast.clinical_utility import decision_curve_analysis
from ml.carmen_forecast.synthetic import generate_synthetic_carmen_data
from ml.carmen_forecast.windowing import make_prediction_windows


def run_demo() -> int:
    data = generate_synthetic_carmen_data()
    X, y, metadata = make_prediction_windows(data)
    experiment = run_baseline_experiment(X, y, metadata)
    calibration = summarize_calibration(experiment["y_test"], experiment["y_prob"])
    decision_curve = decision_curve_analysis(experiment["y_test"], experiment["y_prob"])
    rule_metrics = compare_rule_based_baseline(experiment["X_test"], experiment["y_test"])

    top_index = int(experiment["y_prob"].argmax())
    feature_row = experiment["X_test"].iloc[top_index]
    metadata_row = experiment["test_metadata"].iloc[top_index]
    alert = build_carmen_alert(
        patient_id=str(metadata_row["patient_id"]),
        prediction_time=metadata_row["prediction_time"],
        horizon_hours=int(metadata_row["horizon_hours"]),
        risk_probability=float(experiment["y_prob"][top_index]),
        feature_row=feature_row,
    )

    output = {
        "experiment": "CARMEN-Forecast synthetic demo",
        "model_name": experiment["model_name"],
        "n_rows": int(len(data)),
        "n_windows": int(len(X)),
        "split": experiment["split"],
        "metrics": experiment["metrics"],
        "rule_baseline_metrics": rule_metrics,
        "calibration": calibration,
        "decision_curve": decision_curve[:3],
        "example_alert": alert.model_dump(mode="json"),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CARMEN-Forecast research CLI")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("demo", help="Run the synthetic minimal viable experiment.")

    args = parser.parse_args()
    if args.command == "demo":
        return run_demo()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
