"""
Rework tests for blocking issues identified in MVP-2 review.

These tests validate the fixes for:
1. Evidence markdown filtering
2. Dependency readiness logic
3. Cascading blocked status
4. Submit-packets registry path
5. Submission planning full registry validation
"""

import pytest
from pathlib import Path
from prefect_grace.platform.backlog_controller import BacklogController, update_dependent_packets
from prefect_grace.platform.state_store import PacketRegistryStore


class MockProjectAdapter:
    def __init__(self, repo_root, packets_dir, runtime_state_root):
        self.project_key = "test-project"
        self.repo_root = repo_root
        self.packets_dir = packets_dir
        self.runtime_state_root = runtime_state_root


def test_evidence_markdown_ignored(tmp_path):
    """
    Blocking Issue #1: Evidence markdown should be skipped, not treated as runnable packets.
    """
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    # Create a valid packet
    valid_packet = packets_dir / "P1.md"
    valid_packet.write_text("""# Execution Packet: P1

## Objective
Valid packet

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

    # Create evidence markdown (should be ignored)
    evidence_dir = packets_dir / "P1_evidence"
    evidence_dir.mkdir()
    evidence_file = evidence_dir / "review_notes.md"
    evidence_file.write_text("""# Review Notes

Some evidence without packet_id, feature_id, wave_id.
""")

    # Create another invalid markdown (missing required fields)
    invalid_packet = packets_dir / "incomplete.md"
    invalid_packet.write_text("""# Some Document

Just a document without packet metadata.
""")

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=False)

    # Should only find 1 valid packet, not 3
    assert result.packets_total == 1
    assert "P1" in result.ready
    assert len(result.warnings) >= 2  # Warnings for skipped files


def test_legacy_role_packet_skipped(tmp_path):
    """
    Regression test: Legacy role packets with IDs but missing strict sections should be skipped.
    """
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    # Create a strict controller packet (should be accepted)
    strict_packet = packets_dir / "STRICT.md"
    strict_packet.write_text("""# Execution Packet: STRICT

## Objective
Strict controller packet

## Slice
- packet_id: `STRICT-P1`
- feature_id: `FEAT-STRICT`
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

    # Create a legacy role packet (has IDs but missing strict sections)
    legacy_packet = packets_dir / "LEGACY.md"
    legacy_packet.write_text("""# Execution Packet: LEGACY

## Objective
Legacy role packet with IDs but no strict sections

## Slice
- packet_id: `LEGACY-P1`
- feature_id: `FEAT-LEGACY`
- wave_id: `W1`
- status: `ready`

## Implementation
Some implementation notes without strict controller sections.
""")

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=False)

    # Should only find 1 strict packet, legacy should be skipped
    assert result.packets_total == 1
    assert "STRICT-P1" in result.ready
    assert "LEGACY-P1" not in result.ready

    # Should have warning about legacy packet
    legacy_warnings = [w for w in result.warnings if "LEGACY.md" in w and "legacy packet" in w]
    assert len(legacy_warnings) == 1


def test_dependent_not_ready_until_dependency_accepted(tmp_path):
    """
    Blocking Issue #2: Dependent packet should not be ready until dependency is accepted.
    """
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

    # First sync: P1 should be ready, P2 should be waiting
    result = BacklogController.sync(project, dry_run=False)
    assert result.packets_total == 2
    assert "P1" in result.ready
    assert "P2" not in result.ready  # P2 should NOT be ready yet

    # Manually mark P1 as accepted
    registry = PacketRegistryStore(state_root / "state")
    p1_record = registry.load_packet("P1")
    registry.upsert_packet({**p1_record, "registry_status": "accepted"})

    # Second sync: Now P2 should become ready
    result2 = BacklogController.sync(project, dry_run=False)
    assert "P2" in result2.ready


def test_cascading_blocked_status(tmp_path):
    """
    Blocking Issue #3: Dependency-blocked packets should use cascading_blocked status.
    """
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
- depends_on: `P_MISSING`

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

    project = MockProjectAdapter(tmp_path, "packets", state_root)
    result = BacklogController.sync(project, dry_run=False)

    # P1 should be cascading_blocked due to missing dependency
    assert "P1" in result.cascading_blocked

    # Check registry status
    registry = PacketRegistryStore(state_root / "state")
    p1_record = registry.load_packet("P1")
    assert p1_record["registry_status"] == "cascading_blocked"
    assert "dependency_blocked" in p1_record.get("registry_reason", "")


def test_update_dependent_packets_helper(tmp_path):
    """
    Blocking Issue #3: Test update_dependent_packets helper function.
    """
    state_root = tmp_path / "state"
    registry = PacketRegistryStore(state_root)

    # Setup: P1 is dependency, P2 depends on P1
    p1 = {
        "packet_id": "P1",
        "feature_id": "F1",
        "wave_id": "W1",
        "depends_on": [],
        "registry_status": "ready",
    }
    p2 = {
        "packet_id": "P2",
        "feature_id": "F1",
        "wave_id": "W1",
        "depends_on": ["P1"],
        "registry_status": "ready",
    }

    registry.upsert_packet(p1)
    registry.upsert_packet(p2)

    all_packets = [p1, p2]

    # When P1 becomes blocked, P2 should become cascading_blocked
    updated = update_dependent_packets("P1", "blocked", registry, all_packets)
    assert "P2" in updated

    p2_record = registry.load_packet("P2")
    assert p2_record["registry_status"] == "cascading_blocked"

    # When P1 becomes accepted, P2 should become ready
    registry.upsert_packet({**p1, "registry_status": "accepted"})
    updated = update_dependent_packets("P1", "accepted", registry, all_packets)
    assert "P2" in updated

    p2_record = registry.load_packet("P2")
    assert p2_record["registry_status"] == "ready"


def test_submission_plan_validates_full_registry(tmp_path):
    """
    Blocking Issue #5: plan_submission should validate against full registry, not just ready packets.
    """
    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    # Create packets
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

    # Sync packets
    BacklogController.sync(project, dry_run=False)

    # Manually mark P1 as accepted
    registry = PacketRegistryStore(state_root / "state")
    p1_record = registry.load_packet("P1")
    registry.upsert_packet({**p1_record, "registry_status": "accepted"})

    # Sync again to update P2
    BacklogController.sync(project, dry_run=False)

    # Plan submission
    plan = BacklogController.plan_submission(project)

    # P2 should be in submission plan because P1 is accepted
    assert "P2" in plan.packets_to_submit
    assert "P2" in plan.submission_order


def test_submit_packets_fail_closed_without_safety_gates(tmp_path):
    """
    Blocking Issue #4: submit-packets --execute should fail closed until safety gates exist.

    This test validates the CLI behavior via direct function call.
    """
    import sys
    import argparse
    from io import StringIO
    from prefect_grace.cli import _cmd_submit_packets, _load_adapter_from_args

    packets_dir = tmp_path / "packets"
    packets_dir.mkdir()
    state_root = tmp_path / "state"

    # Create valid packet
    p1_file = packets_dir / "P1.md"
    p1_file.write_text("""# Execution Packet: P1

## Objective
Test packet

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

    # Create project config
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text(f"""
project:
  key: test-project
  root: {tmp_path}
  packets_dir: packets

runtime:
  state_root: {state_root}
""")

    # Test that --execute fails with safety error
    args = argparse.Namespace(
        project_config=str(project_yaml),
        execute=True,
        json=True,
    )

    with pytest.raises(SystemExit) as exc_info:
        _cmd_submit_packets(args)

    # Should exit with code 5 (security/scope violation)
    assert exc_info.value.code == 5
