from __future__ import annotations

import json
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


def test_grace_worker_requirements_include_importlib_metadata():
    """Worker image rebuild includes Prefect 3.6.25 Python 3.12 runtime dependency."""
    requirements = Path("infra/grace-worker/requirements.txt").read_text(encoding="utf-8")
    assert "importlib_metadata" in requirements


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
    key = result.submit_plan["records"][0]["idempotency_key"]
    assert ":namespace:single_live_prefect_packet_pilot-" in key


def test_different_temp_roots_produce_distinct_pilot_idempotency_keys(tmp_path):
    """Synthetic live-pilot proof runs avoid stale Prefect idempotency reuse."""
    state_root_a, worktree_root_a, packet_root_a = _roots(tmp_path / "run-a")
    state_root_b, worktree_root_b, packet_root_b = _roots(tmp_path / "run-b")

    result_a = run_single_live_prefect_packet_pilot(
        project_config=_project_config(),
        state_root=state_root_a,
        worktree_root=worktree_root_a,
        packet_root=packet_root_a,
        dry_run=True,
    )
    result_b = run_single_live_prefect_packet_pilot(
        project_config=_project_config(),
        state_root=state_root_b,
        worktree_root=worktree_root_b,
        packet_root=packet_root_b,
        dry_run=True,
    )

    key_a = result_a.submit_plan["records"][0]["idempotency_key"]
    key_b = result_b.submit_plan["records"][0]["idempotency_key"]

    assert result_a.ok is True
    assert result_b.ok is True
    assert key_a != key_b
    assert ":namespace:single_live_prefect_packet_pilot-" in key_a
    assert ":namespace:single_live_prefect_packet_pilot-" in key_b


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
        assert ":namespace:single_live_prefect_packet_pilot-" in kwargs["idempotency_key"]
        parameters = kwargs["parameters"]
        assert parameters["packet_id"] == PACKET_ID
        assert parameters["dry_run"] is False
        assert parameters["execute_agent"] is True
        assert parameters["runtime_state_root"] == str(state_root)
        payload_path = Path(parameters["managed_result_payload_path"])
        payload_root = Path(parameters["managed_result_payload_root"])
        assert payload_path.name == "result_payload.json"
        assert payload_path.is_relative_to(payload_root)
        assert payload_root.is_relative_to(state_root)
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


def test_missing_deployment_fails_closed_before_submission(tmp_path):
    """Missing deployment fails closed with zero flow runs and zero agents."""
    state_root, worktree_root, packet_root = _roots(tmp_path)
    submitter_calls = []

    def submitter(**kwargs):
        submitter_calls.append(kwargs)
        # Simulate deployment not found error from Prefect
        raise Exception("Deployment 'prefect-grace-managed-packet-runner/live-managed-packet-runner' not found")

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
    )

    assert result.ok is False
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert result.flow_run_id is None
    assert len(submitter_calls) == 1  # Submitter was called but failed
    assert any(error["code"] == "SUBMISSION_FAILED" for error in result.errors)


