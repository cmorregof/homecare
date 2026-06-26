from __future__ import annotations

import math

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_binary_forecast(y_true, y_prob, threshold: float = 0.5) -> dict[str, object]:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    positives = int(np.sum(y_true == 1))
    negatives = int(np.sum(y_true == 0))

    return {
        "auroc": _safe_metric(lambda: roc_auc_score(y_true, y_prob)),
        "auprc": _safe_metric(lambda: average_precision_score(y_true, y_prob)),
        "brier": _safe_metric(lambda: brier_score_loss(y_true, y_prob)),
        "sensitivity": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity": float(tn / negatives) if negatives else math.nan,
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "critical_miss_rate": float(fn / positives) if positives else math.nan,
        "threshold": float(threshold),
    }


def _safe_metric(func):
    try:
        return float(func())
    except ValueError:
        return math.nan
