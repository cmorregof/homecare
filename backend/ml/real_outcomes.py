from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

from ml.explainability import compute_shap_values, top_risk_factors
from ml.preprocessing import FEATURES

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.etl.unify_datasets import (  # noqa: E402
    DATA_DIR,
    REAL_OUTCOME_DIR,
    load_real_outcome_cohorts,
    save_real_outcome_cohorts,
)


RANDOM_STATE = 42
CV_FOLDS = 5
CV_SAMPLE_LIMIT = 25000
BOOTSTRAP_ITERATIONS = 200
NEAR_CONSTANT_THRESHOLD = 0.995
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "ml" / "models" / "real_outcomes"
DEFAULT_RESULTS_PATH = DEFAULT_OUTPUT_DIR / "real_outcome_results.json"

COHORT_LABELS = {
    "stroke": "Stroke Prediction Dataset",
    "cvd": "Cardiovascular Disease Dataset",
    "heart_failure": "Heart Failure Prediction Dataset",
}

LEAKAGE_GUARDS = {
    "stroke": {
        "target": "stroke",
        "forbidden_features": ["stroke_history"],
        "source_outcome": "stroke",
    },
    "cvd": {
        "target": "cardio",
        "forbidden_features": ["heart_disease_history"],
        "source_outcome": "cardio",
    },
    "heart_failure": {
        "target": "HeartDisease",
        "forbidden_features": ["heart_disease_history"],
        "source_outcome": "HeartDisease",
    },
}


@dataclass
class PreparedCohort:
    name: str
    frame: pd.DataFrame
    features: list[str]
    dropped_constant_features: list[str]
    leakage_removed_features: list[str]
    leakage_passed: bool
    split_counts: dict[str, int]


def build_real_outcome_model_registry(strict_external: bool = False) -> dict[str, Any]:
    models: dict[str, Any] = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
        "decision_tree": DecisionTreeClassifier(class_weight="balanced", random_state=RANDOM_STATE),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=200, random_state=RANDOM_STATE),
        "svm": LinearSVC(class_weight="balanced", random_state=RANDOM_STATE, dual="auto", max_iter=5000),
        "knn": KNeighborsClassifier(n_neighbors=15),
        "mlp": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300, random_state=RANDOM_STATE),
    }
    optional_imports = {
        "xgboost": ("xgboost", "XGBClassifier"),
        "lightgbm": ("lightgbm", "LGBMClassifier"),
        "catboost": ("catboost", "CatBoostClassifier"),
    }
    for name, (module_name, class_name) in optional_imports.items():
        try:
            module = __import__(module_name, fromlist=[class_name])
            model_class = getattr(module, class_name)
            if name == "xgboost":
                models[name] = model_class(
                    n_estimators=200,
                    eval_metric="logloss",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                )
            elif name == "lightgbm":
                models[name] = model_class(
                    n_estimators=200,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    verbose=-1,
                )
            else:
                models[name] = model_class(
                    iterations=200,
                    verbose=0,
                    random_state=RANDOM_STATE,
                    thread_count=-1,
                    allow_writing_files=False,
                    auto_class_weights="Balanced",
                )
        except Exception:
            if strict_external:
                raise
            models[name] = None
    return {
        "logistic_regression": models["logistic_regression"],
        "decision_tree": models["decision_tree"],
        "random_forest": models["random_forest"],
        "gradient_boosting": models["gradient_boosting"],
        "xgboost": models["xgboost"],
        "lightgbm": models["lightgbm"],
        "catboost": models["catboost"],
        "svm": models["svm"],
        "knn": models["knn"],
        "mlp": models["mlp"],
    }


