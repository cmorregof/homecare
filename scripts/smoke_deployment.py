#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HomecareCCV post-deploy smoke checks.")
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_PUBLIC_URL"))
    parser.add_argument("--frontend-url", default=os.getenv("FRONTEND_PUBLIC_URL"))
    parser.add_argument("--telegram-token", default=os.getenv("TELEGRAM_BOT_TOKEN"))
    args = parser.parse_args()

    checks: list[tuple[str, bool, str]] = []
    if args.backend_url:
        checks.append(_check_backend(args.backend_url))
    if args.frontend_url:
        checks.append(_check_frontend(args.frontend_url))
    if args.telegram_token:
        checks.append(_check_telegram(args.telegram_token))

    if not checks:
        print("No smoke targets provided. Set BACKEND_PUBLIC_URL, FRONTEND_PUBLIC_URL, or TELEGRAM_BOT_TOKEN.")
        raise SystemExit(1)

    failed = False
    for name, ok, detail in checks:
        status = "OK" if ok else "FAIL"
        print(f"{status} {name}: {detail}")
        failed = failed or not ok

    if failed:
        raise SystemExit(1)


def _check_backend(base_url: str) -> tuple[str, bool, str]:
    try:
        payload = _get_json(f"{base_url.rstrip('/')}/health")
        return ("backend /health", payload.get("status") == "ok", json.dumps(payload, ensure_ascii=False))
    except Exception as exc:
        return ("backend /health", False, str(exc))


def _check_frontend(base_url: str) -> tuple[str, bool, str]:
    try:
        status, body = _get_text(base_url.rstrip("/"))
        ok = status < 400 and ("HomecareCCV" in body or "html" in body[:200].lower())
        return ("frontend", ok, f"HTTP {status}")
    except Exception as exc:
        return ("frontend", False, str(exc))


def _check_telegram(token: str) -> tuple[str, bool, str]:
    try:
        payload = _get_json(f"https://api.telegram.org/bot{token}/getMe")
        result = payload.get("result") or {}
        return ("telegram getMe", bool(payload.get("ok")), str(result.get("username") or payload))
    except Exception as exc:
        return ("telegram getMe", False, str(exc))


def _get_json(url: str) -> dict[str, object]:
    status, body = _get_text(url)
    if status >= 400:
        raise RuntimeError(f"HTTP {status}: {body[:200]}")
    return json.loads(body)


def _get_text(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "homecareccv-smoke/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
