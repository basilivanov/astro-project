"""Tests for run-prefect-e2e-real-dry-run-smoke CLI."""

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from prefect_grace import cli
from prefect_grace.platform.prefect_e2e_real_dry_run_smoke import (
    PrefectE2ERealDryRunSmokeResult,
    SMOKE_MODE,
    SMOKE_PACKET_ID,
)
from prefect_grace.tasks.prefect_submitter import E2E_PACKET_DEPLOYMENT_NAME


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


def test_cli_prefect_e2e_real_dry_run_smoke_help():
    """Verify CLI help exposes required real smoke flags and no fake submitter flag."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-prefect-e2e-real-dry-run-smoke", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--project-config" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--timeout-seconds" in result.stdout
    assert "--poll-interval-seconds" in result.stdout
    assert "--no-wait" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--json" in result.stdout
    assert "--offline-fake-submitter" not in result.stdout


def test_cli_prefect_e2e_real_dry_run_smoke_rejects_execute_agent(tmp_path):
    """Verify CLI exits 1 before submission when --execute-agent is present."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-prefect-e2e-real-dry-run-smoke",
            "--project-config",
            str(_write_project_config(tmp_path)),
            "--state-root",
            str(tmp_path / "state"),
            "--worktree-root",
            str(tmp_path / "worktrees"),
            "--packet-root",
            str(tmp_path / "packets"),
            "--execute-agent",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["command"] == "run-prefect-e2e-real-dry-run-smoke"
    assert output["errors"][0]["code"] == "REAL_DRY_RUN_EXECUTE_AGENT_REJECTED"
    assert output["result"]["submitted"] is False


def test_cli_prefect_e2e_real_dry_run_smoke_json_envelope(monkeypatch, capsys, tmp_path):
    """Verify CLI JSON envelope is stable for a successful no-wait result."""
    from prefect_grace.platform import prefect_e2e_real_dry_run_smoke as smoke_module

    def fake_run(**kwargs):
        assert kwargs["wait"] is False
        assert kwargs["timeout_seconds"] == 17
        assert kwargs["poll_interval_seconds"] == 3
        return PrefectE2ERealDryRunSmokeResult(
            ok=True,
            mode=SMOKE_MODE,
            packet_id=SMOKE_PACKET_ID,
            runner_kind="e2e",
            deployment_name=E2E_PACKET_DEPLOYMENT_NAME,
            work_queue_name="test-live",
            flow_run_id="flow-run-real-smoke",
            flow_run_name="e2e-packet:real-smoke:attempt-1",
            flow_run_url="http://prefect.local/flow-runs/flow-run-real-smoke",
            submitted=True,
            waited=False,
            prefect_state_type=None,
            prefect_state_name=None,
            domain_status=None,
            artifact_ids=[],
            errors=[],
        )

    monkeypatch.setattr(smoke_module, "run_prefect_e2e_real_dry_run_smoke", fake_run)
    args = Namespace(
        project_config=str(_write_project_config(tmp_path)),
        state_root=str(tmp_path / "state"),
        worktree_root=str(tmp_path / "worktrees"),
        packet_root=str(tmp_path / "packets"),
        timeout_seconds=17,
        poll_interval_seconds=3,
        no_wait=True,
        execute_agent=False,
        json=True,
    )

    with pytest.raises(SystemExit) as exc:
        cli._cmd_run_prefect_e2e_real_dry_run_smoke(args)

    assert exc.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is True
    assert output["command"] == "run-prefect-e2e-real-dry-run-smoke"
    assert output["result"]["flow_run_id"] == "flow-run-real-smoke"
    assert output["result"] == output["data"]
