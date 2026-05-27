from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import astro_workloop
from automation import cli_health


def test_cli_health_defaults_to_ignored_runtime_path(monkeypatch) -> None:
    monkeypatch.delenv("SUPERVISOR_CLI_HEALTH_PATH", raising=False)

    assert cli_health.cli_health_path() == cli_health.AUTOMATION_DIR / ".runtime" / "cli_health.json"
    assert astro_workloop.cli_health_path() == astro_workloop.AUTOMATION_DIR / ".runtime" / "cli_health.json"


def test_cli_health_path_can_be_overridden(monkeypatch, tmp_path) -> None:
    target = tmp_path / "health" / "cli.json"
    monkeypatch.setenv("SUPERVISOR_CLI_HEALTH_PATH", str(target))

    assert cli_health.cli_health_path() == target
    assert astro_workloop.cli_health_path() == target


def test_cli_health_script_writes_configured_runtime_path(monkeypatch, tmp_path) -> None:
    target = tmp_path / "health" / "cli.json"
    monkeypatch.setenv("SUPERVISOR_CLI_HEALTH_PATH", str(target))
    monkeypatch.setattr(cli_health, "codex_cli_status", lambda: {"ok": True, "status": "ready"})

    cli_health.main()

    assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True, "status": "ready"}


def test_workloop_writes_configured_runtime_path(monkeypatch, tmp_path) -> None:
    target = tmp_path / "health" / "cli.json"
    monkeypatch.setenv("SUPERVISOR_CLI_HEALTH_PATH", str(target))

    with patch(
        "ductor_bot.cli.codex_health.CodexHealthMonitor",
        return_value=SimpleNamespace(to_payload=lambda force=True: {"ok": True, "status": "ready"}),
    ):
        assert astro_workloop.codex_cli_available() is True

    assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True, "status": "ready"}
