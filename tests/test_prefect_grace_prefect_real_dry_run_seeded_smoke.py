"""Tests for registry-seeded real Prefect dry-run smoke."""

from pathlib import Path

from prefect_grace.platform.prefect_real_dry_run_seeded_smoke import (
    PACKET_CHILD_RUNNABLE,
    PACKET_COMMAND_PASSED,
    PACKET_PARENT_ACCEPTED,
    PACKET_SOURCE_STATUS_ONLY,
    run_prefect_real_dry_run_seeded_smoke,
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


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    return tmp_path / "state", tmp_path / "worktrees", tmp_path / "packets"


def _fake_submitter(calls: list[dict]):
    def submitter(**kwargs):
        calls.append(kwargs)
        packet_id = kwargs["parameters"]["packet_id"]
        return {
            "flow_run_id": "flow-run-seeded-smoke",
            "flow_run_name": f"e2e-packet:{packet_id}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
            "url": "http://prefect.local/flow-runs/flow-run-seeded-smoke",
        }
    return submitter


def _case(result, name: str) -> dict:
    return next(case for case in result.cases if case["name"] == name)


def test_prefect_real_dry_run_seeded_smoke_no_wait_submits_only_runnable_child(tmp_path):
    state_root, worktree_root, packet_root = _roots(tmp_path)
    calls: list[dict] = []

    result = run_prefect_real_dry_run_seeded_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        wait=False,
        submitter=_fake_submitter(calls),
        status_reader=lambda flow_run_id: {"error": "status reader must not be called"},
    )

    assert result.ok is True
    assert result.selected_packet_id == PACKET_CHILD_RUNNABLE
    assert result.submitted is True
    assert result.waited is False
    assert result.prefect_runs_created == 1
    assert result.live_agents_started == 0
    assert result.writes_outside_temp_roots == []
    assert calls[0]["parameters"]["packet_id"] == PACKET_CHILD_RUNNABLE
    assert calls[0]["parameters"]["dry_run"] is True
    assert calls[0]["parameters"]["execute_agent"] is False
    assert result.submit_plan["packets_to_submit"] == [PACKET_CHILD_RUNNABLE]
    assert _case(result, "bounded_parent_seeded_accepted")["packet_id"] == PACKET_PARENT_ACCEPTED
    assert _case(result, "missing_dependency_unsubmitted")["ok"] is True
    assert _case(result, "blocked_dependency_unsubmitted")["ok"] is True
    assert _case(result, "source_status_only_not_accepted")["packet_id"] == PACKET_SOURCE_STATUS_ONLY
    assert _case(result, "command_status_passed_not_accepted")["packet_id"] == PACKET_COMMAND_PASSED


def test_prefect_real_dry_run_seeded_smoke_waits_for_completed_accepted_state(tmp_path):
    state_root, worktree_root, packet_root = _roots(tmp_path)
    result = run_prefect_real_dry_run_seeded_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        submitter=_fake_submitter([]),
        status_reader=lambda flow_run_id: {
            "prefect_state_type": "completed",
            "prefect_state_name": "Completed",
            "domain_status": "accepted",
            "artifact_ids": ["artifact-1"],
        },
        sleep_fn=lambda seconds: None,
    )

    assert result.ok is True
    assert result.waited is True
    assert result.prefect_state_type == "completed"
    assert result.domain_status == "accepted"
    assert result.artifact_ids == ["artifact-1"]


def test_prefect_real_dry_run_seeded_smoke_times_out_with_seeded_error(tmp_path):
    state_root, worktree_root, packet_root = _roots(tmp_path)
    result = run_prefect_real_dry_run_seeded_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        timeout_seconds=0,
        poll_interval_seconds=0,
        submitter=_fake_submitter([]),
        status_reader=lambda flow_run_id: {
            "prefect_state_type": "running",
            "prefect_state_name": "Running",
            "domain_status": "unknown",
            "artifact_ids": [],
        },
        sleep_fn=lambda seconds: None,
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "PREFECT_SEEDED_DRY_RUN_TIMEOUT"


def test_prefect_real_dry_run_seeded_smoke_rejects_unexpected_deployment(tmp_path):
    state_root, worktree_root, packet_root = _roots(tmp_path)

    def bad_submitter(**kwargs):
        return {
            "flow_run_id": "flow-run-seeded-smoke",
            "flow_run_name": "wrong",
            "deployment_name": "wrong/deployment",
            "work_queue_name": "test-live",
        }

    result = run_prefect_real_dry_run_seeded_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        wait=False,
        submitter=bad_submitter,
    )

    assert result.ok is False
    assert any(error["code"] == "PREFECT_SEEDED_UNEXPECTED_DEPLOYMENT" for error in result.errors)


def test_prefect_real_dry_run_seeded_smoke_rejects_execute_agent_before_submission(tmp_path):
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)
    result = run_prefect_real_dry_run_seeded_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        submitter=lambda **kwargs: calls.append(kwargs) or {},
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "PREFECT_SEEDED_DRY_RUN_EXECUTE_AGENT_REJECTED"
    assert calls == []


def test_prefect_real_dry_run_seeded_smoke_rejects_unsafe_roots(tmp_path):
    result = run_prefect_real_dry_run_seeded_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=Path("/var/lib/grace-orchestrator/seeded-smoke"),
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        submitter=_fake_submitter([]),
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "UNSAFE_STATE_ROOT"
