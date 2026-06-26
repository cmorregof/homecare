from __future__ import annotations

import pandas as pd

from ml.carmen_forecast.features import compute_window_summary, infer_temporal_feature_columns


def make_prediction_windows(
    df: pd.DataFrame,
    patient_id_col: str = "patient_id",
    time_col: str = "timestamp",
    lookback_hours: int = 24,
    horizon_hours: int = 6,
    label_col: str = "future_deterioration_6h",
    drop_censored: bool = True,
    horizon_observed_col: str = "horizon_observed",
):
    frame = df.copy()
    frame[time_col] = pd.to_datetime(frame[time_col])
    frame = frame.sort_values([patient_id_col, time_col]).reset_index(drop=True)
    feature_columns = infer_temporal_feature_columns(frame, label_col=label_col)

    rows: list[dict[str, float]] = []
    targets: list[int] = []
    metadata_rows: list[dict[str, object]] = []

    for patient_id, patient_frame in frame.groupby(patient_id_col, sort=False):
        patient_frame = patient_frame.sort_values(time_col).reset_index(drop=True)
        for _, current_row in patient_frame.iterrows():
            label_value = current_row[label_col]
            if drop_censored:
                if horizon_observed_col in current_row and not bool(current_row[horizon_observed_col]):
                    continue
                if pd.isna(label_value):
                    continue

            prediction_time = current_row[time_col]
            window_start = prediction_time - pd.Timedelta(hours=lookback_hours)
            history = patient_frame[
                (patient_frame[time_col] >= window_start) & (patient_frame[time_col] <= prediction_time)
            ]
            if history.empty:
                continue

            rows.append(compute_window_summary(history, feature_columns))
            targets.append(int(label_value) if not pd.isna(label_value) else pd.NA)
            metadata_rows.append(
                {
                    "patient_id": patient_id,
                    "prediction_time": prediction_time,
                    "horizon_hours": horizon_hours,
                    "horizon_observed": bool(current_row[horizon_observed_col])
                    if horizon_observed_col in current_row and not pd.isna(current_row[horizon_observed_col])
                    else not pd.isna(label_value),
                }
            )

    X = pd.DataFrame(rows)
    y_dtype = "Int64" if any(pd.isna(value) for value in targets) else "int64"
    y = pd.Series(targets, name=label_col, dtype=y_dtype)
    metadata = pd.DataFrame(metadata_rows)
    return X, y, metadata
