"""Unify Kaggle datasets into the HomecareCCV feature schema.

Implemented in Sprint 2.
"""


def assign_risk_level(row: dict[str, object]) -> int:
    score = 0
    systolic_bp = float(row.get("systolic_bp") or 0)
    glucose = float(row.get("glucose") or 0)
    bmi = float(row.get("bmi") or 0)

    if systolic_bp >= 180 or systolic_bp < 80:
        score += 3
    elif systolic_bp >= 160 or systolic_bp < 90:
        score += 2
    elif systolic_bp >= 140:
        score += 1

    if bool(row.get("stroke_history")):
        score += 2
    if bool(row.get("heart_disease_history")):
        score += 1
    if bool(row.get("hypertension_history")):
        score += 1
    if glucose > 300:
        score += 2
    elif glucose > 200:
        score += 1
    if bmi > 35:
        score += 1
    if int(row.get("cholesterol_level") or 0) == 3:
        score += 1

    if score >= 7:
        return 3
    if score >= 5:
        return 2
    if score >= 3:
        return 1
    return 0


def main() -> None:
    raise NotImplementedError("Dataset unification belongs to Sprint 2.")


if __name__ == "__main__":
    main()
