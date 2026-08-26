from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from config import settings
from ml.explainability import compute_shap_values, top_risk_factors
from ml.preprocessing import FEATURES, RISK_LABELS, normalize_feature_payload, risk_class_to_label
from utils.risk_levels import apply_hard_overrides, estimate_rule_based_risk, normalize_risk_level


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

logger = logging.getLogger(__name__)


def predict_risk(features: dict[str, Any], model_path: str | Path | None = None) -> dict[str, Any]:
    normalized_features = normalize_feature_payload(features)
    bundle = load_model_bundle(str(_resolve_model_path(model_path)))
    if bundle is None:
        prediction = estimate_rule_based_risk(normalized_features, normalized_features)
        prediction["features_used"] = normalized_features
        return apply_hard_overrides(prediction, normalized_features)

    model = bundle["model"]
    feature_frame = pd.DataFrame([normalized_features], columns=FEATURES)
    predicted_class = int(model.predict(feature_frame)[0])
    risk_level = normalize_risk_level(risk_class_to_label(predicted_class))
    probabilities = _predict_probabilities(model, feature_frame)
    risk_probability = probabilities[risk_level]
    shap_values = compute_shap_values(model, feature_frame)
    prediction = {
        "risk_level": risk_level,
        "risk_probability": risk_probability,
        "probabilities": probabilities,
        "model_used": bundle.get("model_name", "best_model"),
        "shap_values": shap_values,
        "top_risk_factors": top_risk_factors(shap_values, normalized_features),
        "confidence_score": _confidence_score(probabilities),
        "features_used": normalized_features,
    }
    return apply_hard_overrides(prediction, normalized_features)


@lru_cache
def load_model_bundle(model_path: str) -> dict[str, Any] | None:
    path = Path(model_path)
    if not path.exists():
        logger.warning(
            "Bundle de ML no encontrado en %s; las predicciones usarán el fallback de reglas clínicas",
            path,
        )
        return None
    try:
        return joblib.load(path)
    except Exception:
        logger.exception(
            "No se pudo cargar el bundle de ML en %s; las predicciones usarán el fallback de reglas clínicas",
            path,
        )
        return None


def validate_model_bundle(model_path: str | Path | None = None) -> bool:
    resolved = _resolve_model_path(model_path)
    bundle = load_model_bundle(str(resolved))
    if bundle is None:
        return False
    bundle_features = list(bundle.get("features") or [])
    if bundle_features != FEATURES:
        logger.warning(
            "Las features del bundle (%s) no coinciden con las esperadas (%s); "
            "las predicciones del modelo no son confiables",
            bundle_features,
            FEATURES,
        )
        return False
    logger.info(
        "Bundle de ML validado: %s con %d features (%s)",
        bundle.get("model_name", "best_model"),
        len(bundle_features),
        resolved,
    )
    return True


def _predict_probabilities(model: Any, feature_frame: pd.DataFrame) -> dict[str, float]:
    probabilities = {label: 0.0 for label in RISK_LABELS.values()}
    if not hasattr(model, "predict_proba"):
        predicted = int(model.predict(feature_frame)[0])
        probabilities[risk_class_to_label(predicted)] = 1.0
        return probabilities

    raw_probabilities = model.predict_proba(feature_frame)[0]
    classes = getattr(model, "classes_", None)
    if classes is None and hasattr(model, "named_steps"):
        classes = getattr(model.named_steps.get("model"), "classes_", None)
    if classes is None:
        classes = list(range(len(raw_probabilities)))

    for class_value, probability in zip(classes, raw_probabilities, strict=False):
        probabilities[risk_class_to_label(int(class_value))] = float(probability)
    return probabilities


def _confidence_score(probabilities: dict[str, float]) -> float:
    ranked = sorted(probabilities.values(), reverse=True)
    if not ranked:
        return 0.0
    if len(ranked) == 1:
        return float(ranked[0])
    return float(ranked[0] - ranked[1])


def _resolve_model_path(model_path: str | Path | None = None) -> Path:
    candidate = Path(model_path or settings.ml_model_path)
    if candidate.is_absolute():
        return candidate
    cwd_candidate = Path.cwd() / candidate
    if cwd_candidate.exists():
        return cwd_candidate
    repo_candidate = REPO_ROOT / candidate
    if repo_candidate.exists():
        return repo_candidate
    if candidate.parts and candidate.parts[0] == "backend":
        docker_candidate = BACKEND_DIR / Path(*candidate.parts[1:])
        if docker_candidate.exists():
            return docker_candidate
    backend_candidate = BACKEND_DIR / candidate
    if backend_candidate.exists():
        return backend_candidate
    return repo_candidate
