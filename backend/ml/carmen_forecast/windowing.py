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
            prediction_time = current_row[time_col]
            window_start = prediction_time - pd.Timedelta(hours=lookback_hours)
            history = patient_frame[
                (patient_frame[time_col] >= window_start) & (patient_frame[time_col] <= prediction_time)
            ]
            if history.empty:
                continue

            rows.append(compute_window_summary(history, feature_columns))
            targets.append(int(current_row[label_col]))
            metadata_rows.append(
                {
                    "patient_id": patient_id,
                    "prediction_time": prediction_time,
                    "horizon_hours": horizon_hours,
                }
            )

    X = pd.DataFrame(rows)
    y = pd.Series(targets, name=label_col, dtype="int64")
    metadata = pd.DataFrame(metadata_rows)
    return X, y, metadata
