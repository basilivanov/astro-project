"""Tests for create_bounded_prefect_status_reader."""

from __future__ import annotations

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

        state = None
        if state_data is not None:
            state = SimpleNamespace(data=state_data)

        return SimpleNamespace(
            state_type=state_type,
            state_name=state_name,
            state=state,
        )


def test_completed_run_with_accepted_passed_payload_returns_success():
    """Completed run with accepted/passed payload returns success."""
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
    result = reader(
        flow_run_id="flow-run-001",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is True
    assert result["domain_status"] == "accepted"
    assert result["scope_verdict"] == "passed"
    assert result["live_agents_started"] == 1
    assert result["changed_files"] == ["scratch/result.txt"]
    assert len(result["poll_events"]) >= 1


def test_completed_run_with_scope_blocked_payload_fails_closed():
    """Completed run with scope_blocked payload fails closed."""
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
    result = reader(
        flow_run_id="flow-run-002",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "scope_blocked"
    assert result["scope_verdict"] == "blocked"
    assert result["live_agents_started"] == 1
    assert result["changed_files"] == ["backend/forbidden.py"]
    assert any(e["code"] == "SCOPE_BLOCKED" for e in result.get("errors", []))


def test_completed_run_with_missing_payload_fails_closed():
    """Completed run with missing payload fails closed."""
    client = FakePrefectClient({
        "flow-run-003": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": None,  # Missing payload
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(
        flow_run_id="flow-run-003",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is False
    assert result["domain_status"] is None
    assert result["scope_verdict"] == "payload_missing"
    assert result["live_agents_started"] == 0
    assert any(e["code"] == "FLOW_RUN_PAYLOAD_MISSING" for e in result["errors"])


def test_completed_run_with_incomplete_evidence_fails_closed():
    """Completed run with incomplete evidence fails closed."""
    client = FakePrefectClient({
        "flow-run-004": {
            "state_type": "COMPLETED",
            "state_name": "Completed",
            "state_data": {
                "domain_status": "accepted",
                # Missing scope_verdict
                "live_agents_started": 1,
            },
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(
        flow_run_id="flow-run-004",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "accepted"
    assert result["scope_verdict"] == "evidence_incomplete"
    assert any(e["code"] == "FLOW_RUN_EVIDENCE_INCOMPLETE" for e in result["errors"])


def test_failed_terminal_state_fails_closed():
    """Failed terminal state fails closed."""
    client = FakePrefectClient({
        "flow-run-005": {
            "state_type": "FAILED",
            "state_name": "Failed",
            "state_data": None,
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(
        flow_run_id="flow-run-005",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "failed"
    assert result["scope_verdict"] == "flow_failed"
    assert result["live_agents_started"] == 0
    assert any(e["code"] == "FLOW_RUN_FAILED" for e in result["errors"])


def test_cancelled_terminal_state_fails_closed():
    """Cancelled terminal state fails closed."""
    client = FakePrefectClient({
        "flow-run-006": {
            "state_type": "CANCELLED",
            "state_name": "Cancelled",
            "state_data": None,
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(
        flow_run_id="flow-run-006",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "failed"
    assert result["scope_verdict"] == "flow_failed"
    assert any(e["code"] == "FLOW_RUN_FAILED" for e in result["errors"])


def test_crashed_terminal_state_fails_closed():
    """Crashed terminal state fails closed."""
    client = FakePrefectClient({
        "flow-run-007": {
            "state_type": "CRASHED",
            "state_name": "Crashed",
            "state_data": None,
        },
    })

    reader = create_bounded_prefect_status_reader(client)
    result = reader(
        flow_run_id="flow-run-007",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "failed"
    assert result["scope_verdict"] == "flow_failed"
    assert any(e["code"] == "FLOW_RUN_FAILED" for e in result["errors"])


def test_timeout_with_bounded_poll_events():
    """Timeout returns bounded poll events."""
    # Client that never returns terminal state
    class TimeoutClient:
        def __init__(self):
            self.call_count = 0

        def read_flow_run(self, flow_run_id: str):
            self.call_count += 1
            return SimpleNamespace(
                state_type="RUNNING",
                state_name="Running",
                state=None,
            )

    client = TimeoutClient()
    reader = create_bounded_prefect_status_reader(client)
    result = reader(
        flow_run_id="flow-run-timeout",
        packet_id="test-packet",
        timeout_seconds=1,  # Short timeout
    )

    assert result["ok"] is False
    assert result["domain_status"] == "timeout"
    assert result["scope_verdict"] == "pending_timeout"
    assert result["live_agents_started"] == 0
    assert len(result["poll_events"]) > 0  # Has some poll events
    assert len(result["poll_events"]) <= 100  # Bounded
    assert any(e["code"] == "WORKER_TIMEOUT" for e in result["errors"])


def test_flow_run_read_failure_fails_closed():
    """Flow run read failure fails closed."""
    class FailingClient:
        def read_flow_run(self, flow_run_id: str):
            raise Exception("Prefect API error")

    client = FailingClient()
    reader = create_bounded_prefect_status_reader(client)
    result = reader(
        flow_run_id="flow-run-error",
        packet_id="test-packet",
        timeout_seconds=30,
    )

    assert result["ok"] is False
    assert result["scope_verdict"] == "flow_run_read_failed"
    assert any(e["code"] == "FLOW_RUN_READ_FAILED" for e in result["errors"])
