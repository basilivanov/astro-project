import json
import subprocess
import sys
from pathlib import Path

from prefect_grace.platform.registry_apply_smoke import run_registry_apply_smoke


PROJECT_CONFIG = Path(__file__).resolve().parents[1] / "prefect_grace" / "project.yaml"


def test_registry_apply_smoke_runs_isolated_temp_state(tmp_path: Path) -> None:
    state_root = tmp_path / "state"

    result = run_registry_apply_smoke(
        project_config=PROJECT_CONFIG,
        state_root=state_root,
    )

    assert result.ok is True
    assert result.state_root == str(state_root)
    assert result.dry_run is False
    assert result.bootstrap_apply_count == 7
    assert result.prefect_runs_created == 0
    assert result.writes_outside_state_root == []
    assert all(case.ok for case in result.cases)
    assert {case.name for case in result.cases} >= {
        "accepted_parent_seeded",
        "accepted_parent_not_submitted",
        "dependent_ready_runnable",
        "missing_dependency_waits",
        "blocked_dependency_waits",
        "source_status_accepted_without_evidence_not_accepted",
        "command_status_passed_not_accepted",
        "sync_dry_run_no_registry_write",
        "submit_dry_run_no_prefect_runs",
        "submit_execute_fail_closed",
    }

    submit_plan = result.submit_plan
    assert submit_plan["dry_run"] is True
    assert submit_plan["packets_submitted"] == []
    assert "SMOKE-PARENT-ACCEPTED-W01-PACKET" not in submit_plan["packets_planned"]
    assert "SMOKE-DEPENDENT-READY-W01-PACKET" in submit_plan["packets_planned"]
    assert submit_plan["execute_fail_closed"]["ok"] is True
    assert submit_plan["execute_fail_closed"]["packets_submitted"] == []


def test_registry_apply_smoke_rejects_unsafe_state_root() -> None:
    result = run_registry_apply_smoke(
        project_config=PROJECT_CONFIG,
        state_root=Path("/var/lib/grace-orchestrator/unsafe-smoke"),
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "UNSAFE_STATE_ROOT"
    assert result.bootstrap_apply_count == 0


def test_registry_apply_smoke_rejects_packet_root_outside_state(tmp_path: Path) -> None:
    result = run_registry_apply_smoke(
        project_config=PROJECT_CONFIG,
        state_root=tmp_path / "state",
        packet_root=tmp_path / "outside-packets",
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "UNSAFE_PACKET_ROOT"


def test_registry_apply_smoke_cli_json_envelope(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "registry-apply-smoke",
            "--project",
            str(PROJECT_CONFIG),
            "--state-root",
            str(tmp_path / "state"),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "registry-apply-smoke"
    assert payload["project_key"] == "astro-project"
    assert payload["result"] == payload["data"]
    assert payload["data"]["prefect_runs_created"] == 0
    assert payload["data"]["writes_outside_state_root"] == []
    assert all(case["ok"] for case in payload["data"]["cases"])


def test_registry_apply_smoke_cli_rejects_unsafe_state_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "registry-apply-smoke",
            "--project",
            str(PROJECT_CONFIG),
            "--state-root",
            "/var/lib/grace-orchestrator/unsafe-smoke",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["command"] == "registry-apply-smoke"
    assert payload["result"] == payload["data"]
    assert payload["errors"][0]["code"] == "UNSAFE_STATE_ROOT"
