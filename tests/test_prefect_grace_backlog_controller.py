import pytest
import tempfile
from pathlib import Path
from prefect_grace.platform.backlog_controller import BacklogController, BacklogSyncResult, BacklogSubmissionPlan
from prefect_grace.platform.project_adapter import ProjectAdapterConfig


class MockProjectAdapter:
    def __init__(self, repo_root, packets_dir, runtime_state_root):
        self.project_key = "test-project"
        self.repo_root = repo_root
        self.packets_dir = packets_dir
        self.runtime_state_root = runtime_state_root


def test_sync_empty_packets_dir(tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=True)

    assert result.project_key == "test-project"
    assert result.packets_total == 0
    assert result.registry_updates == 0


def test_sync_single_packet(tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    packet_file = packets_dir / "P1.md"
    packet_file.write_text("""# Execution Packet: Test Packet

## Objective
Test objective

## Slice
- packet_id: `P1`
- feature_id: `F1`
- wave_id: `W1`
- status: `ready`

## Allowed Write Scope
- file.py

## Frozen Scope
- other.py

## Must Preserve
- invariant

## Verification
pytest

## Expected Evidence
- test results

## Escalation Triggers
- scope violation
""")

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=False)

    assert result.packets_total == 1
    assert "P1" in result.ready
    assert result.registry_updates == 1


def test_sync_dry_run_no_updates(tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    packet_file = packets_dir / "P1.md"
    packet_file.write_text("""# Execution Packet: Test Packet

## Objective
Test objective

## Slice
- packet_id: `P1`
- feature_id: `F1`
- wave_id: `W1`
- status: `ready`

## Allowed Write Scope
- file.py

## Frozen Scope
- other.py

## Must Preserve
- invariant

## Verification
pytest

## Expected Evidence
- test results

## Escalation Triggers
- scope violation
""")

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=True)

    assert result.packets_total == 1
    assert "P1" in result.ready
    assert result.registry_updates == 0


def test_sync_with_dependencies(tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    p1_file = packets_dir / "P1.md"
    p1_file.write_text("""# Execution Packet: P1

## Objective
Base packet

## Slice
- packet_id: `P1`
- feature_id: `F1`
- wave_id: `W1`
- status: `ready`

## Allowed Write Scope
- file1.py

## Frozen Scope
- other.py

## Must Preserve
- invariant

## Verification
pytest

## Expected Evidence
- test results

## Escalation Triggers
- scope violation
""")

    p2_file = packets_dir / "P2.md"
    p2_file.write_text("""# Execution Packet: P2

## Objective
Dependent packet

## Slice
- packet_id: `P2`
- feature_id: `F1`
- wave_id: `W1`
- status: `ready`
- depends_on: `P1`

## Allowed Write Scope
- file2.py

## Frozen Scope
- other.py

## Must Preserve
- invariant

## Verification
pytest

## Expected Evidence
- test results

## Escalation Triggers
- scope violation
""")

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=False)

    assert result.packets_total == 2
    assert "P1" in result.ready
    # FIXED: P2 should NOT be ready until P1 is accepted
    # This was the wrong contract identified in review
    assert "P2" not in result.ready

    # Now mark P1 as accepted and sync again
    from prefect_grace.platform.state_store import PacketRegistryStore
    registry = PacketRegistryStore(state_root / "state")
    p1_record = registry.load_packet("P1")
    registry.upsert_packet({**p1_record, "registry_status": "accepted"})

    # Second sync: P2 should now become ready
    result2 = BacklogController.sync(project, dry_run=False)
    assert "P2" in result2.ready


def test_sync_with_missing_dependency(tmp_path):
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    packet_file = packets_dir / "P1.md"
    packet_file.write_text("""# Execution Packet: P1

## Objective
Test packet

## Slice
- packet_id: `P1`
- feature_id: `F1`
- wave_id: `W1`
- status: `ready`
- depends_on: `P_MISSING`

## Allowed Write Scope
- file.py

## Frozen Scope
- other.py

## Must Preserve
- invariant

## Verification
pytest

## Expected Evidence
- test results

## Escalation Triggers
- scope violation
""")

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=False)

    assert result.packets_total == 1
    assert "P1" in result.cascading_blocked
    assert len(result.warnings) > 0


def test_plan_submission_empty_registry(tmp_path):
    state_root = tmp_path / "state"
    project = MockProjectAdapter(tmp_path, "packets", state_root)

    plan = BacklogController.plan_submission(project)

    assert plan.project_key == "test-project"
    assert plan.packets_to_submit == []
    assert plan.submission_order == []


def test_sync_result_structure():
    result = BacklogSyncResult(project_key="test", packets_total=5)
    assert result.project_key == "test"
    assert result.packets_total == 5
    assert result.registry_updates == 0
    assert result.ready == []
    assert result.accepted == []
    assert result.blocked == []


def test_submission_plan_structure():
    plan = BacklogSubmissionPlan(project_key="test")
    assert plan.project_key == "test"
    assert plan.packets_to_submit == []
    assert plan.submission_order == []
    assert plan.blocked_packets == []
