#!/usr/bin/env python3
"""Codex CLI health monitor.

Usage:
    python3 automation/cli_health.py

Pings `codex --version` and stores the result in `automation/cli_health.yaml`.
Supervisor reads this file to decide whether codex CLI is ready.
"""
from __future__ import annotations

import json
from pathlib import Path

from ductor_bot.cli.codex_health import CodexHealthMonitor

AUTOMATION_DIR = Path(__file__).resolve().parent
HEALTH_PATH = AUTOMATION_DIR / "cli_health.yaml"
MONITOR = CodexHealthMonitor()


def codex_cli_status() -> dict[str, object]:
    return MONITOR.to_payload(force=True)


def main() -> None:
    status = codex_cli_status()
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_PATH.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
