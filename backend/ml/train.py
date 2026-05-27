from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from ml.evaluate import evaluate_classifier
from ml.model_selection import select_best_model
from ml.preprocessing import FEATURES, TARGET


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_DATASET_PATH = REPO_ROOT / "data" / "processed" / "unified_dataset.csv"
DEFAULT_MODEL_PATH = BACKEND_DIR / "ml" / "models" / "best_model.pkl"
DEFAULT_RESULTS_PATH = BACKEND_DIR / "ml" / "models" / "comparison_results.json"
DEFAULT_METADATA_PATH = BACKEND_DIR / "ml" / "models" / "training_metadata.json"

METRIC = "f1_macro"
CV_FOLDS = 5
CV_SAMPLE_LIMIT = 25000

TRANSFER_NOTES = {
    "logistic_regression": "Baseline lineal; reutilizable como referencia/calibrador, no como fine-tuning incremental principal.",
    "decision_tree": "No incremental; sus hiperparametros y reglas sirven como baseline interpretable.",
    "random_forest": "Puede extender arboles con warm_start, pero no es transferencia clinica estricta.",
    "gradient_boosting": "Soporta warm_start para agregar etapas, util como baseline de boosting clasico.",
    "xgboost": "Permite continuar entrenamiento usando el booster previo con xgb_model.",
    "lightgbm": "Modelo seleccionado; permite continuar entrenamiento con init_model y conserva compatibilidad SHAP.",
    "catboost": "Permite continuar entrenamiento con init_model en flujos CatBoost.",
    "svm": "No incremental en sklearn; se conserva como baseline kernel.",
    "knn": "Modelo basado en instancias; no tiene parametros aprendidos transferibles mas alla del set/base de referencia.",
    "mlp": "Puede reutilizar pesos con warm_start o partial_fit en escenarios controlados.",
}


