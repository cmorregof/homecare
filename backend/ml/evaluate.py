from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, roc_auc_score


EVALUATION_METRICS = [
    "f1_macro",
    "roc_auc_ovr",
    "precision_by_risk_level",
    "recall_by_risk_level",
]


def evaluate_classifier(model: Any, x, y_true) -> dict[str, Any]:
    y_pred = model.predict(x)
    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=[0, 1, 2, 3],
        zero_division=0,
    )
    metrics["by_class"] = {
        str(label): {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate([0, 1, 2, 3])
    }
    if hasattr(model, "predict_proba"):
        try:
            probabilities = model.predict_proba(x)
            if probabilities.shape[1] == 4 and len(set(y_true)) > 1:
                metrics["roc_auc_ovr"] = float(roc_auc_score(y_true, probabilities, multi_class="ovr"))
        except Exception:
            metrics["roc_auc_ovr"] = None
    return metrics


def probability_map(classes: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    return {str(int(label)): float(probabilities[index]) for index, label in enumerate(classes)}
