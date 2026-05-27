"""Tests for run-prefect-e2e-batch-smoke CLI."""

import json
import subprocess
import sys
from pathlib import Path


def _write_project_config(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(exist_ok=True)
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


def _base_command(tmp_path: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "prefect_grace.cli",
        "run-prefect-e2e-batch-smoke",
        "--project-config",
        str(_write_project_config(tmp_path)),
        "--state-root",
        str(tmp_path / "state"),
        "--worktree-root",
        str(tmp_path / "worktrees"),
        "--packet-root",
        str(tmp_path / "packets"),
    ]


def test_cli_prefect_e2e_batch_smoke_offline_fake_submitter(tmp_path):
    """Verify CLI can run an offline fake-submitter batch smoke without live Prefect."""
    result = subprocess.run(
        [
            *_base_command(tmp_path),
            "--batch-size",
            "2",
            "--offline-fake-submitter",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "run-prefect-e2e-batch-smoke"
    assert output["result"]["batch_size"] == 2
    assert output["result"]["runner_kind"] == "e2e"
    assert output["result"]["deployment_name"] == "prefect-grace-e2e-packet-runner/live-e2e-packet-runner"
    assert output["result"]["work_queue_name"] == "grace-live"
    assert len(output["result"]["records"]) == 2
    assert output["result"]["packets_submitted"] == output["result"]["packets_planned"]
    assert all(record["flow_run_id"].startswith("fake-batch-smoke-") for record in output["result"]["records"])


def test_cli_prefect_e2e_batch_smoke_rejects_invalid_batch_sizes(tmp_path):
    """Verify CLI exits 1 for too-small and too-large batch sizes."""
    for batch_size, expected_code in [("1", "BATCH_SMOKE_TOO_SMALL"), ("4", "BATCH_SMOKE_TOO_LARGE")]:
        result = subprocess.run(
            [
                *_base_command(tmp_path),
                "--batch-size",
                batch_size,
                "--offline-fake-submitter",
                "--json",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert output["ok"] is False
        assert output["errors"][0]["code"] == expected_code


def test_cli_prefect_e2e_batch_smoke_rejects_execute_agent(tmp_path):
    """Verify batch smoke always rejects live-agent execution."""
    result = subprocess.run(
        [
            *_base_command(tmp_path),
            "--batch-size",
            "2",
            "--execute-agent",
            "--offline-fake-submitter",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["errors"][0]["code"] == "BATCH_LIVE_AGENT_UNSUPPORTED"
    assert output["result"]["records"] == []


def test_cli_prefect_e2e_batch_smoke_help():
    """Verify CLI help exposes required batch smoke flags."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-prefect-e2e-batch-smoke", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--project-config" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--batch-size" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--json" in result.stdout
