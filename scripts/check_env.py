#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path


BACKEND_REQUIRED = [
    "OPENAI_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_ANON_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_URL",
    "ML_MODEL_PATH",
]

FRONTEND_REQUIRED = [
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_TELEGRAM_BOT_URL",
]

PLACEHOLDER_MARKERS = ("...", "xxxxx", "7xxxxxxxxx", "sk-", "eyJhbGciOiJIUzI1NiIs")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate HomecareCCV deployment variables.")
    parser.add_argument("--target", choices=["backend", "frontend", "all"], default="all")
    parser.add_argument("--template", type=Path, help="Optional .env template file to inspect.")
    parser.add_argument("--allow-placeholder", action="store_true", help="Allow placeholder values in templates.")
    args = parser.parse_args()

    env_values = _load_template(args.template) if args.template else dict(os.environ)
    required = []
    if args.target in {"backend", "all"}:
        required.extend(BACKEND_REQUIRED)
    if args.target in {"frontend", "all"}:
        required.extend(FRONTEND_REQUIRED)

    missing = [name for name in required if not env_values.get(name)]
    placeholders = [
        name
        for name in required
        if env_values.get(name) and _looks_placeholder(env_values[name]) and not args.allow_placeholder
    ]

    if missing or placeholders:
        if missing:
            print("Missing variables:")
            for name in missing:
                print(f"- {name}")
        if placeholders:
            print("Placeholder variables:")
            for name in placeholders:
                print(f"- {name}")
        raise SystemExit(1)

    print(f"Environment check passed for {args.target}.")


def _load_template(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        values[key.strip()] = value.strip()
    return values


def _looks_placeholder(value: str) -> bool:
    return any(marker in value for marker in PLACEHOLDER_MARKERS)


if __name__ == "__main__":
    main()
