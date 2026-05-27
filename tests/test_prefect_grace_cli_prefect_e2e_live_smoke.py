"""Tests for run-prefect-e2e-live-smoke CLI."""

import json
import subprocess
import sys
from pathlib import Path


def _write_project_config(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_path = tmp_path / "project.yaml"
    config_path.write_text(f"""
version: 1
project_key: test-project
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
""")
    return config_path


def test_cli_prefect_e2e_live_smoke_offline_fake_submitter(tmp_path):
    """Verify CLI can run an offline fake-submitter smoke without live Prefect."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-prefect-e2e-live-smoke",
            "--project-config",
            str(_write_project_config(tmp_path)),
            "--state-root",
            str(tmp_path / "state"),
            "--worktree-root",
            str(tmp_path / "worktrees"),
            "--packet-root",
            str(tmp_path / "packets"),
            "--dry-run",
            "--offline-fake-submitter",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "run-prefect-e2e-live-smoke"
    assert output["result"]["submitted"] is True
    assert output["result"]["runner_kind"] == "e2e"
    assert output["result"]["deployment_name"] == "prefect-grace-e2e-packet-runner/live-e2e-packet-runner"
    assert output["result"]["flow_run_id"].startswith("fake-live-smoke-")


def test_cli_prefect_e2e_live_smoke_blocks_unsafe_live_agent(tmp_path):
    """Verify CLI exits 1 for safely blocked live-agent smoke."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-prefect-e2e-live-smoke",
            "--project-config",
            str(_write_project_config(tmp_path)),
            "--state-root",
            str(tmp_path / "state"),
            "--worktree-root",
            str(tmp_path / "worktrees"),
            "--packet-root",
            str(tmp_path / "packets"),
            "--no-dry-run",
            "--execute-agent",
            "--allow-live-agent-smoke",
            "--offline-fake-submitter",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["status"] == "blocked"
    assert output["errors"][0]["code"] == "LIVE_AGENT_SMOKE_GUARD_FAILED"


def test_cli_prefect_e2e_live_smoke_help():
    """Verify CLI help exposes required smoke flags."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-prefect-e2e-live-smoke", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--project-config" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--no-dry-run" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--allow-live-agent-smoke" in result.stdout
    assert "--json" in result.stdout
