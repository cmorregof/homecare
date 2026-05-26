"""Validation helpers for Telegram vital sign reports."""


def parse_blood_pressure(value: str) -> tuple[int, int]:
    systolic, diastolic = value.strip().split("/", maxsplit=1)
    return int(systolic), int(diastolic)
