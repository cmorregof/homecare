from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml.preprocessing import FEATURES, TARGET, add_derived_features, bmi_category


DATA_DIR = REPO_ROOT / "data" / "mock"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
UNIFIED_DATASET_PATH = PROCESSED_DIR / "unified_dataset.csv"
TRAIN_RESAMPLED_PATH = PROCESSED_DIR / "train_resampled.csv"


def assign_risk_level(row: dict[str, object] | pd.Series) -> int:
    score = 0
    systolic_bp = float(row.get("systolic_bp") or 0)
    glucose = float(row.get("glucose") or 0)
    bmi = float(row.get("bmi") or 0)

    if systolic_bp >= 180 or systolic_bp < 80:
        score += 3
    elif systolic_bp >= 160 or systolic_bp < 90:
        score += 2
    elif systolic_bp >= 140:
        score += 1

    if bool(row.get("stroke_history")):
        score += 2
    if bool(row.get("heart_disease_history")):
        score += 1
    if bool(row.get("hypertension_history")):
        score += 1
    if glucose > 300:
        score += 2
    elif glucose > 200:
        score += 1
    if bmi > 35:
        score += 1
    if int(row.get("cholesterol_level") or 0) == 3:
        score += 1

    if score >= 7:
        return 3
    if score >= 5:
        return 2
    if score >= 3:
        return 1
    return 0


def load_and_unify_datasets(data_dir: Path = DATA_DIR, allow_synthetic: bool = False) -> pd.DataFrame:
    frames = [
        _load_stroke_dataset(data_dir),
        _load_cardio_dataset(data_dir),
        _load_heart_failure_dataset(data_dir),
    ]
    frames = [frame for frame in frames if frame is not None and not frame.empty]
    if not frames:
        if allow_synthetic:
            return generate_synthetic_dataset()
        raise FileNotFoundError(
            "No real Kaggle CSV files were found. Download the datasets into data/mock "
            "or run with --allow-synthetic for a local smoke-test dataset."
        )
    unified = pd.concat(frames, ignore_index=True)
    return finalize_unified_dataset(unified)


def finalize_unified_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    for row in frame.to_dict(orient="records"):
        normalized = _with_defaults(row)
        normalized = add_derived_features(normalized)
        normalized[TARGET] = assign_risk_level(normalized)
        records.append(normalized)
    unified = pd.DataFrame(records)
    for feature in FEATURES:
        if feature not in unified.columns:
            unified[feature] = 0
    unified = unified[FEATURES + [TARGET]]
    return unified.dropna(subset=["systolic_bp", "diastolic_bp"]).reset_index(drop=True)


