#!/usr/bin/env python3
import os
from typing import Any

import requests


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
TEST_AUTH = os.getenv("X_TELEGRAM_AUTH", "999")
TIMEOUT = float(os.getenv("VERIFY_TIMEOUT", "20"))


def _headers(include_auth: bool = False) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if include_auth and TEST_AUTH:
        headers["X-Telegram-Auth"] = TEST_AUTH
    return headers


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _request(path: str, *, include_auth: bool = False) -> requests.Response:
    url = f"{API_URL}{path}"
    response = requests.get(url, headers=_headers(include_auth), timeout=TIMEOUT)
    print(f"[HTTP] GET {path} -> {response.status_code}")
    return response


def _json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError as exc:
        raise AssertionError(f"Expected JSON response, got: {response.text[:200]}") from exc


def verify_daily_feed() -> None:
    response = _request("/api/feed/today", include_auth=True)
    _require(response.status_code == 200, f"/api/feed/today returned {response.status_code}: {response.text[:200]}")

    payload = _json(response)
    _require(isinstance(payload, dict), "Daily feed payload must be a JSON object")

    for field in ("date", "moon_sign", "moon_phase", "moon_emoji", "general_vibe", "traffic_lights", "aspects_count"):
        _require(field in payload, f"Daily feed missing field: {field}")

    _require(isinstance(payload["general_vibe"], str) and payload["general_vibe"].strip(), "general_vibe must be a non-empty string")
    _require(isinstance(payload["aspects_count"], int), "aspects_count must be an integer")

    traffic_lights = payload["traffic_lights"]
    _require(isinstance(traffic_lights, dict), "traffic_lights must be an object")
    _require(set(traffic_lights.keys()) == {"health", "money", "love"}, "traffic_lights must contain health/money/love")
    print(f"[OK] Daily feed baseline green: {payload['moon_sign']} / {payload['moon_phase']}")


def verify_payment_packs() -> None:
    response = _request("/api/billing/packs")
    _require(response.status_code == 200, f"/api/billing/packs returned {response.status_code}: {response.text[:200]}")

    payload = _json(response)
    _require(isinstance(payload, dict), "Billing packs payload must be a JSON object")

    for pack_id in ("pack_1", "pack_3", "pack_5"):
        _require(pack_id in payload, f"Missing billing pack: {pack_id}")
        pack = payload[pack_id]
        _require(isinstance(pack, dict), f"{pack_id} must be an object")
        _require(isinstance(pack.get("price"), (int, float)) and pack["price"] > 0, f"{pack_id} price must be positive")
        _require(isinstance(pack.get("credits"), int) and pack["credits"] > 0, f"{pack_id} credits must be positive")

    print(f"[OK] Billing packs baseline green: {', '.join(payload.keys())}")


def main() -> int:
    print(f"Verifying API responses against {API_URL}")
    try:
        verify_daily_feed()
        verify_payment_packs()
    except (AssertionError, requests.RequestException) as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("[PASS] API response verification baseline is green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
