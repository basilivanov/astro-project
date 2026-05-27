#!/usr/bin/env python3
"""Codex CLI health monitor.

Usage:
    python3 automation/cli_health.py

Pings `codex --version` and stores the result in a local runtime file.
Supervisor reads this file to decide whether codex CLI is ready.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ductor_bot.cli.codex_health import CodexHealthMonitor

AUTOMATION_DIR = Path(__file__).resolve().parent
DEFAULT_HEALTH_PATH = AUTOMATION_DIR / ".runtime" / "cli_health.json"
MONITOR = CodexHealthMonitor()


def cli_health_path() -> Path:
    configured = os.environ.get("SUPERVISOR_CLI_HEALTH_PATH")
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_HEALTH_PATH


def codex_cli_status() -> dict[str, object]:
    return MONITOR.to_payload(force=True)


def main() -> None:
    status = codex_cli_status()
    health_path = cli_health_path()
    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