def run_real_outcome_pipeline(
    *,
    data_dir: Path = DATA_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    results_path: Path = DEFAULT_RESULTS_PATH,
    strict_external: bool = False,
    only_models: list[str] | None = None,
    bootstrap_iterations: int = BOOTSTRAP_ITERATIONS,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    cohorts = load_real_outcome_cohorts(data_dir)
    cohort_paths = save_real_outcome_cohorts(cohorts, REAL_OUTCOME_DIR)
    registry = build_real_outcome_model_registry(strict_external=strict_external)
    if only_models:
        registry = {name: model for name, model in registry.items() if name in set(only_models)}

    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "design": {
            "target": "real binary outcome per cohort",
            "legacy_synthetic_risk_level": "kept as clinical rule baseline/audit, not as ML target",
            "selection_metric": "validation_roc_auc",
            "random_state": RANDOM_STATE,
            "tripod_ai_alignment": [
                "source cohorts documented",
                "outcome definitions are real dataset outcomes",
                "candidate predictors audited for leakage",
                "held-out test split preserved",
                "calibration and decision-curve analysis reported",
                "subgroup performance by sex and age band reported",
                "bootstrap confidence intervals reported",
            ],
        },
        "cohort_dataset_paths": {name: _repo_path(path) for name, path in cohort_paths.items()},
        "cohorts": {},
        "summary": [],
    }

    for cohort_name, frame in cohorts.items():
        prepared = prepare_cohort(cohort_name, frame)
        cohort_result = evaluate_cohort(
            prepared,
            registry,
            output_dir=output_dir,
            figures_dir=figures_dir,
            bootstrap_iterations=bootstrap_iterations,
        )
        report["cohorts"][cohort_name] = cohort_result
        best = cohort_result["best_model"]
        best_result = cohort_result["models"][best]
        baseline = cohort_result["clinical_rule_baseline"]["test"]
        report["summary"].append(
            {
                "cohort": cohort_name,
                "label": COHORT_LABELS.get(cohort_name, cohort_name),
                "rows": int(len(frame)),
                "outcome_prevalence": float(frame["outcome"].mean()),
                "best_model": best,
                "test_roc_auc": best_result["test"]["roc_auc"],
                "test_auc_pr": best_result["test"]["auc_pr"],
                "test_brier": best_result["test"]["brier_score"],
                "rule_roc_auc": baseline["roc_auc"],
                "rule_auc_pr": baseline["auc_pr"],
                "rule_brier": baseline["brier_score"],
                "delta_mean_net_benefit_vs_rule": best_result["decision_curve"]["delta_mean_net_benefit_vs_rule"],
                "leakage_passed": prepared.leakage_passed,
                "dropped_constant_features": prepared.dropped_constant_features,
                "leakage_removed_features": prepared.leakage_removed_features,
            }
        )

    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(_json_safe(report), indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def prepare_cohort(cohort_name: str, frame: pd.DataFrame) -> PreparedCohort:
    guard = LEAKAGE_GUARDS[cohort_name]
    candidate_features = [feature for feature in FEATURES if feature in frame.columns]
    leakage_removed = [feature for feature in guard["forbidden_features"] if feature in candidate_features]
    candidate_features = [feature for feature in candidate_features if feature not in leakage_removed]
    dropped_constant = _constant_or_near_constant_features(frame, candidate_features)
    features = [feature for feature in candidate_features if feature not in dropped_constant]
    leakage_passed = not set(guard["forbidden_features"]).intersection(features)
    if not leakage_passed:
        raise ValueError(f"Leakage guard failed for {cohort_name}: {guard['forbidden_features']}")
    train, validation, test = split_cohort(frame)
    split_counts = {"train": len(train), "validation": len(validation), "test": len(test)}
    prepared_frame = pd.concat(
        [
            train.assign(split="train"),
            validation.assign(split="validation"),
            test.assign(split="test"),
        ],
        ignore_index=True,
    )
    return PreparedCohort(
        name=cohort_name,
        frame=prepared_frame,
        features=features,
        dropped_constant_features=dropped_constant,
        leakage_removed_features=leakage_removed,
        leakage_passed=leakage_passed,
        split_counts=split_counts,
    )


def split_cohort(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train, temp = train_test_split(
        frame,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=frame["outcome"],
    )
    validation, test = train_test_split(
        temp,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=temp["outcome"],
    )
    return train.copy(), validation.copy(), test.copy()


def evaluate_cohort(
    prepared: PreparedCohort,
    registry: dict[str, Any],
    *,
    output_dir: Path,
    figures_dir: Path,
    bootstrap_iterations: int,
) -> dict[str, Any]:
    train = prepared.frame[prepared.frame["split"] == "train"].copy()
    validation = prepared.frame[prepared.frame["split"] == "validation"].copy()
    test = prepared.frame[prepared.frame["split"] == "test"].copy()

    x_train, y_train = train[prepared.features], train["outcome"].astype(int)
    x_validation, y_validation = validation[prepared.features], validation["outcome"].astype(int)
    x_test, y_test = test[prepared.features], test["outcome"].astype(int)
    rule_baseline = evaluate_clinical_rule_baseline(validation, test, figures_dir, prepared.name)

    model_results: dict[str, Any] = {}
    fitted_models: dict[str, Any] = {}
    for model_name, estimator in registry.items():
        print(f"[real-outcomes] {prepared.name}: training {model_name}", flush=True)
        if estimator is None:
            model_results[model_name] = {"status": "skipped", "reason": "optional dependency unavailable"}
            continue
        try:
            pipeline = Pipeline(
                steps=[
                    (
                        "preprocess",
                        Pipeline(
                            [
                                ("imputer", SimpleImputer(strategy="median")),
                                ("scaler", StandardScaler()),
                            ]
                        ),
                    ),
                    ("model", clone(estimator)),
                ]
            )
            cv_scores = cross_validate_roc_auc(pipeline, x_train, y_train)
            pipeline.fit(x_train, y_train)
            raw_validation_prob = predict_positive_probability(pipeline, x_validation)
            raw_test_prob = predict_positive_probability(pipeline, x_test)
            calibration = choose_calibration(pipeline, x_validation, y_validation, raw_validation_prob)
            final_model = calibration["model"]
            validation_prob = calibration["validation_probability"]
            test_prob = (
                predict_positive_probability(final_model, x_test)
                if calibration["method"] != "none"
                else raw_test_prob
            )
            validation_metrics = binary_metrics(y_validation, validation_prob)
            test_metrics = binary_metrics(y_test, test_prob)
            ci = bootstrap_metric_intervals(y_test.to_numpy(), test_prob, iterations=bootstrap_iterations)
            decision_curve = decision_curve_report(
                y_test.to_numpy(),
                test_prob,
                rule_baseline["test"]["probability"],
            )
            calibration_plot = plot_calibration_curve(
                y_test.to_numpy(),
                test_prob,
                figures_dir / f"{prepared.name}_{model_name}_calibration.png",
                title=f"{prepared.name} / {model_name}",
            )
            decision_plot = plot_decision_curve(
                y_test.to_numpy(),
                test_prob,
                rule_baseline["test"]["probability"],
                figures_dir / f"{prepared.name}_{model_name}_decision_curve.png",
                title=f"{prepared.name} / {model_name}",
            )
            shap_values = representative_shap_values(pipeline, x_test, test_prob, prepared.features)
            model_results[model_name] = {
                "status": "trained",
                "train_rows": int(len(x_train)),
                "validation_rows": int(len(x_validation)),
                "test_rows": int(len(x_test)),
                "features_used": prepared.features,
                "cv_roc_auc_mean": float(np.mean(cv_scores)) if len(cv_scores) else None,
                "cv_roc_auc_std": float(np.std(cv_scores)) if len(cv_scores) else None,
                "calibration": {
                    "selected_method": calibration["method"],
                    "raw_validation_brier": calibration["raw_validation_brier"],
                    "selected_validation_brier": calibration["selected_validation_brier"],
                },
                "validation": validation_metrics,
                "test": {key: value for key, value in test_metrics.items() if key != "probability"},
                "bootstrap_ci": ci,
                "decision_curve": decision_curve,
                "subgroups": subgroup_metrics(test, test_prob),
                "shap_top_features": top_risk_factors(shap_values, x_test.iloc[int(np.argmax(test_prob))].to_dict()),
                "figures": {
                    "calibration": _repo_path(calibration_plot),
                    "decision_curve": _repo_path(decision_plot),
                },
            }
            fitted_models[model_name] = final_model
        except Exception as exc:
            model_results[model_name] = {"status": "failed", "reason": str(exc)}
            print(f"[real-outcomes] {prepared.name}: {model_name} failed: {exc}", flush=True)

    best_model = select_best_real_outcome_model(model_results)
    best_artifact = None
    if best_model in fitted_models:
        cohort_dir = output_dir / prepared.name
        cohort_dir.mkdir(parents=True, exist_ok=True)
        best_artifact = cohort_dir / "best_model.pkl"
        joblib.dump(
            {
                "model": fitted_models[best_model],
                "model_name": best_model,
                "cohort": prepared.name,
                "features": prepared.features,
                "target": "outcome",
                "trained_at": datetime.now(UTC).isoformat(),
            },
            best_artifact,
        )

    return {
        "label": COHORT_LABELS.get(prepared.name, prepared.name),
        "source_outcome": LEAKAGE_GUARDS[prepared.name]["source_outcome"],
        "target": "outcome",
        "rows": int(len(prepared.frame)),
        "outcome_prevalence": float(prepared.frame["outcome"].mean()),
        "split_counts": prepared.split_counts,
        "features_used": prepared.features,
        "leakage_audit": {
            "target_source_column": LEAKAGE_GUARDS[prepared.name]["source_outcome"],
            "removed_target_derived_features": prepared.leakage_removed_features,
            "forbidden_features_absent_from_model_matrix": prepared.leakage_passed,
        },
        "constant_feature_audit": {
            "threshold": NEAR_CONSTANT_THRESHOLD,
            "dropped_features": prepared.dropped_constant_features,
        },
        "clinical_rule_baseline": {
            "description": "MEWS/Framingham-style rule score evaluated against real outcome; not used as ML target.",
            "test": {key: value for key, value in rule_baseline["test"].items() if key != "probability"},
            "figures": rule_baseline["figures"],
        },
        "best_model": best_model,
        "best_model_artifact": _repo_path(best_artifact) if best_artifact else None,
        "models": model_results,
    }


def evaluate_clinical_rule_baseline(
    validation: pd.DataFrame,
    test: pd.DataFrame,
    figures_dir: Path,
    cohort_name: str,
) -> dict[str, Any]:
    y_validation = validation["outcome"].astype(int)
    y_test = test["outcome"].astype(int)
    validation_score = validation["clinical_rule_score"].astype(float).to_numpy().reshape(-1, 1)
    test_score = test["clinical_rule_score"].astype(float).to_numpy().reshape(-1, 1)
    calibrator = LogisticRegression(random_state=RANDOM_STATE)
    calibrator.fit(validation_score, y_validation)
    test_probability = calibrator.predict_proba(test_score)[:, 1]
    test_metrics = binary_metrics(y_test, test_probability)
    test_metrics["raw_score_roc_auc"] = safe_roc_auc(y_test, test["clinical_rule_score"].to_numpy())
    calibration_plot = plot_calibration_curve(
        y_test.to_numpy(),
        test_probability,
        figures_dir / f"{cohort_name}_clinical_rule_calibration.png",
        title=f"{cohort_name} / clinical rule baseline",
    )
    return {
        "test": test_metrics,
        "figures": {
            "calibration": _repo_path(calibration_plot),
        },
    }


def choose_calibration(
    pipeline: Any,
    x_validation: pd.DataFrame,
    y_validation: pd.Series,
    raw_validation_probability: np.ndarray,
) -> dict[str, Any]:
    raw_brier = float(brier_score_loss(y_validation, raw_validation_probability))
    best: dict[str, Any] = {
        "method": "none",
        "model": pipeline,
        "validation_probability": raw_validation_probability,
        "raw_validation_brier": raw_brier,
        "selected_validation_brier": raw_brier,
    }
    for method in ("sigmoid", "isotonic"):
        if method == "isotonic" and min(int(y_validation.sum()), int((1 - y_validation).sum())) < 30:
            continue
        try:
            calibrator = CalibratedClassifierCV(pipeline, cv="prefit", method=method)
            calibrator.fit(x_validation, y_validation)
            probability = calibrator.predict_proba(x_validation)[:, 1]
            brier = float(brier_score_loss(y_validation, probability))
            if brier + 1e-6 < best["selected_validation_brier"]:
                best = {
                    "method": method,
                    "model": calibrator,
                    "validation_probability": probability,
                    "raw_validation_brier": raw_brier,
                    "selected_validation_brier": brier,
                }
        except Exception:
            continue
    return best


def cross_validate_roc_auc(pipeline: Pipeline, x_train: pd.DataFrame, y_train: pd.Series) -> np.ndarray:
    x_cv, y_cv = cv_frame(x_train, y_train)
    min_count = int(y_cv.value_counts().min())
    folds = min(CV_FOLDS, min_count)
    if folds < 2:
        return np.array([])
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    return cross_val_score(pipeline, x_cv, y_cv, cv=cv, scoring="roc_auc")


def cv_frame(x_train: pd.DataFrame, y_train: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    if len(x_train) <= CV_SAMPLE_LIMIT:
        return x_train, y_train
    frame = x_train.copy()
    frame["outcome"] = y_train.to_numpy()
    per_class = max(1, CV_SAMPLE_LIMIT // frame["outcome"].nunique())
    sampled = pd.concat(
        [
            group.sample(min(len(group), per_class), random_state=RANDOM_STATE)
            for _, group in frame.groupby("outcome", group_keys=False)
        ],
        ignore_index=True,
    ).sample(frac=1, random_state=RANDOM_STATE)
    return sampled.drop(columns=["outcome"]), sampled["outcome"].astype(int)


def predict_positive_probability(model: Any, x: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        probability = model.predict_proba(x)
        return np.asarray(probability[:, 1], dtype=float)
    if hasattr(model, "decision_function"):
        score = np.asarray(model.decision_function(x), dtype=float)
        return 1 / (1 + np.exp(-score))
    prediction = np.asarray(model.predict(x), dtype=float)
    return np.clip(prediction, 0, 1)


def binary_metrics(y_true: pd.Series | np.ndarray, probability: np.ndarray) -> dict[str, Any]:
    y_array = np.asarray(y_true, dtype=int)
    prob = np.asarray(probability, dtype=float)
    metrics = {
        "roc_auc": safe_roc_auc(y_array, prob),
        "auc_pr": safe_auc_pr(y_array, prob),
        "brier_score": float(brier_score_loss(y_array, prob)),
        "calibration": calibration_slope_intercept(y_array, prob),
        "probability": prob,
    }
    return metrics


def calibration_slope_intercept(y_true: np.ndarray, probability: np.ndarray) -> dict[str, float | None]:
    if len(np.unique(y_true)) < 2:
        return {"slope": None, "intercept": None}
    clipped = np.clip(probability, 1e-5, 1 - 1e-5)
    logit = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    model = LogisticRegression(penalty=None, solver="lbfgs", max_iter=1000)
    try:
        model.fit(logit, y_true)
        return {
            "slope": float(model.coef_[0][0]),
            "intercept": float(model.intercept_[0]),
        }
    except Exception:
        return {"slope": None, "intercept": None}


def bootstrap_metric_intervals(
    y_true: np.ndarray,
    probability: np.ndarray,
    *,
    iterations: int,
) -> dict[str, dict[str, float | None]]:
    rng = np.random.default_rng(RANDOM_STATE)
    values: dict[str, list[float]] = {"roc_auc": [], "auc_pr": [], "brier_score": []}
    n = len(y_true)
    for _ in range(iterations):
        indices = rng.integers(0, n, n)
        sample_y = y_true[indices]
        sample_p = probability[indices]
        if len(np.unique(sample_y)) < 2:
            continue
        values["roc_auc"].append(float(roc_auc_score(sample_y, sample_p)))
        values["auc_pr"].append(float(average_precision_score(sample_y, sample_p)))
        values["brier_score"].append(float(brier_score_loss(sample_y, sample_p)))
    return {
        metric: {
            "low": percentile_or_none(metric_values, 2.5),
            "high": percentile_or_none(metric_values, 97.5),
        }
        for metric, metric_values in values.items()
    }


def decision_curve_report(
    y_true: np.ndarray,
    model_probability: np.ndarray,
    rule_probability: np.ndarray,
) -> dict[str, Any]:
    thresholds = np.round(np.arange(0.05, 0.51, 0.05), 2)
    rows = []
    for threshold in thresholds:
        model_nb = net_benefit(y_true, model_probability, threshold)
        rule_nb = net_benefit(y_true, rule_probability, threshold)
        treat_all = treat_all_net_benefit(y_true, threshold)
        rows.append(
            {
                "threshold": float(threshold),
                "model": model_nb,
                "clinical_rule": rule_nb,
                "treat_all": treat_all,
                "treat_none": 0.0,
                "delta_model_vs_rule": model_nb - rule_nb,
                "delta_model_vs_treat_all": model_nb - treat_all,
            }
        )
    return {
        "thresholds": rows,
        "mean_net_benefit_model": float(np.mean([row["model"] for row in rows])),
        "mean_net_benefit_rule": float(np.mean([row["clinical_rule"] for row in rows])),
        "delta_mean_net_benefit_vs_rule": float(
            np.mean([row["delta_model_vs_rule"] for row in rows])
        ),
        "net_benefit_at_0_20": next(row for row in rows if row["threshold"] == 0.2),
    }


def net_benefit(y_true: np.ndarray, probability: np.ndarray, threshold: float) -> float:
    predicted_positive = probability >= threshold
    tp = float(np.sum((predicted_positive == 1) & (y_true == 1)))
    fp = float(np.sum((predicted_positive == 1) & (y_true == 0)))
    n = float(len(y_true))
    odds = threshold / (1 - threshold)
    return (tp / n) - (fp / n) * odds


def treat_all_net_benefit(y_true: np.ndarray, threshold: float) -> float:
    prevalence = float(np.mean(y_true))
    odds = threshold / (1 - threshold)
    return prevalence - (1 - prevalence) * odds


def subgroup_metrics(test: pd.DataFrame, probability: np.ndarray) -> dict[str, Any]:
    frame = test.copy()
    frame["probability"] = probability
    frame["age_band"] = pd.cut(
        frame["age"],
        bins=[0, 49, 64, 74, 120],
        labels=["<50", "50-64", "65-74", ">=75"],
        include_lowest=True,
    ).astype(str)
    groups: dict[str, Any] = {}
    for group_name, column in {"sex": "gender_encoded", "age_band": "age_band"}.items():
        groups[group_name] = {}
        for value, group in frame.groupby(column):
            y = group["outcome"].astype(int).to_numpy()
            p = group["probability"].to_numpy()
            if len(group) < 20 or len(np.unique(y)) < 2:
                groups[group_name][str(value)] = {
                    "n": int(len(group)),
                    "prevalence": float(np.mean(y)) if len(group) else None,
                    "roc_auc": None,
                    "auc_pr": None,
                    "brier_score": None,
                    "note": "insufficient sample or one-class subgroup",
                }
                continue
            groups[group_name][str(value)] = {
                "n": int(len(group)),
                "prevalence": float(np.mean(y)),
                "roc_auc": float(roc_auc_score(y, p)),
                "auc_pr": float(average_precision_score(y, p)),
                "brier_score": float(brier_score_loss(y, p)),
            }
    return groups


def representative_shap_values(
    model: Any,
    x_test: pd.DataFrame,
    probability: np.ndarray,
    feature_names: list[str],
) -> dict[str, float]:
    if x_test.empty:
        return {}
    index = int(np.argmax(probability))
    sample = x_test.iloc[[index]]
    return compute_shap_values(model, sample, feature_names=feature_names)


def plot_calibration_curve(
    y_true: np.ndarray,
    probability: np.ndarray,
    path: Path,
    *,
    title: str,
) -> Path:
    fraction, mean_predicted = calibration_curve(y_true, probability, n_bins=10, strategy="quantile")
    plt.figure(figsize=(6, 5))
    plt.plot([0, 1], [0, 1], linestyle="--", color="#6b7280", label="Perfecta")
    plt.plot(mean_predicted, fraction, marker="o", color="#0f766e", label="Modelo")
    plt.xlabel("Probabilidad predicha")
    plt.ylabel("Frecuencia observada")
    plt.title(f"Calibración: {title}")
    plt.legend()
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def plot_decision_curve(
    y_true: np.ndarray,
    model_probability: np.ndarray,
    rule_probability: np.ndarray,
    path: Path,
    *,
    title: str,
) -> Path:
    thresholds = np.arange(0.05, 0.51, 0.05)
    model_nb = [net_benefit(y_true, model_probability, threshold) for threshold in thresholds]
    rule_nb = [net_benefit(y_true, rule_probability, threshold) for threshold in thresholds]
    all_nb = [treat_all_net_benefit(y_true, threshold) for threshold in thresholds]
    plt.figure(figsize=(7, 5))
    plt.plot(thresholds, model_nb, marker="o", label="Modelo ML", color="#0f766e")
    plt.plot(thresholds, rule_nb, marker="s", label="Score-regla", color="#b45309")
    plt.plot(thresholds, all_nb, linestyle="--", label="Tratar todos", color="#6b7280")
    plt.axhline(0, linestyle=":", color="#111827", label="Tratar nadie")
    plt.xlabel("Umbral de decisión")
    plt.ylabel("Beneficio neto")
    plt.title(f"Curva de decisión: {title}")
    plt.legend()
    plt.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def select_best_real_outcome_model(results: dict[str, Any]) -> str:
    trained = {
        name: result
        for name, result in results.items()
        if result.get("status") == "trained" and result.get("validation", {}).get("roc_auc") is not None
    }
    if not trained:
        raise ValueError("No trained real-outcome model results are available.")
    return max(trained, key=lambda name: float(trained[name]["validation"]["roc_auc"]))


def _constant_or_near_constant_features(frame: pd.DataFrame, features: list[str]) -> list[str]:
    dropped = []
    for feature in features:
        series = frame[feature]
        nunique = series.nunique(dropna=True)
        top_frequency = float(series.value_counts(normalize=True, dropna=True).iloc[0]) if nunique else 1.0
        if nunique <= 1 or top_frequency >= NEAR_CONSTANT_THRESHOLD:
            dropped.append(feature)
    return dropped


def safe_roc_auc(y_true: pd.Series | np.ndarray, score: np.ndarray) -> float | None:
    y_array = np.asarray(y_true, dtype=int)
    if len(np.unique(y_array)) < 2:
        return None
    return float(roc_auc_score(y_array, score))


def safe_auc_pr(y_true: pd.Series | np.ndarray, score: np.ndarray) -> float | None:
    y_array = np.asarray(y_true, dtype=int)
    if len(np.unique(y_array)) < 2:
        return None
    return float(average_precision_score(y_array, score))


def percentile_or_none(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(values, percentile))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return _repo_path(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _repo_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and audit real-outcome HomecareCCV ML cohorts.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--results-output", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--strict-external", action="store_true")
    parser.add_argument("--models", nargs="*")
    parser.add_argument("--bootstrap-iterations", type=int, default=BOOTSTRAP_ITERATIONS)
    args = parser.parse_args()
    report = run_real_outcome_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        results_path=args.results_output,
        strict_external=args.strict_external,
        only_models=args.models,
        bootstrap_iterations=args.bootstrap_iterations,
    )
    print(json.dumps(_json_safe({"summary": report["summary"]}), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
