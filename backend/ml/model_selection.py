from __future__ import annotations


def select_best_model(results: list[dict[str, object]]) -> dict[str, object]:
    candidates = [result for result in results if result.get("status") == "trained"]
    if not candidates:
        raise ValueError("At least one model result is required.")
    return max(candidates, key=lambda item: float(item.get("validation", {}).get("f1_macro", 0.0)))
