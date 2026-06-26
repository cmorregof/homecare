from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_synthetic_carmen_data(
    n_patients: int = 200,
    observations_per_patient: int = 24,
    interval_hours: int = 6,
    random_state: int = 42,
) -> pd.DataFrame:
    """Generate synthetic longitudinal data for pipeline testing only.

    This dataset is intentionally simulated and must never be interpreted as
    evidence of clinical performance.
    """

    rng = np.random.default_rng(random_state)
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    trajectories = [
        "stable",
        "gradual_worsening",
        "sudden_deterioration",
        "non_adherence",
        "hypoxemia",
        "hypertensive_episode",
        "glucose_excursion",
    ]
    sexes = ["female", "male"]
    rows: list[dict[str, object]] = []

    for patient_index in range(n_patients):
        patient_id = f"P{patient_index + 1:03d}"
        trajectory = str(rng.choice(trajectories, p=[0.32, 0.18, 0.12, 0.12, 0.10, 0.08, 0.08]))
        age = int(rng.integers(38, 90))
        sex = str(rng.choice(sexes))
        previous_event_flag = int(rng.random() < 0.18)

        systolic = rng.normal(126, 10)
        diastolic = rng.normal(78, 7)
        heart_rate = rng.normal(76, 8)
        oxygen = rng.normal(96.5, 1.2)
        glucose = rng.normal(112, 18)
        temperature = rng.normal(36.7, 0.2)
        pain = max(0.0, rng.normal(1.5, 1.0))
        dizziness = max(0.0, rng.normal(1.2, 1.0))
        dyspnea = max(0.0, rng.normal(1.0, 1.0))
        adherence = float(np.clip(rng.normal(0.92, 0.06), 0.45, 1.0))
        activity = float(np.clip(rng.normal(0.60, 0.15), 0.05, 1.0))

        patient_rows: list[dict[str, object]] = []
        sudden_start = int(rng.integers(max(2, observations_per_patient // 2), observations_per_patient))

        for obs_index in range(observations_per_patient):
            time_fraction = obs_index / max(1, observations_per_patient - 1)

            systolic += rng.normal(0, 3)
            diastolic += rng.normal(0, 2)
            heart_rate += rng.normal(0, 2.5)
            oxygen += rng.normal(0, 0.4)
            glucose += rng.normal(0, 6)
            temperature += rng.normal(0, 0.08)
            pain = np.clip(pain + rng.normal(0, 0.5), 0, 10)
            dizziness = np.clip(dizziness + rng.normal(0, 0.5), 0, 10)
            dyspnea = np.clip(dyspnea + rng.normal(0, 0.5), 0, 10)
            adherence = float(np.clip(adherence + rng.normal(0, 0.03), 0, 1))
            activity = float(np.clip(activity + rng.normal(0, 0.05), 0, 1))

            if trajectory == "gradual_worsening":
                systolic += 1.2
                heart_rate += 1.1
                oxygen -= 0.15
                pain = np.clip(pain + 0.25, 0, 10)
                dyspnea = np.clip(dyspnea + 0.22, 0, 10)
                adherence = float(np.clip(adherence - 0.01, 0, 1))
            elif trajectory == "sudden_deterioration" and obs_index >= sudden_start:
                systolic += 4.5
                heart_rate += 4.0
                oxygen -= 1.2
                temperature += 0.12
                dyspnea = np.clip(dyspnea + 0.7, 0, 10)
                dizziness = np.clip(dizziness + 0.6, 0, 10)
            elif trajectory == "non_adherence":
                adherence = float(np.clip(adherence - 0.03, 0, 1))
                if adherence < 0.65:
                    systolic += 1.8
                    glucose += 4.5
                    pain = np.clip(pain + 0.18, 0, 10)
            elif trajectory == "hypoxemia":
                oxygen -= 0.22
                heart_rate += 0.7
                dyspnea = np.clip(dyspnea + 0.3, 0, 10)
            elif trajectory == "hypertensive_episode":
                systolic += 2.0 if time_fraction > 0.45 else 0.3
                diastolic += 1.2 if time_fraction > 0.45 else 0.2
                dizziness = np.clip(dizziness + 0.2, 0, 10)
            elif trajectory == "glucose_excursion":
                glucose += 7.0 if obs_index % 4 in {2, 3} else -2.0
                activity = float(np.clip(activity - 0.02, 0, 1))

            systolic = float(np.clip(systolic, 70, 230))
            diastolic = float(np.clip(diastolic, 40, 130))
            heart_rate = float(np.clip(heart_rate, 35, 165))
            oxygen = float(np.clip(oxygen, 78, 100))
            glucose = float(np.clip(glucose, 45, 430))
            temperature = float(np.clip(temperature, 35.0, 40.5))

            severity_score = (
                (systolic >= 180 or systolic < 80) * 3
                + (heart_rate > 130 or heart_rate < 40) * 3
                + (oxygen < 88) * 3
                + (glucose > 400 or glucose < 50) * 3
                + (dyspnea >= 8 or dizziness >= 8 or pain >= 8) * 2
                + (adherence < 0.55) * 1
                + previous_event_flag * 1
            )

            if severity_score >= 6:
                risk_state = "critical"
            elif severity_score >= 4:
                risk_state = "high"
            elif severity_score >= 2:
                risk_state = "moderate"
            else:
                risk_state = "low"

            patient_rows.append(
                {
                    "patient_id": patient_id,
                    "timestamp": start_time + timedelta(hours=obs_index * interval_hours),
                    "age": age,
                    "sex": sex,
                    "systolic_bp": round(systolic, 1),
                    "diastolic_bp": round(diastolic, 1),
                    "heart_rate": round(heart_rate, 1),
                    "oxygen_saturation": round(oxygen, 1),
                    "glucose": round(glucose, 1),
                    "temperature": round(temperature, 1),
                    "pain_score": round(float(pain), 1),
                    "dizziness_score": round(float(dizziness), 1),
                    "dyspnea_score": round(float(dyspnea), 1),
                    "medication_adherence": round(adherence, 3),
                    "activity_level": round(activity, 3),
                    "previous_event_flag": previous_event_flag,
                    "risk_state": risk_state,
                }
            )

        for obs_index, row in enumerate(patient_rows):
            next_row = patient_rows[obs_index + 1] if obs_index + 1 < len(patient_rows) else None
            future_deterioration = int(next_row is not None and next_row["risk_state"] in {"high", "critical"})
            row["future_deterioration_6h"] = future_deterioration
            rows.append(row)

    frame = pd.DataFrame(rows).sort_values(["patient_id", "timestamp"]).reset_index(drop=True)
    return frame
