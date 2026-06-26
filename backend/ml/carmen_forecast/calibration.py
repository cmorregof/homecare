from __future__ import annotations

import numpy as np
from sklearn.calibration import calibration_curve


def summarize_calibration(y_true, y_prob, n_bins: int = 10) -> dict[str, list[float]]:
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")
    return {
        "predicted": np.asarray(prob_pred, dtype=float).round(6).tolist(),
        "observed": np.asarray(prob_true, dtype=float).round(6).tolist(),
        "n_bins": int(n_bins),
    }
