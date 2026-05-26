"""
Tests for prefect_native_submission module.

Verifies packet submission to Prefect with offline fake submitter.
"""

import tempfile
from pathlib import Path

import pytest

from prefect_grace.platform.prefect_native_submission import (
    PacketSubmissionRecord,
    NativeSubmissionResult,
    build_idempotency_key,
    submit_ready_packets_to_prefect,
)
from prefect_grace.platform.state_store import PacketRegistryStore


def _create_test_project(tmp_path):
    """Create minimal project adapter for testing."""
    class TestProject:
        def __init__(self, project_key, repo_root, runtime_state_root):
            self.project_key = project_key
            self.repo_root = repo_root
            self.runtime_state_root = runtime_state_root

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    runtime_state_root = tmp_path / "runtime_state"
    runtime_state_root.mkdir()

    return TestProject("test-project", str(repo_root), str(runtime_state_root))


def _create_test_packet_file(tmp_path, packet_id):
    """Create minimal packet file."""
    packet_file = tmp_path / "repo" / "packets" / f"{packet_id}.md"
    packet_file.parent.mkdir(parents=True, exist_ok=True)
    packet_file.write_text(f"""# Test Packet

- packet_id: {packet_id}
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for native submission.

## Allowed Write Scope
- src/**

## Frozen Scope
- backend/**

## Must Preserve
- Existing tests pass

## Verification
Run tests.

## Expected Evidence
- Test output

## Escalation Triggers
- Tests fail
""")
    return packet_file


def test_build_idempotency_key():
    """Verify idempotency key format."""
    key = build_idempotency_key("test-project", "TEST-W01-PACKET", 1, "abc123")
    assert key == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123"


def test_build_idempotency_key_zero_padded():
    """Verify attempt number is zero-padded."""
    key = build_idempotency_key("test-project", "TEST-W01-PACKET", 42, "abc123")
    assert key == "grace-packet:test-project:TEST-W01-PACKET:attempt-0042:abc123"


def test_submit_ready_packets_dry_run_returns_plan(tmp_path):
    """Verify dry run returns submission plan without calling submitter."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)

    # Create registry with ready packet
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-W01-PACKET",
        "project_key": "test-project",
        "feature_id": "TEST-FEATURE",
        "wave_id": "W01",
        "title": "Test Packet",
        "path": "packets/TEST-W01-PACKET.md",
        "source_hash": "abc123",
        "registry_status": "ready",
        "registry_reason": "test",
        "depends_on": [],
    })

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=True,
    )

    assert result.ok is True
    assert result.dry_run is True
    assert len(result.packets_planned) == 1
    assert result.packets_planned[0] == "TEST-W01-PACKET"
    assert len(result.packets_submitted) == 0
    assert len(result.records) == 1
    assert result.records[0].status == "dry_run"


def test_submit_ready_packets_execute_calls_submitter(tmp_path):
    """Verify execute mode calls submitter and updates registry."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)

    # Create packet file
    packet_file = _create_test_packet_file(tmp_path, "TEST-W01-PACKET")

    # Create registry with ready packet
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-W01-PACKET",
        "project_key": "test-project",
        "feature_id": "TEST-FEATURE",
        "wave_id": "W01",
        "title": "Test Packet",
        "path": str(packet_file.relative_to(tmp_path / "repo")),
        "source_hash": "abc123",
        "registry_status": "ready",
        "registry_reason": "test",
        "depends_on": [],
    })

    # Fake submitter
    submitted_calls = []

    def fake_submitter(**kwargs):
        submitted_calls.append(kwargs)
        return {
            "flow_run_id": "fake-flow-run-123",
            "flow_run_name": f"packet:{kwargs['parameters']['packet_id']}",
            "deployment_name": "prefect-grace-managed-packet-runner/live-managed-packet-runner",
            "work_queue_name": "default",
            "url": "http://prefect.local/flow-runs/fake-flow-run-123",
        }

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=False,
        submitter=fake_submitter,
    )

    assert result.ok is True
    assert result.dry_run is False
    assert len(result.packets_submitted) == 1
    assert result.packets_submitted[0] == "TEST-W01-PACKET"
    assert len(result.records) == 1
    assert result.records[0].status == "submitted"
    assert result.records[0].flow_run_id == "fake-flow-run-123"

    # Verify submitter was called
    assert len(submitted_calls) == 1
    call = submitted_calls[0]
    assert call["parameters"]["packet_id"] == "TEST-W01-PACKET"
    assert call["parameters"]["project_key"] == "test-project"
    assert call["idempotency_key"] == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123"

    # Verify registry was updated
    updated_packet = registry.load_packet("TEST-W01-PACKET")
    assert updated_packet["registry_status"] == "submitted"
    assert updated_packet["prefect_flow_run_id"] == "fake-flow-run-123"


