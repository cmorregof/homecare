from __future__ import annotations

import re
from typing import Any


OPTIONAL_SKIP_VALUES = {
    "no",
    "no medi",
    "no medí",
    "no tengo",
    "no aplica",
    "n/a",
    "na",
    "ninguno",
}


def parse_blood_pressure(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d{2,3})\s*/\s*(\d{2,3})\s*", value)
    if not match:
        raise ValueError("Escribe la presión con el formato 120/80.")
    systolic, diastolic = match.groups()
    systolic_value = int(systolic)
    diastolic_value = int(diastolic)
    if not 50 <= systolic_value <= 260 or not 30 <= diastolic_value <= 160:
        raise ValueError("La presión parece fuera del rango reportable. Revísala y envíala de nuevo.")
    if systolic_value <= diastolic_value:
        raise ValueError("La sistólica debe ser mayor que la diastólica. Ejemplo: 120/80.")
    return systolic_value, diastolic_value


def parse_required_number(
    value: str,
    *,
    label: str,
    minimum: float,
    maximum: float,
) -> float | int:
    parsed = _parse_number(value)
    if parsed is None:
        raise ValueError(f"Escribe un número para {label}.")
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"El valor de {label} parece fuera del rango reportable.")
    return _int_if_whole(parsed)


def parse_optional_number(
    value: str,
    *,
    label: str,
    minimum: float,
    maximum: float,
) -> float | int | None:
    if is_skip_value(value):
        return None
    return parse_required_number(value, label=label, minimum=minimum, maximum=maximum)


def parse_score(value: str, *, label: str) -> int:
    parsed = parse_required_number(value, label=label, minimum=0, maximum=10)
    if isinstance(parsed, float):
        raise ValueError(f"Usa un número entero de 0 a 10 para {label}.")
    return parsed


def is_affirmative(value: str) -> bool:
    return _normalize(value) in {"si", "sí", "s", "claro", "listo", "ok", "dale"}


def is_negative(value: str) -> bool:
    return _normalize(value) in {"no", "n", "despues", "después", "luego", "ahora no"}


def is_skip_value(value: str) -> bool:
    return _normalize(value) in OPTIONAL_SKIP_VALUES


def normalize_telegram_id(value: int | str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _parse_number(value: str) -> float | None:
    match = re.search(r"-?\d+(?:[\.,]\d+)?", value.strip())
    if not match:
        return None
    return float(match.group(0).replace(",", "."))


def _int_if_whole(value: float) -> float | int:
    if value.is_integer():
        return int(value)
    return value


def _normalize(value: Any) -> str:
    return str(value).strip().lower()