def split_and_balance_dataset(
    frame: pd.DataFrame,
    output_path: Path = UNIFIED_DATASET_PATH,
    train_resampled_path: Path = TRAIN_RESAMPLED_PATH,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    train, temp = _safe_train_test_split(frame, test_size=0.30, random_state=random_state)
    validation, test = _safe_train_test_split(temp, test_size=0.50, random_state=random_state)
    train = train.assign(split="train")
    validation = validation.assign(split="validation")
    test = test.assign(split="test")
    unified = pd.concat([train, validation, test], ignore_index=True)
    unified.to_csv(output_path, index=False)

    train_resampled = _balance_training_split(train.drop(columns=["split"]), random_state=random_state)
    train_resampled = train_resampled.assign(split="train_resampled")
    train_resampled.to_csv(train_resampled_path, index=False)
    return unified, train_resampled


def generate_synthetic_dataset(rows: int = 320, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    records: list[dict[str, Any]] = []
    for _ in range(rows):
        age = int(rng.integers(35, 91))
        gender_encoded = int(rng.integers(0, 2))
        hypertension = bool(rng.random() < (0.25 + max(age - 55, 0) / 100))
        stroke = bool(rng.random() < (0.06 + max(age - 65, 0) / 180))
        heart = bool(rng.random() < (0.12 + max(age - 60, 0) / 150))
        diabetes = bool(rng.random() < 0.18)
        systolic = float(rng.normal(128 + (18 if hypertension else 0) + max(age - 65, 0) * 0.35, 18))
        diastolic = float(rng.normal(80 + (8 if hypertension else 0), 10))
        bmi = float(np.clip(rng.normal(27, 5), 17, 45))
        glucose = float(rng.normal(105 + (55 if diabetes else 0), 35))
        record = {
            "age": age,
            "gender_encoded": gender_encoded,
            "systolic_bp": round(np.clip(systolic, 80, 220), 1),
            "diastolic_bp": round(np.clip(diastolic, 45, 130), 1),
            "heart_rate": int(np.clip(rng.normal(78, 14), 45, 135)),
            "oxygen_saturation": int(np.clip(rng.normal(96, 2), 88, 100)),
            "glucose": round(np.clip(glucose, 60, 390), 1),
            "bmi": round(bmi, 1),
            "cholesterol_level": int(rng.choice([1, 2, 3], p=[0.55, 0.30, 0.15])),
            "hypertension_history": hypertension,
            "heart_disease_history": heart,
            "stroke_history": stroke,
            "diabetes_history": diabetes,
            "smoking_encoded": int(rng.choice([0, 1, 2], p=[0.58, 0.25, 0.17])),
            "alcohol_intake": bool(rng.random() < 0.18),
            "physical_activity": bool(rng.random() < 0.62),
            "pain_score": int(rng.integers(0, 5)),
            "dizziness_score": int(rng.integers(0, 5)),
            "dyspnea_score": int(rng.integers(0, 5)),
        }
        records.append(record)
    return finalize_unified_dataset(pd.DataFrame(records))


def _load_stroke_dataset(data_dir: Path) -> pd.DataFrame | None:
    path = _first_existing(data_dir, ["healthcare-dataset-stroke-data.csv", "stroke_dataset.csv"])
    if path is None:
        return None
    raw = _read_csv(path)
    if _is_placeholder(raw):
        return None
    frame = pd.DataFrame()
    frame["age"] = pd.to_numeric(raw.get("age"), errors="coerce")
    frame["gender_encoded"] = raw.get("gender", "").map({"Female": 0, "Male": 1, "Other": 0}).fillna(0).astype(int)
    frame["hypertension_history"] = _bool_series(raw.get("hypertension"))
    frame["heart_disease_history"] = _bool_series(raw.get("heart_disease"))
    frame["stroke_history"] = _bool_series(raw.get("stroke"))
    frame["diabetes_history"] = False
    frame["glucose"] = pd.to_numeric(raw.get("avg_glucose_level"), errors="coerce")
    frame["bmi"] = pd.to_numeric(raw.get("bmi"), errors="coerce")
    frame["smoking_encoded"] = raw.get("smoking_status", "").map(
        {"never smoked": 0, "formerly smoked": 1, "smokes": 2, "Unknown": 0}
    ).fillna(0).astype(int)
    frame["systolic_bp"] = 118 + frame["age"].fillna(60) * 0.25 + frame["hypertension_history"].astype(int) * 24
    frame["diastolic_bp"] = 76 + frame["hypertension_history"].astype(int) * 10
    frame["heart_rate"] = 76
    frame["oxygen_saturation"] = 97
    frame["cholesterol_level"] = 1
    frame["alcohol_intake"] = False
    frame["physical_activity"] = True
    frame["pain_score"] = 0
    frame["dizziness_score"] = frame["stroke_history"].astype(int) * 2
    frame["dyspnea_score"] = 0
    return frame


def _load_cardio_dataset(data_dir: Path) -> pd.DataFrame | None:
    path = _first_existing(data_dir, ["cardio_train.csv", "cardio_dataset.csv"])
    if path is None:
        return None
    raw = _read_csv(path)
    if _is_placeholder(raw):
        return None
    frame = pd.DataFrame()
    frame["age"] = pd.to_numeric(raw.get("age"), errors="coerce") / 365.25
    frame["gender_encoded"] = pd.to_numeric(raw.get("gender"), errors="coerce").map({1: 0, 2: 1}).fillna(0).astype(int)
    frame["systolic_bp"] = pd.to_numeric(raw.get("ap_hi"), errors="coerce")
    frame["diastolic_bp"] = pd.to_numeric(raw.get("ap_lo"), errors="coerce")
    frame["bmi"] = pd.to_numeric(raw.get("weight"), errors="coerce") / (
        (pd.to_numeric(raw.get("height"), errors="coerce") / 100) ** 2
    )
    frame["cholesterol_level"] = pd.to_numeric(raw.get("cholesterol"), errors="coerce").fillna(1).astype(int)
    glucose_level = pd.to_numeric(raw.get("gluc"), errors="coerce").fillna(1).astype(int)
    frame["glucose"] = glucose_level.map({1: 95, 2: 155, 3: 225}).fillna(100)
    frame["heart_rate"] = 78
    frame["oxygen_saturation"] = 97
    frame["hypertension_history"] = frame["systolic_bp"] >= 140
    frame["heart_disease_history"] = _bool_series(raw.get("cardio"))
    frame["stroke_history"] = False
    frame["diabetes_history"] = glucose_level >= 2
    frame["smoking_encoded"] = _bool_series(raw.get("smoke")).astype(int) * 2
    frame["alcohol_intake"] = _bool_series(raw.get("alco"))
    frame["physical_activity"] = _bool_series(raw.get("active"))
    frame["pain_score"] = 0
    frame["dizziness_score"] = 0
    frame["dyspnea_score"] = frame["heart_disease_history"].astype(int)
    return frame


def _load_heart_failure_dataset(data_dir: Path) -> pd.DataFrame | None:
    path = _first_existing(data_dir, ["heart.csv", "heart_failure_dataset.csv"])
    if path is None:
        return None
    raw = _read_csv(path)
    if _is_placeholder(raw):
        return None
    frame = pd.DataFrame()
    frame["age"] = pd.to_numeric(raw.get("Age"), errors="coerce")
    frame["gender_encoded"] = raw.get("Sex", "").map({"F": 0, "M": 1}).fillna(0).astype(int)
    frame["systolic_bp"] = pd.to_numeric(raw.get("RestingBP"), errors="coerce")
    frame["diastolic_bp"] = frame["systolic_bp"].apply(lambda value: 80 if pd.isna(value) else max(55, value * 0.62))
    cholesterol = pd.to_numeric(raw.get("Cholesterol"), errors="coerce").fillna(180)
    frame["cholesterol_level"] = cholesterol.apply(lambda value: 3 if value >= 240 else 2 if value >= 200 else 1)
    frame["glucose"] = _bool_series(raw.get("FastingBS")).map({True: 180, False: 100})
    frame["heart_rate"] = pd.to_numeric(raw.get("MaxHR"), errors="coerce").fillna(82)
    frame["oxygen_saturation"] = 97
    height = 165 + frame["gender_encoded"] * 8
    weight = 72 + frame["gender_encoded"] * 8
    frame["bmi"] = weight / ((height / 100) ** 2)
    frame["hypertension_history"] = frame["systolic_bp"] >= 140
    frame["heart_disease_history"] = _bool_series(raw.get("HeartDisease"))
    frame["stroke_history"] = False
    frame["diabetes_history"] = _bool_series(raw.get("FastingBS"))
    frame["smoking_encoded"] = 0
    frame["alcohol_intake"] = False
    frame["physical_activity"] = raw.get("ExerciseAngina", "").map({"N": True, "Y": False}).fillna(True)
    frame["pain_score"] = raw.get("ChestPainType", "").map({"ASY": 0, "ATA": 2, "NAP": 4, "TA": 6}).fillna(0)
    frame["dizziness_score"] = 0
    frame["dyspnea_score"] = frame["heart_disease_history"].astype(int)
    return frame


def _with_defaults(row: dict[str, Any]) -> dict[str, Any]:
    bmi = _float_or_none(row.get("bmi")) or 25
    return {
        "age": _float_or_none(row.get("age")) or 65,
        "gender_encoded": int(_float_or_none(row.get("gender_encoded")) or 0),
        "systolic_bp": _float_or_none(row.get("systolic_bp")) or 120,
        "diastolic_bp": _float_or_none(row.get("diastolic_bp")) or 80,
        "heart_rate": _float_or_none(row.get("heart_rate")) or 75,
        "oxygen_saturation": _float_or_none(row.get("oxygen_saturation")) or 97,
        "glucose": _float_or_none(row.get("glucose")) or 100,
        "bmi": bmi,
        "cholesterol_level": int(_float_or_none(row.get("cholesterol_level")) or 1),
        "hypertension_history": bool(row.get("hypertension_history")),
        "heart_disease_history": bool(row.get("heart_disease_history")),
        "stroke_history": bool(row.get("stroke_history")),
        "diabetes_history": bool(row.get("diabetes_history")),
        "smoking_encoded": int(_float_or_none(row.get("smoking_encoded")) or 0),
        "alcohol_intake": bool(row.get("alcohol_intake")),
        "physical_activity": bool(row.get("physical_activity", True)),
        "pain_score": int(_float_or_none(row.get("pain_score")) or 0),
        "dizziness_score": int(_float_or_none(row.get("dizziness_score")) or 0),
        "dyspnea_score": int(_float_or_none(row.get("dyspnea_score")) or 0),
        "pulse_pressure": 40,
        "map": 93.3,
        "bmi_category": bmi_category(bmi),
    }


def _safe_train_test_split(frame: pd.DataFrame, test_size: float, random_state: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    stratify = frame[TARGET] if frame[TARGET].nunique() > 1 and frame[TARGET].value_counts().min() >= 2 else None
    return train_test_split(frame, test_size=test_size, random_state=random_state, stratify=stratify)


def _balance_training_split(frame: pd.DataFrame, random_state: int) -> pd.DataFrame:
    try:
        from imblearn.over_sampling import SMOTE

        min_count = int(frame[TARGET].value_counts().min())
        if min_count >= 2:
            k_neighbors = max(1, min(5, min_count - 1))
            sampler = SMOTE(random_state=random_state, k_neighbors=k_neighbors)
            features, target = sampler.fit_resample(frame[FEATURES], frame[TARGET])
            balanced = pd.DataFrame(features, columns=FEATURES)
            balanced[TARGET] = target
            return balanced
    except ModuleNotFoundError:
        pass

    max_count = int(frame[TARGET].value_counts().max())
    balanced_parts = [
        group.sample(max_count, replace=True, random_state=random_state)
        for _, group in frame.groupby(TARGET, group_keys=False)
    ]
    return pd.concat(balanced_parts, ignore_index=True).sample(frac=1, random_state=random_state).reset_index(drop=True)


def _first_existing(data_dir: Path, names: list[str]) -> Path | None:
    for name in names:
        path = data_dir / name
        if path.exists():
            return path
    return None


def _read_csv(path: Path) -> pd.DataFrame:
    if path.name == "cardio_train.csv":
        return pd.read_csv(path, sep=";")
    return pd.read_csv(path)


def _is_placeholder(frame: pd.DataFrame) -> bool:
    return "placeholder" in frame.columns and frame["placeholder"].astype(str).str.contains("download_required").any()


def _bool_series(series: Any) -> pd.Series:
    if series is None:
        return pd.Series(dtype=bool)
    return pd.Series(series).fillna(0).isin([1, "1", True, "true", "True", "Y", "yes", "Yes"])


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Unify HomecareCCV Kaggle datasets.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output", type=Path, default=UNIFIED_DATASET_PATH)
    parser.add_argument("--train-resampled-output", type=Path, default=TRAIN_RESAMPLED_PATH)
    parser.add_argument("--allow-synthetic", action="store_true")
    args = parser.parse_args()

    unified = load_and_unify_datasets(args.data_dir, allow_synthetic=args.allow_synthetic)
    output, train_resampled = split_and_balance_dataset(
        unified,
        output_path=args.output,
        train_resampled_path=args.train_resampled_output,
    )
    print(f"Saved unified dataset: {args.output} ({len(output)} rows)")
    print(f"Saved balanced training split: {args.train_resampled_output} ({len(train_resampled)} rows)")


if __name__ == "__main__":
    main()
