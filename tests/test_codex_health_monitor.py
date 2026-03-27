from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ductor_bot.cli.codex_health import CodexHealthMonitor, _default_codex_home
from ductor_bot.tasks.hub import TaskHub
from ductor_bot.tasks.models import TaskSubmit


def _make_codex_home(tmp_path: Path) -> Path:
    home = tmp_path / "codex-home"
    home.mkdir()
    (home / "auth.json").write_text(json.dumps({"token": "ok"}), encoding="utf-8")
    state = home / "state_1.sqlite"
    import sqlite3

    with sqlite3.connect(state) as conn:
        conn.execute("create table sample(id integer primary key)")
    return home


def test_codex_health_monitor_reports_healthy(tmp_path: Path) -> None:
    home = _make_codex_home(tmp_path)
    monitor = CodexHealthMonitor(codex_home=home)
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stderr="", stdout="codex 1.0")):
        status = monitor.get_status(force=True)
    assert status.ok is True
    assert status.state_ok is True
    assert status.ping_ok is True


def test_codex_health_monitor_reports_bad_state(tmp_path: Path) -> None:
    home = tmp_path / "codex-home"
    home.mkdir()
    monitor = CodexHealthMonitor(codex_home=home)
    with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stderr="", stdout="codex 1.0")):
        status = monitor.get_status(force=True)
    assert status.ok is False
    assert status.state_ok is False
    assert "missing auth file" in status.details


def test_codex_health_monitor_payload_includes_ping_and_state(tmp_path: Path) -> None:
    home = _make_codex_home(tmp_path)
    monitor = CodexHealthMonitor(codex_home=home)
    with patch("ductor_bot.cli.codex_health.which", return_value="/usr/bin/codex"), patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stderr="", stdout="codex 1.0")):
        payload = monitor.to_payload(force=True)
    assert payload["status"] == "ready"
    assert payload["ok"] is True
    assert payload["ping_ok"] is True
    assert payload["state_ok"] is True
    assert "checked_at" in payload


def test_default_codex_home_uses_env_override(tmp_path: Path) -> None:
    explicit = tmp_path / "custom-home"
    explicit.mkdir()
    with patch.dict(os.environ, {"CODEX_HOME": str(explicit)}, clear=False):
        assert _default_codex_home() == explicit


def test_default_codex_home_prefers_ductor_cliproxy(tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    cliproxy = fake_home / ".ductor" / "codex-cliproxy-home"
    cliproxy.mkdir(parents=True)
    with patch.dict(os.environ, {}, clear=True), patch("pathlib.Path.home", return_value=fake_home):
        assert _default_codex_home() == cliproxy


def test_taskhub_submit_blocks_unhealthy_codex(tmp_path: Path) -> None:
    registry = SimpleNamespace()
    paths = SimpleNamespace()
    hub = TaskHub(registry, paths, cli_service=object(), config=SimpleNamespace(enabled=True, max_parallel=2, timeout_seconds=10))
    submit = TaskSubmit(
        chat_id=1,
        message_id=1,
        parent_agent="main",
        name="test",
        prompt="hello",
        provider_override="codex",
        model_override="",
        thinking_override="",
        thread_id=None,
    )
    with patch("ductor_bot.tasks.hub._CODEX_HEALTH.ensure_healthy", side_effect=RuntimeError("Codex CLI is unhealthy")):
        try:
            hub.submit(submit)
        except RuntimeError as exc:
            assert "unhealthy" in str(exc)
        else:
            raise AssertionError("expected RuntimeError")
