import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

import prefect_grace.cli as cli


def _write_project_config(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_path = tmp_path / "project.yaml"
    config_path.write_text(f"""
version: 1
project_key: cli-test-project
repo_root: {repo_root}
default_branch: main
grace_dir: grace
packets_dir: packets
runtime_state_root: {tmp_path / "project-state"}
artifact_root: {tmp_path / "artifacts"}
worktree_root: {tmp_path / "project-worktrees"}
workflow_runtime: prefect
prefect:
  work_pool: test-pool
  live_queue: test-live
  monitoring_queue: test-monitoring
agent_executor:
  default: codex-cli
  command: codex1
""", encoding="utf-8")
    return config_path


def test_cli_live_opt_in_single_scratch_help_exposes_safety_flags() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-live-opt-in-single-scratch-packet", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--i-understand-live-agent" in result.stdout
    assert "--timeout-seconds" in result.stdout
    assert "--json" in result.stdout


def test_cli_live_opt_in_single_scratch_fails_closed_without_env_token(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("GRACE_LIVE_AGENT_OPT_IN", raising=False)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-live-opt-in-single-scratch-packet",
            "--project",
            str(_write_project_config(tmp_path)),
            "--state-root",
            str(tmp_path / "state"),
            "--worktree-root",
            str(tmp_path / "worktrees"),
            "--packet-root",
            str(tmp_path / "packets"),
            "--execute-agent",
            "--i-understand-live-agent",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    data = json.loads(result.stdout)
    assert result.returncode == 1
    assert data["ok"] is False
    assert data["command"] == "run-live-opt-in-single-scratch-packet"
    assert data["result"] == data["data"]
    assert data["data"]["agent_launch_count"] == 0
    assert data["data"]["opt_in_confirmed"] is False
    assert data["errors"][0]["code"] == "LIVE_OPT_IN_TOKEN_REQUIRED"


def test_cli_live_opt_in_single_scratch_passes_env_token_to_runner(monkeypatch, tmp_path: Path, capsys) -> None:
    captured: dict[str, object] = {}

    class Result:
        ok = True
        project_key = "cli-test-project"
        warnings: list[str] = []
        errors: list[dict] = []

        def to_dict(self):
            return {
                "ok": True,
                "project_key": self.project_key,
                "mode": "live_opt_in_single_scratch_packet",
                "opt_in_confirmed": True,
                "agent_launch_count": 1,
            }

    def fake_run(**kwargs):
        captured.update(kwargs)
        return Result()

    monkeypatch.setenv("GRACE_LIVE_AGENT_OPT_IN", "single-scratch")
    monkeypatch.setattr(
        "prefect_grace.platform.live_opt_in_single_scratch_packet.run_live_opt_in_single_scratch_packet",
        fake_run,
    )

    args = argparse.Namespace(
        project=str(tmp_path / "project.yaml"),
        state_root=str(tmp_path / "state"),
        worktree_root=str(tmp_path / "worktrees"),
        packet_root=str(tmp_path / "packets"),
        execute_agent=True,
        i_understand_live_agent=True,
        timeout_seconds=1800,
        json=True,
    )

    with pytest.raises(SystemExit) as exc:
        cli._cmd_run_live_opt_in_single_scratch_packet(args)

    data = json.loads(capsys.readouterr().out)
    assert exc.value.code == 0
    assert captured["opt_in_token"] == "single-scratch"
    assert captured["execute_agent"] is True
    assert captured["acknowledge_live_agent"] is True
    assert data["ok"] is True
    assert data["result"]["agent_launch_count"] == 1
