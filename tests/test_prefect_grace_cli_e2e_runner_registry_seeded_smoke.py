import json
import subprocess
import sys
from pathlib import Path

from prefect_grace.platform.e2e_runner_registry_seeded_smoke import PACKET_CHILD_RUNNABLE


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG = PROJECT_ROOT / "prefect_grace" / "project.yaml"


def test_cli_run_e2e_registry_seeded_smoke_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-e2e-registry-seeded-smoke", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--packet-root" in result.stdout
    assert "--json" in result.stdout
    assert "--execute-agent" not in result.stdout
    assert "--no-dry-run" not in result.stdout


def test_cli_run_e2e_registry_seeded_smoke_json_envelope(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-e2e-registry-seeded-smoke",
            "--project",
            str(PROJECT_CONFIG),
            "--state-root",
            str(tmp_path / "state"),
            "--worktree-root",
            str(tmp_path / "worktrees"),
            "--packet-root",
            str(tmp_path / "packets"),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "run-e2e-registry-seeded-smoke"
    assert payload["project_key"] == "astro-project"
    assert payload["result"] == payload["data"]
    assert payload["data"]["selected_packet_id"] == PACKET_CHILD_RUNNABLE
    assert payload["data"]["prefect_runs_created"] == 0
    assert payload["data"]["live_agents_started"] == 0
    assert payload["data"]["writes_outside_temp_roots"] == []
    assert payload["data"]["e2e_result"]["domain_status"] == "accepted"
    assert payload["data"]["e2e_result"]["registry_status"] == "accepted"
    assert payload["data"]["e2e_result"]["registry_reason"] == "execution_accepted"
    assert all(case["ok"] for case in payload["data"]["cases"])


def test_cli_run_e2e_registry_seeded_smoke_rejects_unsafe_state_root(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-e2e-registry-seeded-smoke",
            "--project",
            str(PROJECT_CONFIG),
            "--state-root",
            "/var/lib/grace-orchestrator/e2e-seeded-smoke",
            "--worktree-root",
            str(tmp_path / "worktrees"),
            "--packet-root",
            str(tmp_path / "packets"),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "run-e2e-registry-seeded-smoke"
    assert payload["result"] == payload["data"]
    assert payload["errors"][0]["code"] == "UNSAFE_STATE_ROOT"
