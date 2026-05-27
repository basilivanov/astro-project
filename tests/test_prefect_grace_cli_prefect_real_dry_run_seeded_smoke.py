"""Tests for run-prefect-real-dry-run-seeded-smoke CLI."""

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from prefect_grace import cli
from prefect_grace.platform.prefect_real_dry_run_seeded_smoke import (
    PACKET_CHILD_RUNNABLE,
    PrefectRealDryRunSeededSmokeResult,
    SMOKE_MODE,
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


def test_cli_prefect_real_dry_run_seeded_smoke_help():
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-prefect-real-dry-run-seeded-smoke", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--timeout-seconds" in result.stdout
    assert "--poll-interval-seconds" in result.stdout
    assert "--no-wait" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--json" in result.stdout


def test_cli_prefect_real_dry_run_seeded_smoke_rejects_execute_agent(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-prefect-real-dry-run-seeded-smoke",
            "--project",
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
    assert output["command"] == "run-prefect-real-dry-run-seeded-smoke"
    assert output["result"] == output["data"]
    assert output["errors"][0]["code"] == "PREFECT_SEEDED_DRY_RUN_EXECUTE_AGENT_REJECTED"


def test_cli_prefect_real_dry_run_seeded_smoke_json_envelope(monkeypatch, capsys, tmp_path):
    from prefect_grace.platform import prefect_real_dry_run_seeded_smoke as smoke_module

    def fake_run(**kwargs):
        assert kwargs["wait"] is False
        assert kwargs["timeout_seconds"] == 17
        assert kwargs["poll_interval_seconds"] == 3
        assert kwargs["execute_agent"] is False
        return PrefectRealDryRunSeededSmokeResult(
            ok=True,
            project_key="test-project",
            mode=SMOKE_MODE,
            state_root=str(tmp_path / "state"),
            worktree_root=str(tmp_path / "worktrees"),
            packet_root=str(tmp_path / "packets"),
            selected_packet_id=PACKET_CHILD_RUNNABLE,
            bootstrap_apply_count=3,
            sync_plan={"ready": [PACKET_CHILD_RUNNABLE]},
            submit_plan={"packets_to_submit": [PACKET_CHILD_RUNNABLE]},
            deployment_name=E2E_PACKET_DEPLOYMENT_NAME,
            work_queue_name="test-live",
            flow_run_id="flow-run-seeded-smoke",
            flow_run_name="e2e-packet:CHILD-RUNNABLE:attempt-1",
            flow_run_url="http://prefect.local/flow-runs/flow-run-seeded-smoke",
            submitted=True,
            waited=False,
            prefect_state_type=None,
            prefect_state_name=None,
            domain_status=None,
            artifact_ids=[],
            prefect_runs_created=1,
            live_agents_started=0,
            writes_outside_temp_roots=[],
            warnings=[],
            errors=[],
            cases=[],
        )

    monkeypatch.setattr(smoke_module, "run_prefect_real_dry_run_seeded_smoke", fake_run)
    args = Namespace(
        project=str(_write_project_config(tmp_path)),
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
        cli._cmd_run_prefect_real_dry_run_seeded_smoke(args)

    assert exc.value.code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["ok"] is True
    assert output["command"] == "run-prefect-real-dry-run-seeded-smoke"
    assert output["project_key"] == "test-project"
    assert output["result"] == output["data"]
    assert output["result"]["selected_packet_id"] == PACKET_CHILD_RUNNABLE
