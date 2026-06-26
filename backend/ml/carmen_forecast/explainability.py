from __future__ import annotations

import pandas as pd


def derive_driver_statements(feature_row: pd.Series) -> list[str]:
    drivers: list[str] = []
    checks = [
        ("oxygen_saturation__slope", "oxygen saturation decreasing"),
        ("heart_rate__slope", "heart rate increasing"),
        ("systolic_bp__slope", "systolic blood pressure increasing"),
        ("glucose__max", "glucose excursions"),
    ]
    for feature_name, statement in checks:
        value = feature_row.get(feature_name)
        if value is None or pd.isna(value):
            continue
        if feature_name.endswith("__slope") and (
            (feature_name.startswith("oxygen") and value < -0.15)
            or (not feature_name.startswith("oxygen") and value > 0.8)
        ):
            drivers.append(statement)
        if feature_name == "glucose__max" and value > 220:
            drivers.append(statement)

    adherence = feature_row.get("medication_adherence__mean")
    if adherence is not None and not pd.isna(adherence) and adherence < 0.75:
        drivers.append("low medication adherence")

    dyspnea = feature_row.get("dyspnea_score__max")
    if dyspnea is not None and not pd.isna(dyspnea) and dyspnea >= 6:
        drivers.append("worsening dyspnea symptoms")

    return drivers[:5] or ["recent trajectory requires clinician review"]
