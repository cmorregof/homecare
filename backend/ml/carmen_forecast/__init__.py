"""CARMEN-Forecast research scaffold for short-horizon deterioration forecasting."""

from ml.carmen_forecast.alerts import CarmenForecastAlert, build_carmen_alert
from ml.carmen_forecast.baselines import (
    patient_level_train_test_split,
    run_baseline_experiment,
    rule_based_forecast_baseline,
)
from ml.carmen_forecast.metrics import evaluate_binary_forecast
from ml.carmen_forecast.synthetic import generate_synthetic_carmen_data
from ml.carmen_forecast.windowing import make_prediction_windows

__all__ = [
    "CarmenForecastAlert",
    "build_carmen_alert",
    "evaluate_binary_forecast",
    "generate_synthetic_carmen_data",
    "make_prediction_windows",
    "patient_level_train_test_split",
    "rule_based_forecast_baseline",
    "run_baseline_experiment",
]
