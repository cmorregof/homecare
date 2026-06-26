"""Configuration constants for the CARMEN-Forecast research scaffold."""

LOOKBACK_HOURS = 24
HORIZON_HOURS = 6
DEFAULT_RANDOM_STATE = 42

RISK_TIER_THRESHOLDS = {
    "low": 0.25,
    "moderate": 0.50,
    "high": 0.75,
}

IMMEDIATE_OVERRIDE_THRESHOLDS = {
    "systolic_bp_high": 180,
    "systolic_bp_low": 80,
    "heart_rate_high": 130,
    "heart_rate_low": 40,
    "oxygen_saturation_low": 88,
    "glucose_high": 400,
    "glucose_low": 50,
    "severe_symptom_score": 8,
}

SAFETY_NOTE = (
    "This is not a diagnosis or prescription. Human clinical review is required."
)