def test_submit_ready_packets_no_submitter_fails(tmp_path):
    """Verify execute mode without submitter returns error."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)

    # Create packet file
    packet_file = _create_test_packet_file(tmp_path, "TEST-W01-PACKET")

    # Create registry with ready packet
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-W01-PACKET",
        "project_key": "test-project",
        "feature_id": "TEST-FEATURE",
        "wave_id": "W01",
        "title": "Test Packet",
        "path": str(packet_file.relative_to(tmp_path / "repo")),
        "source_hash": "abc123",
        "registry_status": "ready",
        "registry_reason": "test",
        "depends_on": [],
    })

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=False,
        submitter=None,
    )

    assert result.ok is False
    assert len(result.errors) == 1
    assert result.errors[0]["code"] == "NO_SUBMITTER_PROVIDED"


def test_submit_ready_packets_missing_source_hash_fails(tmp_path):
    """Verify packet without source_hash returns error."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)

    # Create registry with packet missing source_hash
    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": "TEST-W01-PACKET",
        "project_key": "test-project",
        "feature_id": "TEST-FEATURE",
        "wave_id": "W01",
        "title": "Test Packet",
        "path": "packets/TEST-W01-PACKET.md",
        "registry_status": "ready",
        "registry_reason": "test",
        "depends_on": [],
    })

    def fake_submitter(**kwargs):
        return {"flow_run_id": "fake-123"}

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=False,
        submitter=fake_submitter,
    )

    assert result.ok is False
    assert len(result.errors) == 1
    assert result.errors[0]["code"] == "MISSING_SOURCE_HASH"


def test_submit_ready_packets_limit_respected(tmp_path):
    """Verify limit parameter restricts submission count."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)

    # Create registry with 3 ready packets
    registry = PacketRegistryStore(state_root)
    for i in range(1, 4):
        packet_id = f"TEST-W01-PACKET-{i}"
        packet_file = _create_test_packet_file(tmp_path, packet_id)
        registry.upsert_packet({
            "packet_id": packet_id,
            "project_key": "test-project",
            "feature_id": "TEST-FEATURE",
            "wave_id": "W01",
            "title": f"Test Packet {i}",
            "path": str(packet_file.relative_to(tmp_path / "repo")),
            "source_hash": f"abc{i}",
            "registry_status": "ready",
            "registry_reason": "test",
            "depends_on": [],
        })

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=True,
        limit=2,
    )

    assert result.ok is True
    assert len(result.packets_planned) == 2


def test_submit_ready_packets_continue_on_error(tmp_path):
    """Verify continue_on_error allows processing remaining packets."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)

    # Create registry with 2 ready packets
    registry = PacketRegistryStore(state_root)
    for i in range(1, 3):
        packet_id = f"TEST-W01-PACKET-{i}"
        packet_file = _create_test_packet_file(tmp_path, packet_id)
        registry.upsert_packet({
            "packet_id": packet_id,
            "project_key": "test-project",
            "feature_id": "TEST-FEATURE",
            "wave_id": "W01",
            "title": f"Test Packet {i}",
            "path": str(packet_file.relative_to(tmp_path / "repo")),
            "source_hash": f"abc{i}",
            "registry_status": "ready",
            "registry_reason": "test",
            "depends_on": [],
        })

    # Fake submitter that fails on first packet
    call_count = [0]

    def fake_submitter(**kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("Simulated submission failure")
        return {
            "flow_run_id": f"fake-flow-run-{call_count[0]}",
            "flow_run_name": f"packet:{kwargs['parameters']['packet_id']}",
            "deployment_name": "prefect-grace-managed-packet-runner/live-managed-packet-runner",
            "work_queue_name": "default",
        }

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=False,
        submitter=fake_submitter,
        continue_on_error=True,
    )

    assert result.ok is False
    assert len(result.errors) == 1
    assert result.errors[0]["code"] == "SUBMISSION_FAILED"
    assert len(result.packets_submitted) == 1
    assert result.packets_submitted[0] == "TEST-W01-PACKET-2"


def test_submit_ready_packets_to_dict_serialization(tmp_path):
    """Verify NativeSubmissionResult.to_dict() works."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=True,
    )

    result_dict = result.to_dict()

    assert result_dict["ok"] is True
    assert result_dict["project_key"] == "test-project"
    assert result_dict["dry_run"] is True
    assert isinstance(result_dict["packets_planned"], list)
    assert isinstance(result_dict["packets_submitted"], list)
    assert isinstance(result_dict["records"], list)
    assert isinstance(result_dict["blocked_packets"], list)
    assert isinstance(result_dict["warnings"], list)
    assert isinstance(result_dict["errors"], list)


def test_packet_submission_record_to_dict():
    """Verify PacketSubmissionRecord.to_dict() works."""
    record = PacketSubmissionRecord(
        packet_id="TEST-W01-PACKET",
        feature_id="TEST-FEATURE",
        wave_id="W01",
        attempt=1,
        source_hash="abc123",
        idempotency_key="grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123",
        flow_run_id="fake-flow-run-123",
        flow_run_name="packet:TEST-W01-PACKET",
        deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
        work_queue_name="default",
        status="submitted",
        url="http://prefect.local/flow-runs/fake-flow-run-123",
    )

    record_dict = record.to_dict()

    assert record_dict["packet_id"] == "TEST-W01-PACKET"
    assert record_dict["feature_id"] == "TEST-FEATURE"
    assert record_dict["wave_id"] == "W01"
    assert record_dict["attempt"] == 1
    assert record_dict["source_hash"] == "abc123"
    assert record_dict["idempotency_key"] == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123"
    assert record_dict["flow_run_id"] == "fake-flow-run-123"
    assert record_dict["flow_run_name"] == "packet:TEST-W01-PACKET"
    assert record_dict["deployment_name"] == "prefect-grace-managed-packet-runner/live-managed-packet-runner"
    assert record_dict["work_queue_name"] == "default"
    assert record_dict["status"] == "submitted"
    assert record_dict["url"] == "http://prefect.local/flow-runs/fake-flow-run-123"
