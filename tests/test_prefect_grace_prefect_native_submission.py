"""
Tests for prefect_native_submission module.

Verifies packet submission to Prefect with offline fake submitter.
"""

from pathlib import Path

from prefect_grace.platform.prefect_native_submission import (
    PacketSubmissionRecord,
    NativeSubmissionResult,
    build_idempotency_key,
    submit_ready_packets_to_prefect,
)
from prefect_grace.platform.state_store import PacketRegistryStore
from prefect_grace.tasks.prefect_submitter import (
    E2E_PACKET_DEPLOYMENT_NAME,
    MANAGED_PACKET_DEPLOYMENT_NAME,
    build_e2e_packet_submission_request,
    e2e_packet_flow_parameters,
    e2e_packet_flow_run_name,
)


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


def test_build_idempotency_key_optional_namespace_preserves_default():
    """Verify optional namespace only changes key when explicitly provided."""
    default_key = build_idempotency_key("test-project", "TEST-W01-PACKET", 1, "abc123")
    namespaced_key = build_idempotency_key(
        "test-project",
        "TEST-W01-PACKET",
        1,
        "abc123",
        idempotency_namespace="proof-run-001",
    )

    assert default_key == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123"
    assert namespaced_key == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123:namespace:proof-run-001"


def test_e2e_packet_submitter_helpers_build_flow_request():
    """Verify E2E submitter helpers target the E2E deployment and tags."""
    params = e2e_packet_flow_parameters(
        project_root="/repo",
        packet_path="/repo/packets/TEST-W01-PACKET.md",
        state_root="/state",
        worktree_root="/worktrees",
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        timeout_seconds=3600,
        keep_worktree=True,
    )
    request = build_e2e_packet_submission_request(
        parameters=params,
        scheduled_for="2026-05-26T12:00:00Z",
        tags=["feature:TEST-FEATURE", "wave:W01"],
        idempotency_key="grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123",
    )

    assert e2e_packet_flow_run_name("TEST-W01-PACKET", 1) == "e2e-packet:TEST-W01-PACKET:attempt-1"
    assert params["packet_path"] == "/repo/packets/TEST-W01-PACKET.md"
    assert "packet_file" not in params
    assert request["deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME
    assert request["flow_run_name"] == "e2e-packet:TEST-W01-PACKET:attempt-1"
    assert request["idempotency_key"] == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123"
    assert "grace" in request["tags"]
    assert "packet" in request["tags"]
    assert "e2e" in request["tags"]
    assert "packet:TEST-W01-PACKET" in request["tags"]
    assert "feature:TEST-FEATURE" in request["tags"]
    assert "wave:W01" in request["tags"]


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
    assert result.records[0].runner_kind == "e2e"
    assert result.records[0].deployment_name == E2E_PACKET_DEPLOYMENT_NAME
    assert result.records[0].flow_run_name == "e2e-packet:TEST-W01-PACKET:attempt-1:Test Packet"
    assert result.records[0].idempotency_key == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123"


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
            "flow_run_name": f"e2e-packet:{kwargs['parameters']['packet_id']}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "runner_kind": "e2e",
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
    assert result.records[0].runner_kind == "e2e"
    assert result.records[0].deployment_name == E2E_PACKET_DEPLOYMENT_NAME

    # Verify submitter was called
    assert len(submitted_calls) == 1
    call = submitted_calls[0]
    assert call["parameters"]["packet_id"] == "TEST-W01-PACKET"
    assert call["parameters"]["project_key"] == "test-project"
    assert call["parameters"]["project_root"] == str(tmp_path / "repo")
    assert call["parameters"]["packet_path"] == str(packet_file)
    assert call["parameters"]["state_root"] == str(Path(project.runtime_state_root))
    assert call["parameters"]["worktree_root"] == str(Path(project.runtime_state_root) / "worktrees")
    assert call["parameters"]["dry_run"] is True
    assert call["parameters"]["execute_agent"] is False
    assert "e2e" in call["tags"]
    assert "managed-runner" not in call["tags"]
    assert call["idempotency_key"] == "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123"

    # Verify registry was updated
    updated_packet = registry.load_packet("TEST-W01-PACKET")
    assert updated_packet["registry_status"] == "submitted"
    assert updated_packet["registry_reason"] == "prefect_e2e_flow_run_submitted"
    assert updated_packet["prefect_flow_run_id"] == "fake-flow-run-123"
    assert updated_packet["prefect_deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME
    assert updated_packet["submission_runner_kind"] == "e2e"


def test_submit_ready_packets_managed_runner_explicit_compatibility(tmp_path):
    """Verify managed runner remains available only as an explicit runner kind."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    packet_file = _create_test_packet_file(tmp_path, "TEST-W01-PACKET")

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

    submitted_calls = []

    def fake_submitter(**kwargs):
        submitted_calls.append(kwargs)
        return {
            "flow_run_id": "fake-flow-run-managed",
            "flow_run_name": f"packet:{kwargs['parameters']['packet_id']}",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "default",
        }

    result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=False,
        submitter=fake_submitter,
        runner_kind="managed",
    )

    assert result.ok is True
    assert result.records[0].runner_kind == "managed"
    assert result.records[0].deployment_name == MANAGED_PACKET_DEPLOYMENT_NAME
    call = submitted_calls[0]
    assert "packet_file" in call["parameters"]
    assert "packet_path" not in call["parameters"]
    assert call["parameters"]["runtime_state_root"] == str(Path(project.runtime_state_root))
    payload_path = Path(call["parameters"]["managed_result_payload_path"])
    payload_root = Path(call["parameters"]["managed_result_payload_root"])
    assert payload_path.name == "result_payload.json"
    assert payload_path.is_relative_to(payload_root)
    assert payload_root.is_relative_to(Path(project.runtime_state_root))
    assert "managed-runner" in call["tags"]
    assert "e2e" not in call["tags"]
    updated_packet = registry.load_packet("TEST-W01-PACKET")
    assert updated_packet["registry_reason"] == "prefect_flow_run_submitted"
    assert updated_packet["submission_runner_kind"] == "managed"


def test_submit_ready_packets_idempotency_namespace_applies_to_plan_and_submit(tmp_path):
    """Verify proof-run namespace is reflected in dry-run records and live submission call."""
    project = _create_test_project(tmp_path)
    state_root = Path(project.runtime_state_root) / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    packet_file = _create_test_packet_file(tmp_path, "TEST-W01-PACKET")
    registry = PacketRegistryStore(state_root)
    packet_record = {
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
    }
    registry.upsert_packet(packet_record)

    dry_result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=True,
        runner_kind="managed",
        idempotency_namespace="proof-run-001",
    )

    expected = "grace-packet:test-project:TEST-W01-PACKET:attempt-0001:abc123:namespace:proof-run-001"
    assert dry_result.records[0].idempotency_key == expected

    submitted_calls = []

    def fake_submitter(**kwargs):
        submitted_calls.append(kwargs)
        return {
            "flow_run_id": "fake-flow-run-managed",
            "flow_run_name": f"packet:{kwargs['parameters']['packet_id']}",
            "deployment_name": MANAGED_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "default",
        }

    live_result = submit_ready_packets_to_prefect(
        project=project,
        dry_run=False,
        submitter=fake_submitter,
        runner_kind="managed",
        idempotency_namespace="proof-run-001",
    )

    assert live_result.records[0].idempotency_key == expected
    assert submitted_calls[0]["idempotency_key"] == expected


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
            "flow_run_name": f"e2e-packet:{kwargs['parameters']['packet_id']}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
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
        deployment_name=E2E_PACKET_DEPLOYMENT_NAME,
        work_queue_name="default",
        status="submitted",
        runner_kind="e2e",
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
    assert record_dict["deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME
    assert record_dict["work_queue_name"] == "default"
    assert record_dict["status"] == "submitted"
    assert record_dict["runner_kind"] == "e2e"
    assert record_dict["url"] == "http://prefect.local/flow-runs/fake-flow-run-123"
