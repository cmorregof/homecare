from __future__ import annotations

import numpy as np


def decision_curve_analysis(
    y_true,
    y_prob,
    thresholds: list[float] | None = None,
) -> list[dict[str, float]]:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    thresholds = thresholds or [round(x, 2) for x in np.arange(0.1, 0.91, 0.1)]

    results: list[dict[str, float]] = []
    for threshold in thresholds:
        predictions = (y_prob >= threshold).astype(int)
        tp = float(np.sum((predictions == 1) & (y_true == 1)))
        fp = float(np.sum((predictions == 1) & (y_true == 0)))
        n = max(1.0, float(len(y_true)))
        odds = threshold / max(1e-6, 1 - threshold)
        net_benefit = (tp / n) - (fp / n) * odds
        results.append({"threshold": float(threshold), "net_benefit": float(net_benefit)})
    return results