def test_worker_timeout_fails_closed_with_bounded_events(tmp_path):
    """Worker timeout fails closed with one submitted run, bounded poll events, and no writes outside scratch."""
    state_root, worktree_root, packet_root = _roots(tmp_path)
    submitter_calls = []
    status_reader_calls = []

    def submitter(**kwargs):
        submitter_calls.append(kwargs)
        return {
            "flow_run_id": "flow-run-timeout",
            "flow_run_name": "packet:SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-SCRATCH",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "grace-live",
            "url": "http://prefect.local/flow-runs/flow-run-timeout",
            "status": "submitted",
        }

    def status_reader(**kwargs):
        status_reader_calls.append(kwargs)
        assert kwargs["flow_run_id"] == "flow-run-timeout"
        # Simulate timeout with bounded poll events
        return {
            "ok": False,
            "domain_status": "timeout",
            "scope_verdict": "pending_timeout",
            "live_agents_started": 0,  # Worker never started or timed out before reporting
            "changed_files": [],
            "poll_events": [
                {"status": "scheduled", "timestamp": "2026-05-28T10:00:00Z"},
                {"status": "pending", "timestamp": "2026-05-28T10:00:05Z"},
                {"status": "running", "timestamp": "2026-05-28T10:00:10Z"},
            ],
            "errors": [{"code": "WORKER_TIMEOUT", "message": "Worker did not complete within timeout"}],
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
        timeout_seconds=30,
        submitter=submitter,
        status_reader=status_reader,
    )

    assert result.ok is False
    assert result.prefect_runs_created == 1
    assert result.flow_run_id == "flow-run-timeout"
    assert result.domain_status == "timeout"
    assert result.scope_verdict == "pending_timeout"
    assert result.changed_files == []
    assert result.writes_outside_temp_roots == []
    assert len(result.poll_events) == 3  # Bounded events
    assert len(submitter_calls) == 1
    assert len(status_reader_calls) == 1
    assert any(error["code"] == "WORKER_TIMEOUT" for error in result.errors)


# Tests for create_bounded_prefect_status_reader

from types import SimpleNamespace
from prefect_grace.platform.single_live_prefect_packet_pilot import create_bounded_prefect_status_reader


class FakePrefectClient:
    """Fake Prefect client for testing status reader."""

    def __init__(self, flow_runs: dict[str, dict]):
        """Initialize with flow run states."""
        self.flow_runs = flow_runs

    def read_flow_run(self, flow_run_id: str):
        """Return fake flow run."""
        run_data = self.flow_runs.get(flow_run_id, {})
        state_type = run_data.get("state_type", "PENDING")
        state_name = run_data.get("state_name", "Pending")
        state_data = run_data.get("state_data")
        parameters = run_data.get("parameters", {})

        state = None
        if state_data is not None:
            state = SimpleNamespace(data=state_data)

        return SimpleNamespace(
            state_type=state_type,
            state_name=state_name,
            state=state,
            parameters=parameters,
        )