def build_model_registry(strict_external: bool = False) -> dict[str, Any]:
    models: dict[str, Any] = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "decision_tree": DecisionTreeClassifier(class_weight="balanced", random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=200, random_state=42),
        "svm": SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=42),
        "knn": KNeighborsClassifier(n_neighbors=7),
        "mlp": MLPClassifier(hidden_layer_sizes=(128, 64, 32), max_iter=500, random_state=42),
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
                models[name] = model_class(n_estimators=200, eval_metric="mlogloss", random_state=42, n_jobs=-1)
            elif name == "lightgbm":
                models[name] = model_class(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)
            else:
                models[name] = model_class(
                    iterations=200,
                    verbose=0,
                    random_state=42,
                    thread_count=-1,
                    allow_writing_files=False,
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


def train_all_models(
    dataset_path: Path = DEFAULT_DATASET_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
    results_path: Path = DEFAULT_RESULTS_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
    strict_external: bool = False,
    only_models: list[str] | None = None,
) -> dict[str, Any]:
    data = pd.read_csv(dataset_path)
    _validate_dataset(data)
    train_frame, validation_frame, test_frame = _split_frames(data)
    train_balanced = _balance_training_frame(train_frame)
    split_summary = _split_summary(data, train_frame, train_balanced, validation_frame, test_frame)
    x_train, y_train = train_balanced[FEATURES], train_balanced[TARGET].astype(int)
    x_validation, y_validation = validation_frame[FEATURES], validation_frame[TARGET].astype(int)
    x_test, y_test = test_frame[FEATURES], test_frame[TARGET].astype(int)

    registry = build_model_registry(strict_external=strict_external)
    if only_models:
        registry = {name: model for name, model in registry.items() if name in only_models}

    results: list[dict[str, Any]] = []
    trained_models: dict[str, Any] = {}
    for name, estimator in registry.items():
        print(f"[train] Starting {name}", flush=True)
        if estimator is None:
            results.append(
                {
                    "model": name,
                    "status": "skipped",
                    "reason": "Optional dependency is not installed in this environment.",
                }
            )
            continue
        pipeline = Pipeline(
            steps=[
                ("preprocess", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])),
                ("model", estimator),
            ]
        )
        try:
            x_cv, y_cv = _cv_frame(x_train, y_train)
            cv_scores = _cross_validate(pipeline, x_cv, y_cv)
            pipeline.fit(x_train, y_train)
            result = {
                "model": name,
                "status": "trained",
                "train_rows_used": int(len(x_train)),
                "train_rows_available": int(len(x_train)),
                "cv_rows_used": int(len(x_cv)),
                "cv_f1_macro_mean": float(cv_scores.mean()) if len(cv_scores) else None,
                "cv_f1_macro_std": float(cv_scores.std()) if len(cv_scores) else None,
                "validation": evaluate_classifier(pipeline, x_validation, y_validation),
                "test": evaluate_classifier(pipeline, x_test, y_test),
            }
            results.append(result)
            trained_models[name] = pipeline
            print(
                f"[train] Finished {name}: validation f1_macro="
                f"{result['validation']['f1_macro']:.4f}",
                flush=True,
            )
        except Exception as exc:
            results.append({"model": name, "status": "failed", "reason": str(exc)})
            print(f"[train] Failed {name}: {exc}", flush=True)

    best = select_best_model(results)
    best_model_name = str(best["model"])
    bundle = {
        "model": trained_models[best_model_name],
        "model_name": best_model_name,
        "features": FEATURES,
        "target": TARGET,
        "trained_at": datetime.now(UTC).isoformat(),
        "metric": METRIC,
        "selection": best,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    report = {
        "trained_at": bundle["trained_at"],
        "dataset_path": str(dataset_path),
        "best_model": best_model_name,
        "selection_metric": METRIC,
        "results": results,
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    metadata = build_training_metadata(report, registry, bundle, split_summary)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _validate_dataset(data: pd.DataFrame) -> None:
    missing = [column for column in FEATURES + [TARGET] if column not in data.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")


def _split_frames(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if "split" in data.columns:
        train = data[data["split"] == "train"].copy()
        validation = data[data["split"] == "validation"].copy()
        test = data[data["split"] == "test"].copy()
        if not train.empty and not validation.empty and not test.empty:
            return train, validation, test

    train, temp = train_test_split(data, test_size=0.30, random_state=42, stratify=_safe_stratify(data))
    validation, test = train_test_split(temp, test_size=0.50, random_state=42, stratify=_safe_stratify(temp))
    return train, validation, test


def _balance_training_frame(train: pd.DataFrame) -> pd.DataFrame:
    try:
        from imblearn.over_sampling import SMOTE

        min_count = int(train[TARGET].value_counts().min())
        if min_count >= 2:
            sampler = SMOTE(random_state=42, k_neighbors=max(1, min(5, min_count - 1)))
            x_resampled, y_resampled = sampler.fit_resample(train[FEATURES], train[TARGET].astype(int))
            balanced = pd.DataFrame(x_resampled, columns=FEATURES)
            balanced[TARGET] = y_resampled
            return balanced
    except ModuleNotFoundError:
        pass
    max_count = int(train[TARGET].value_counts().max())
    parts = [
        group.sample(max_count, replace=True, random_state=42)
        for _, group in train.groupby(TARGET, group_keys=False)
    ]
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=42)


def _split_summary(
    data: pd.DataFrame,
    train_frame: pd.DataFrame,
    train_balanced: pd.DataFrame,
    validation_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "raw_rows": int(len(data)),
        "train_rows_raw": int(len(train_frame)),
        "train_rows_balanced": int(len(train_balanced)),
        "validation_rows": int(len(validation_frame)),
        "test_rows": int(len(test_frame)),
        "class_distribution": {
            "raw": _class_distribution(data),
            "train_raw": _class_distribution(train_frame),
            "train_balanced": _class_distribution(train_balanced),
            "validation": _class_distribution(validation_frame),
            "test": _class_distribution(test_frame),
        },
    }


def _class_distribution(frame: pd.DataFrame) -> dict[str, int]:
    counts = frame[TARGET].astype(int).value_counts().sort_index()
    return {str(int(label)): int(count) for label, count in counts.items()}


def build_training_metadata(
    report: dict[str, Any],
    registry: dict[str, Any],
    bundle: dict[str, Any],
    split_summary: dict[str, Any],
) -> dict[str, Any]:
    best_model_name = str(report["best_model"])
    return {
        "trained_at": report["trained_at"],
        "dataset_path": _repo_path(Path(report["dataset_path"])),
        "selection_metric": report["selection_metric"],
        "best_model": best_model_name,
        "best_model_artifact": _repo_path(DEFAULT_MODEL_PATH),
        "results_artifact": _repo_path(DEFAULT_RESULTS_PATH),
        "feature_columns": FEATURES,
        "target_column": TARGET,
        "target_mapping": {"0": "low", "1": "moderate", "2": "high", "3": "critical"},
        "training_protocol": {
            "random_state": 42,
            "cv_folds": CV_FOLDS,
            "cv_sample_limit": CV_SAMPLE_LIMIT,
            "resampling": "SMOTE on training split only",
            "preprocessing": ["SimpleImputer(strategy='median')", "StandardScaler()"],
            "model_selection_rule": "highest validation f1_macro; test split is retained as final holdout",
        },
        "split_summary": split_summary,
        "model_parameters": {
            name: _model_parameter_record(name, estimator, best_model_name)
            for name, estimator in registry.items()
            if estimator is not None
        },
        "best_model_details": _best_model_details(bundle),
        "model_results": report["results"],
    }


def _model_parameter_record(model_name: str, estimator: Any, best_model_name: str) -> dict[str, Any]:
    return {
        "class": f"{estimator.__class__.__module__}.{estimator.__class__.__name__}",
        "init_params": _json_safe(estimator.get_params()) if hasattr(estimator, "get_params") else {},
        "trained_pipeline_artifact": _repo_path(DEFAULT_MODEL_PATH) if model_name == best_model_name else None,
        "transfer_learning_note": TRANSFER_NOTES.get(model_name, "No transfer note registered."),
    }


def _best_model_details(bundle: dict[str, Any]) -> dict[str, Any]:
    pipeline = bundle["model"]
    estimator = pipeline.named_steps["model"]
    details = {
        "model_name": bundle["model_name"],
        "trained_at": bundle["trained_at"],
        "pipeline_steps": list(pipeline.named_steps.keys()),
        "estimator_class": f"{estimator.__class__.__module__}.{estimator.__class__.__name__}",
        "estimator_params": _json_safe(estimator.get_params()) if hasattr(estimator, "get_params") else {},
    }
    booster = getattr(estimator, "booster_", None)
    if booster is not None:
        details["booster"] = {
            "params": _json_safe(getattr(booster, "params", {})),
            "num_trees": int(booster.num_trees()) if hasattr(booster, "num_trees") else None,
            "num_model_per_iteration": (
                int(booster.num_model_per_iteration()) if hasattr(booster, "num_model_per_iteration") else None
            ),
        }
    return details


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def _repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _cross_validate(pipeline: Pipeline, x_train: pd.DataFrame, y_train: pd.Series):
    min_count = int(y_train.value_counts().min())
    folds = min(CV_FOLDS, min_count)
    if folds < 2:
        return pd.Series(dtype=float).to_numpy()
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    return cross_val_score(pipeline, x_train, y_train, cv=cv, scoring=METRIC)


def _cv_frame(x_train: pd.DataFrame, y_train: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    if len(x_train) <= CV_SAMPLE_LIMIT:
        return x_train, y_train
    frame = x_train.copy()
    frame[TARGET] = y_train.to_numpy()
    per_class = max(1, CV_SAMPLE_LIMIT // frame[TARGET].nunique())
    sampled = _sample_per_class(frame, per_class)
    return sampled[FEATURES], sampled[TARGET].astype(int)


def _sample_per_class(frame: pd.DataFrame, per_class: int) -> pd.DataFrame:
    parts = [
        group.sample(min(len(group), per_class), random_state=42)
        for _, group in frame.groupby(TARGET, group_keys=False)
    ]
    return pd.concat(parts, ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)


def _safe_stratify(data: pd.DataFrame):
    if data[TARGET].nunique() > 1 and data[TARGET].value_counts().min() >= 2:
        return data[TARGET]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Train HomecareCCV risk models.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--model-output", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--results-output", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--metadata-output", type=Path, default=DEFAULT_METADATA_PATH)
    parser.add_argument("--strict-external", action="store_true")
    parser.add_argument("--models", nargs="*")
    args = parser.parse_args()
    report = train_all_models(
        dataset_path=args.dataset,
        model_path=args.model_output,
        results_path=args.results_output,
        metadata_path=args.metadata_output,
        strict_external=args.strict_external,
        only_models=args.models,
    )
    print(json.dumps({"best_model": report["best_model"], "results": report["results"]}, indent=2))


if __name__ == "__main__":
    main()
