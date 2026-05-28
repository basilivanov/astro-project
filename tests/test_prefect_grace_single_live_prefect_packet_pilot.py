from __future__ import annotations

from pathlib import Path

from prefect_grace.platform.single_live_prefect_packet_pilot import (
    MANAGED_PACKET_DEPLOYMENT_NAME,
    PACKET_ID,
    run_single_live_prefect_packet_pilot,
)


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    return (
        tmp_path / "state",
        tmp_path / "worktrees",
        tmp_path / "packet-root",
    )


def _project_config() -> Path:
    return Path("prefect_grace/project.yaml")


def test_dry_run_plans_one_managed_scratch_packet(tmp_path):
    """Dry-run plans one managed scratch packet and creates zero Prefect runs."""
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_single_live_prefect_packet_pilot(
        project_config=_project_config(),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
    )

    assert result.ok is True
    assert result.dry_run is True
    assert result.selected_packet_id == PACKET_ID
    assert result.deployment_name == MANAGED_PACKET_DEPLOYMENT_NAME
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert result.writes_outside_temp_roots == []
    assert result.errors == []


def test_missing_opt_in_blocks_before_prefect_submission(tmp_path):
    """Live mode fails closed before calling Prefect submitter when gates are missing."""
    state_root, worktree_root, packet_root = _roots(tmp_path)
    submitter_calls = []

    def submitter(**kwargs):
        submitter_calls.append(kwargs)
        raise AssertionError("submitter must not be called without opt-in gates")

    result = run_single_live_prefect_packet_pilot(
        project_config=_project_config(),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=False,
        opt_in_token=None,
        submitter=submitter,
    )

    assert result.ok is False
    assert result.opt_in_confirmed is False
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert submitter_calls == []
    assert any(error["code"] == "LIVE_PREFECT_ACK_REQUIRED" for error in result.errors)
    assert any(error["code"] == "LIVE_PREFECT_TOKEN_REQUIRED" for error in result.errors)


def test_injected_live_path_creates_one_prefect_run_and_agent(tmp_path):
    """Injected live path proves one managed Prefect run and one agent launch."""
    state_root, worktree_root, packet_root = _roots(tmp_path)
    submitter_calls = []
    status_reader_calls = []

    def submitter(**kwargs):
        submitter_calls.append(kwargs)
        parameters = kwargs["parameters"]
        assert parameters["packet_id"] == PACKET_ID
        assert parameters["dry_run"] is False
        assert parameters["execute_agent"] is True
        return {
            "flow_run_id": "flow-run-001",
            "flow_run_name": "packet:SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-SCRATCH",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "grace-live",
            "url": "http://prefect.local/flow-runs/flow-run-001",
            "status": "submitted",
        }

    def status_reader(**kwargs):
        status_reader_calls.append(kwargs)
        assert kwargs["flow_run_id"] == "flow-run-001"
        return {
            "ok": True,
            "domain_status": "accepted",
            "scope_verdict": "passed",
            "live_agents_started": 1,
            "changed_files": ["scratch/grace-single-live-prefect/result.txt"],
            "poll_events": [{"status": "completed"}],
        }

    result = run_single_live_prefect_packet_pilot(
        project_config=_project_config(),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-live-prefect",
        submitter=submitter,
        status_reader=status_reader,
    )

    assert result.ok is True
    assert result.selected_packet_id == PACKET_ID
    assert result.flow_run_id == "flow-run-001"
    assert result.prefect_runs_created == 1
    assert result.live_agents_started == 1
    assert result.domain_status == "accepted"
    assert result.scope_verdict == "passed"
    assert result.changed_files == ["scratch/grace-single-live-prefect/result.txt"]
    assert result.writes_outside_temp_roots == []
    assert len(submitter_calls) == 1
    assert len(status_reader_calls) == 1


def test_scope_blocked_fails_closed(tmp_path):
    """Injected scope violation blocks the pilot even after one Prefect run."""
    state_root, worktree_root, packet_root = _roots(tmp_path)

    def submitter(**kwargs):
        return {
            "flow_run_id": "flow-run-002",
            "flow_run_name": "packet:SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-SCRATCH",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "grace-live",
            "url": "http://prefect.local/flow-runs/flow-run-002",
            "status": "submitted",
        }

    def status_reader(**kwargs):
        return {
            "ok": False,
            "domain_status": "scope_blocked",
            "scope_verdict": "blocked",
            "live_agents_started": 1,
            "changed_files": ["backend/forbidden.py"],
            "errors": [{"code": "SCOPE_BLOCKED", "message": "backend write"}],
        }

    result = run_single_live_prefect_packet_pilot(
        project_config=_project_config(),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-live-prefect",
        submitter=submitter,
        status_reader=status_reader,
    )

    assert result.ok is False
    assert result.prefect_runs_created == 1
    assert result.live_agents_started == 1
    assert result.domain_status == "scope_blocked"
    assert any(error["code"] == "SCOPE_BLOCKED" for error in result.errors)
    assert any(error["code"] == "LIVE_PREFECT_CHANGED_FILES_OUTSIDE_SCRATCH" for error in result.errors)


def test_multiple_ready_packets_fail_closed(tmp_path):
    """Pilot rejects plans that contain more than one runnable scratch packet."""
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_single_live_prefect_packet_pilot(
        project_config=_project_config(),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
        extra_ready_packet=True,
    )

    assert result.ok is False
    assert result.selected_packet_id is None
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert any(error["code"] == "LIVE_PREFECT_PACKET_COUNT_INVALID" for error in result.errors)
