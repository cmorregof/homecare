from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.carmen_forecast.metrics import evaluate_binary_forecast


@dataclass
class PatientSplit:
    train_patients: set[str]
    test_patients: set[str]
    train_indices: list[int]
    test_indices: list[int]


def patient_level_train_test_split(
    metadata: pd.DataFrame,
    y,
    test_size: float = 0.25,
    random_state: int = 42,
) -> PatientSplit:
    split_frame = metadata.copy()
    split_frame["label"] = np.asarray(y, dtype=int)
    patient_labels = split_frame.groupby("patient_id", as_index=False)["label"].max()
    stratify = patient_labels["label"] if patient_labels["label"].nunique() > 1 else None
    if stratify is not None and stratify.value_counts().min() < 2:
        stratify = None

    train_patients, test_patients = train_test_split(
        patient_labels["patient_id"],
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )
    train_patients_set = set(train_patients.tolist())
    test_patients_set = set(test_patients.tolist())
    train_indices = split_frame.index[split_frame["patient_id"].isin(train_patients_set)].tolist()
    test_indices = split_frame.index[split_frame["patient_id"].isin(test_patients_set)].tolist()
    return PatientSplit(
        train_patients=train_patients_set,
        test_patients=test_patients_set,
        train_indices=train_indices,
        test_indices=test_indices,
    )


def build_baseline_estimator(random_state: int = 42):
    try:
        from lightgbm import LGBMClassifier

        model = LGBMClassifier(
            n_estimators=150,
            learning_rate=0.05,
            num_leaves=31,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=1,
        )
        model_name = "lightgbm"
    except Exception:
        # Keep the fallback local and simple for environments without LightGBM.
        model = GradientBoostingClassifier(random_state=random_state)
        model_name = "gradient_boosting"

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", model),
        ]
    )
    return model_name, pipeline


def run_baseline_experiment(
    X: pd.DataFrame,
    y,
    metadata: pd.DataFrame,
    threshold: float = 0.5,
    random_state: int = 42,
) -> dict[str, object]:
    split = patient_level_train_test_split(metadata=metadata, y=y, random_state=random_state)
    X_train = X.iloc[split.train_indices]
    X_test = X.iloc[split.test_indices]
    y_train = np.asarray(y)[split.train_indices]
    y_test = np.asarray(y)[split.test_indices]

    model_name, pipeline = build_baseline_estimator(random_state=random_state)
    if len(np.unique(y_train)) < 2:
        pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        )
        model_name = "logistic_regression"

    pipeline.fit(X_train, y_train)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    metrics = evaluate_binary_forecast(y_test, y_prob, threshold=threshold)

    return {
        "model_name": model_name,
        "model": pipeline,
        "metrics": metrics,
        "y_test": y_test,
        "y_prob": y_prob,
        "X_test": X_test,
        "test_metadata": metadata.iloc[split.test_indices].reset_index(drop=True),
        "split": {
            "train_patients": sorted(split.train_patients),
            "test_patients": sorted(split.test_patients),
            "train_windows": len(split.train_indices),
            "test_windows": len(split.test_indices),
        },
    }


def rule_based_forecast_baseline(window_row: pd.Series | dict[str, object]) -> dict[str, object]:
    row = pd.Series(window_row)
    severe_symptom = max(
        _value(row, "pain_score__max"),
        _value(row, "dizziness_score__max"),
        _value(row, "dyspnea_score__max"),
    ) >= 8

    critical = any(
        [
            _value(row, "systolic_bp__last") > 180,
            _value(row, "systolic_bp__last") < 80,
            _value(row, "heart_rate__last") > 130,
            _value(row, "heart_rate__last") < 40,
            _value(row, "oxygen_saturation__last") < 88,
            _value(row, "glucose__last") > 400,
            _value(row, "glucose__last") < 50,
            severe_symptom,
        ]
    )
    high = any(
        [
            _value(row, "oxygen_saturation__last") < 92,
            _value(row, "heart_rate__last") > 115,
            _value(row, "systolic_bp__last") > 160,
            _value(row, "medication_adherence__mean") < 0.65,
        ]
    )
    if critical:
        return {"probability": 0.95, "risk_tier": "critical", "override": True}
    if high:
        return {"probability": 0.70, "risk_tier": "high", "override": False}
    return {"probability": 0.15, "risk_tier": "low", "override": False}


def compare_rule_based_baseline(X: pd.DataFrame, y, threshold: float = 0.5) -> dict[str, object]:
    probabilities = np.array([rule_based_forecast_baseline(row)["probability"] for _, row in X.iterrows()])
    return evaluate_binary_forecast(y, probabilities, threshold=threshold)


def _value(row: pd.Series, key: str) -> float:
    value = row.get(key, 0.0)
    return float(0.0 if pd.isna(value) else value)
