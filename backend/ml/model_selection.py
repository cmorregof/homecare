"""Model selection utilities for the Sprint 2 training pipeline."""


def select_best_model(results: list[dict[str, object]]) -> dict[str, object]:
    if not results:
        raise ValueError("At least one model result is required.")
    return max(results, key=lambda item: float(item.get("f1_macro", 0.0)))
