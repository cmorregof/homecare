from __future__ import annotations

from typing import Any

import numpy as np

from ml.preprocessing import FEATURES


def compute_shap_values(model: object, feature_frame: Any) -> dict[str, float]:
    try:
        import shap

        if hasattr(model, "named_steps"):
            estimator = model.named_steps.get("model")
            preprocessor = model.named_steps.get("preprocess")
            transformed = preprocessor.transform(feature_frame) if preprocessor is not None else feature_frame
        else:
            estimator = model
            transformed = feature_frame
        explainer = shap.Explainer(estimator, transformed)
        values = explainer(transformed)
        raw_values = values.values
        if isinstance(raw_values, list):
            raw_values = raw_values[0]
        array = np.asarray(raw_values)
        if array.ndim == 3:
            array = array[0, :, -1]
        elif array.ndim == 2:
            array = array[0]
        return _as_feature_dict(array)
    except Exception:
        return compute_proxy_shap_values(model, feature_frame)


def compute_proxy_shap_values(model: object, feature_frame: Any) -> dict[str, float]:
    estimator = model.named_steps.get("model") if hasattr(model, "named_steps") else model
    values = None
    if hasattr(estimator, "feature_importances_"):
        values = np.asarray(estimator.feature_importances_, dtype=float)
    elif hasattr(estimator, "coef_"):
        values = np.asarray(estimator.coef_, dtype=float)
        if values.ndim > 1:
            values = np.mean(np.abs(values), axis=0)
    if values is None or len(values) == 0:
        values = np.zeros(len(FEATURES), dtype=float)
    return _as_feature_dict(values)


def top_risk_factors(shap_values: dict[str, float], features: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    ranked = sorted(shap_values.items(), key=lambda item: abs(float(item[1])), reverse=True)
    return [
        {
            "feature": feature,
            "value": features.get(feature),
            "shap": float(value),
        }
        for feature, value in ranked[:limit]
    ]


def _as_feature_dict(values: np.ndarray) -> dict[str, float]:
    flattened = np.ravel(values)
    if len(flattened) < len(FEATURES):
        flattened = np.pad(flattened, (0, len(FEATURES) - len(flattened)))
    return {feature: float(flattened[index]) for index, feature in enumerate(FEATURES)}