def test_status_reader_completed_with_accepted_passed_returns_success():
    """Status reader: completed run with accepted/passed payload returns success."""
    client = FakePrefectClient({
        "flow-run-001": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": {
                "domain_status": "accepted",
                "scope_verdict": "passed",
                "live_agents_started": 1,
                "changed_files": ["scratch/result.txt"],
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-001", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is True
    assert result["domain_status"] == "accepted"
    assert result["scope_verdict"] == "passed"


def test_status_reader_completed_with_passed_passed_returns_success():
    """Status reader: completed run with passed/passed payload returns success."""
    client = FakePrefectClient({
        "flow-run-passed": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": {
                "domain_status": "passed",
                "scope_verdict": "passed",
                "live_agents_started": 1,
                "changed_files": ["scratch/result.txt"],
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-passed", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is True
    assert result["domain_status"] == "passed"
    assert result["scope_verdict"] == "passed"


def test_status_reader_completed_with_scope_blocked_fails_closed():
    """Status reader: completed run with scope_blocked payload fails closed."""
    client = FakePrefectClient({
        "flow-run-002": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": {
                "domain_status": "scope_blocked",
                "scope_verdict": "blocked",
                "live_agents_started": 1,
                "changed_files": ["backend/forbidden.py"],
                "errors": [{"code": "SCOPE_BLOCKED", "message": "backend write"}],
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-002", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is False
    assert result["domain_status"] == "scope_blocked"
    assert result["scope_verdict"] == "blocked"


def test_status_reader_completed_with_missing_payload_fails_closed():
    """Status reader: completed run with missing payload fails closed."""
    client = FakePrefectClient({
        "flow-run-003": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-003", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is False
    assert result["scope_verdict"] == "payload_missing"
    assert any(e["code"] == "MANAGED_RESULT_PAYLOAD_PATH_MISSING" for e in result["errors"])


def test_status_reader_falls_back_to_managed_result_payload_file(tmp_path):
    """Status reader: completed run with missing API payload reads bounded managed result file."""
    payload_root = tmp_path / "state" / "managed-runner-results"
    payload_path = payload_root / "TEST-PACKET" / "attempt-0001" / "result_payload.json"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_text(
        json.dumps(
            {
                "domain_status": "passed",
                "scope_verdict": "passed",
                "live_agents_started": 1,
                "changed_files": ["scratch/grace-single-live-prefect/result.txt"],
            }
        ),
        encoding="utf-8",
    )
    client = FakePrefectClient({
        "flow-run-fallback": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,
            "parameters": {
                "managed_result_payload_path": str(payload_path),
                "managed_result_payload_root": str(payload_root),
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-fallback", packet_id="TEST-PACKET", timeout_seconds=30)

    assert result["ok"] is True
    assert result["domain_status"] == "passed"
    assert result["scope_verdict"] == "passed"
    assert result["live_agents_started"] == 1
    assert result["changed_files"] == ["scratch/grace-single-live-prefect/result.txt"]


def test_status_reader_fallback_scope_blocked_fails_closed(tmp_path):
    """Status reader: fallback payload preserves scope_blocked fail-closed semantics."""
    payload_root = tmp_path / "state" / "managed-runner-results"
    payload_path = payload_root / "TEST-PACKET" / "attempt-0001" / "result_payload.json"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_text(
        json.dumps(
            {
                "domain_status": "scope_blocked",
                "scope_verdict": "blocked",
                "live_agents_started": 1,
                "changed_files": ["backend/forbidden.py"],
                "errors": [{"code": "SCOPE_BLOCKED", "message": "backend write"}],
            }
        ),
        encoding="utf-8",
    )
    client = FakePrefectClient({
        "flow-run-scope-blocked-fallback": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,
            "parameters": {
                "managed_result_payload_path": str(payload_path),
                "managed_result_payload_root": str(payload_root),
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-scope-blocked-fallback", packet_id="TEST-PACKET", timeout_seconds=30)

    assert result["ok"] is False
    assert result["domain_status"] == "scope_blocked"
    assert result["scope_verdict"] == "blocked"
    assert any(e["code"] == "SCOPE_BLOCKED" for e in result["errors"])


def test_status_reader_fallback_outside_root_fails_closed(tmp_path):
    """Status reader: fallback payload path outside declared root fails closed."""
    payload_root = tmp_path / "state" / "managed-runner-results"
    outside_path = tmp_path / "outside" / "result_payload.json"
    client = FakePrefectClient({
        "flow-run-outside-root": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,
            "parameters": {
                "managed_result_payload_path": str(outside_path),
                "managed_result_payload_root": str(payload_root),
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-outside-root", packet_id="TEST-PACKET", timeout_seconds=30)

    assert result["ok"] is False
    assert result["scope_verdict"] == "payload_read_failed"
    assert any(e["code"] == "MANAGED_RESULT_PAYLOAD_READ_FAILED" for e in result["errors"])


def test_status_reader_fallback_missing_file_fails_closed(tmp_path):
    """Status reader: fallback path with no payload file fails closed."""
    payload_root = tmp_path / "state" / "managed-runner-results"
    payload_path = payload_root / "TEST-PACKET" / "attempt-0001" / "result_payload.json"
    client = FakePrefectClient({
        "flow-run-missing-file": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,
            "parameters": {
                "managed_result_payload_path": str(payload_path),
                "managed_result_payload_root": str(payload_root),
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-missing-file", packet_id="TEST-PACKET", timeout_seconds=30)

    assert result["ok"] is False
    assert result["scope_verdict"] == "payload_missing"
    assert any(e["code"] == "MANAGED_RESULT_PAYLOAD_FILE_MISSING" for e in result["errors"])


def test_status_reader_fallback_malformed_json_fails_closed(tmp_path):
    """Status reader: unreadable fallback JSON fails closed."""
    payload_root = tmp_path / "state" / "managed-runner-results"
    payload_path = payload_root / "TEST-PACKET" / "attempt-0001" / "result_payload.json"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_text("{not-json", encoding="utf-8")
    client = FakePrefectClient({
        "flow-run-malformed-fallback": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,
            "parameters": {
                "managed_result_payload_path": str(payload_path),
                "managed_result_payload_root": str(payload_root),
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-malformed-fallback", packet_id="TEST-PACKET", timeout_seconds=30)

    assert result["ok"] is False
    assert result["scope_verdict"] == "payload_read_failed"
    assert any(e["code"] == "MANAGED_RESULT_PAYLOAD_READ_FAILED" for e in result["errors"])


def test_status_reader_fallback_incomplete_payload_fails_closed(tmp_path):
    """Status reader: fallback payload missing scope evidence fails closed."""
    payload_root = tmp_path / "state" / "managed-runner-results"
    payload_path = payload_root / "TEST-PACKET" / "attempt-0001" / "result_payload.json"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_text(json.dumps({"domain_status": "passed"}), encoding="utf-8")
    client = FakePrefectClient({
        "flow-run-incomplete-fallback": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,
            "parameters": {
                "managed_result_payload_path": str(payload_path),
                "managed_result_payload_root": str(payload_root),
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-incomplete-fallback", packet_id="TEST-PACKET", timeout_seconds=30)

    assert result["ok"] is False
    assert result["scope_verdict"] == "evidence_incomplete"
    assert any(e["code"] == "FLOW_RUN_EVIDENCE_INCOMPLETE" for e in result["errors"])


def test_status_reader_completed_with_incomplete_evidence_fails_closed():
    """Status reader: completed run with incomplete evidence fails closed."""
    client = FakePrefectClient({
        "flow-run-004": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": {"domain_status": "accepted"},
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-004", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is False
    assert result["scope_verdict"] == "evidence_incomplete"


def test_status_reader_failed_terminal_state_fails_closed():
    """Status reader: failed terminal state fails closed."""
    client = FakePrefectClient({
        "flow-run-005": {
            "state_type": "FAILED",
            "state_name": "Failed",
            "state_data": None,
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-005", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is False
    assert result["domain_status"] == "failed"


def test_status_reader_cancelled_terminal_state_fails_closed():
    """Status reader: cancelled terminal state fails closed."""
    client = FakePrefectClient({
        "flow-run-006": {
            "state_type": "CANCELLED",
            "state_name": "Cancelled",
            "state_data": None,
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-006", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is False


def test_status_reader_crashed_terminal_state_fails_closed():
    """Status reader: crashed terminal state fails closed."""
    client = FakePrefectClient({
        "flow-run-007": {
            "state_type": "CRASHED",
            "state_name": "Crashed",
            "state_data": None,
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-007", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is False


def test_status_reader_timeout_with_bounded_poll_events():
    """Status reader: timeout returns bounded poll events."""
    class TimeoutClient:
        def __init__(self):
            self.call_count = 0

        def read_flow_run(self, flow_run_id: str):
            self.call_count += 1
            return SimpleNamespace(state_type="RUNNING", state_name="Running", state=None)

    client = TimeoutClient()
    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-timeout", packet_id="test-packet", timeout_seconds=1)

    assert result["ok"] is False
    assert result["domain_status"] == "timeout"
    assert len(result["poll_events"]) > 0
    assert len(result["poll_events"]) <= 100


def test_status_reader_flow_run_read_failure_fails_closed():
    """Status reader: flow run read failure fails closed."""
    class FailingClient:
        def read_flow_run(self, flow_run_id: str):
            raise Exception("Prefect API error")

    client = FailingClient()
    reader = create_bounded_prefect_status_reader(client)
    result = reader(flow_run_id="flow-run-error", packet_id="test-packet", timeout_seconds=30)

    assert result["ok"] is False
    assert result["scope_verdict"] == "flow_run_read_failed"
