from __future__ import annotations

import math

import numpy as np
import pandas as pd


IDENTIFIER_COLUMNS = {
    "patient_id",
    "timestamp",
    "sex",
    "risk_state",
    "future_deterioration_6h",
}


def infer_temporal_feature_columns(df: pd.DataFrame, label_col: str) -> list[str]:
    feature_columns: list[str] = []
    for column in df.columns:
        if column in IDENTIFIER_COLUMNS or column == label_col:
            continue
        if pd.api.types.is_numeric_dtype(df[column]):
            feature_columns.append(column)
    return feature_columns


def compute_window_summary(window: pd.DataFrame, feature_columns: list[str]) -> dict[str, float]:
    summary: dict[str, float] = {}
    for column in feature_columns:
        series = pd.to_numeric(window[column], errors="coerce")
        summary[f"{column}__last"] = _safe_float(series.iloc[-1]) if len(series) else math.nan
        summary[f"{column}__mean"] = _safe_float(series.mean())
        summary[f"{column}__min"] = _safe_float(series.min())
        summary[f"{column}__max"] = _safe_float(series.max())
        summary[f"{column}__slope"] = _compute_slope(series)
        summary[f"{column}__missing_count"] = float(series.isna().sum())
    return summary


def _compute_slope(series: pd.Series) -> float:
    clean = series.dropna()
    if len(clean) < 2:
        return 0.0
    x_values = np.arange(len(clean), dtype=float)
    slope, _ = np.polyfit(x_values, clean.to_numpy(dtype=float), deg=1)
    return float(slope)


def _safe_float(value: object) -> float:
    if value is None or pd.isna(value):
        return math.nan
    return float(value)
