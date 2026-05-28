# ############################################################################
# AI_HEADER: test_prefect_grace_cli_nightly_controlled_batch_run
# ROLE: CLI contract tests for controlled nightly batch run command.
# ############################################################################

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def _project(tmp_path: Path) -> Path:
    (tmp_path / "prefect_grace" / "packets").mkdir(parents=True)
    project = tmp_path / "prefect_grace" / "project.yaml"
    project.write_text(
        "\n".join([
            "version: 1",
            "project_key: cli-controlled-test",
            f"repo_root: {tmp_path}",
            "default_branch: main",
            "grace_dir: grace",
            "packets_dir: prefect_grace/packets",
            f"runtime_state_root: {tmp_path / 'runtime'}",
            f"artifact_root: {tmp_path / 'artifacts'}",
            f"worktree_root: {tmp_path / 'worktrees'}",
            "workflow_runtime: prefect",
            "prefect:",
            "  work_pool: test-pool",
            "  live_queue: grace-live",
            "  monitoring_queue: grace-monitoring",
        ]),
        encoding="utf-8",
    )
    return project


def _run_cli(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", *args],
        capture_output=True,
        text=True,
        env=merged_env,
    )


def test_run_nightly_controlled_batch_help_contract() -> None:
    result = _run_cli(["run-nightly-controlled-batch", "--help"])

    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--selection" in result.stdout
    assert "--max-packets" in result.stdout
    assert "--concurrency" in result.stdout
    assert "--timeout-seconds-per-packet" in result.stdout
    assert "--max-failures" in result.stdout
    assert "--no-stop-on-degradation" in result.stdout
    assert "--allow-git-commit" in result.stdout
    assert "--allow-git-push" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--execute" in result.stdout
    assert "--i-understand-live-batch" in result.stdout
    assert "--json" in result.stdout
    assert "--allow-git-merge" not in result.stdout
    assert "--merge" not in result.stdout


def test_run_nightly_controlled_batch_dry_run_json_envelope(tmp_path: Path) -> None:
    result = _run_cli([
        "run-nightly-controlled-batch",
        "--project",
        str(_project(tmp_path)),
        "--json",
    ])

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["command"] == "run-nightly-controlled-batch"
    assert output["result"] == output["data"]
    assert output["result"]["mode"] == "nightly_controlled_batch_run"
    assert output["result"]["dry_run"] is True
    assert output["result"]["executed_total"] == 0
    assert output["result"]["live_agents_started"] == 0
    assert output["result"]["prefect_runs_created"] == 0
    assert output["result"]["controls"]["max_packets"] == 3
    assert output["result"]["controls"]["concurrency"] == 1
    assert output["result"]["allow_merge"] is False


def test_run_nightly_controlled_batch_missing_live_approval_blocks_before_recheck(tmp_path: Path) -> None:
    result = _run_cli(
        [
            "run-nightly-controlled-batch",
            "--project",
            str(_project(tmp_path)),
            "--execute",
            "--json",
        ],
        env={"GRACE_NIGHTLY_BATCH_EXECUTION_APPROVED": "0"},
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    payload = output["result"]
    assert output["result"] == output["data"]
    assert payload["stop_reason"] == "live_opt_in_blocked"
    assert payload["executed_total"] == 0
    assert payload["live_agents_started"] == 0
    assert payload["prefect_runs_created"] == 0
    assert payload["recheck"] == {}
    assert {blocker["code"] for blocker in payload["blockers"]} == {
        "LIVE_BATCH_ACK_REQUIRED",
        "LIVE_BATCH_TOKEN_REQUIRED",
    }


def test_run_nightly_controlled_batch_execute_dry_run_conflict_fails_closed(tmp_path: Path) -> None:
    result = _run_cli([
        "run-nightly-controlled-batch",
        "--project",
        str(_project(tmp_path)),
        "--execute",
        "--dry-run",
        "--json",
    ])

    assert result.returncode == 2
    assert "not allowed with argument" in result.stderr
    assert result.stdout == ""


def test_run_nightly_controlled_batch_rejects_concurrency_above_one(tmp_path: Path) -> None:
    result = _run_cli([
        "run-nightly-controlled-batch",
        "--project",
        str(_project(tmp_path)),
        "--concurrency",
        "2",
        "--json",
    ])

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["result"]["stop_reason"] == "control_blocked"
    assert any(
        blocker["code"] == "CONCURRENCY_MUST_BE_ONE"
        for blocker in output["result"]["blockers"]
    )
