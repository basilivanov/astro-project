import pytest
from pathlib import Path
from prefect_grace.platform.backlog_controller import BacklogController
from prefect_grace.platform.state_store import PacketRegistryStore


class MockProjectAdapter:
    def __init__(self, repo_root, packets_dir, runtime_state_root):
        self.project_key = "test-project"
        self.repo_root = repo_root
        self.packets_dir = packets_dir
        self.runtime_state_root = runtime_state_root


def test_sync_updates_resume_state_on_hash_change(tmp_path):
    """
    Verify sync updates resume state when source hash changes after acceptance.
    """
    repo_root = tmp_path / "repo"
    packets_dir = repo_root / "packets"
    packets_dir.mkdir(parents=True)
    state_root = tmp_path / "state"

    # Create packet with initial hash
    packet_content_v1 = """# Execution Packet: Test Implementation

## Objective
Test objective

## Slice
- packet_id: `TEST-P1-W01-IMPL`
- feature_id: `TEST-P1`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- src/

## Frozen Scope
- tests/

## Must Preserve
- existing tests

## Verification
pytest

## Expected Evidence
- tests passed

## Escalation Triggers
- scope violation

# Implementation
Test content v1
"""
    (packets_dir / "TEST-P1.md").write_text(packet_content_v1)

    adapter = MockProjectAdapter(
        repo_root=str(repo_root),
        packets_dir="packets",
        runtime_state_root=str(state_root),
    )

    # First sync: packet is new, should be ready
    result1 = BacklogController.sync(adapter, dry_run=False)
    assert len(result1.ready) == 1
    assert "TEST-P1-W01-IMPL" in result1.ready

    registry = PacketRegistryStore(state_root / "state")
    packet1 = registry.load_packet("TEST-P1-W01-IMPL")
    assert packet1["registry_status"] == "ready"
    initial_hash = packet1["source_hash"]

    # Simulate acceptance
    registry.upsert_packet({
        **packet1,
        "registry_status": "accepted",
        "last_executed_source_hash": initial_hash,
    })

    # Change packet content (new hash)
    packet_content_v2 = """# Execution Packet: Test Implementation

## Objective
Test objective CHANGED

## Slice
- packet_id: `TEST-P1-W01-IMPL`
- feature_id: `TEST-P1`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- src/

## Frozen Scope
- tests/

## Must Preserve
- existing tests

## Verification
pytest

## Expected Evidence
- tests passed

## Escalation Triggers
- scope violation

# Implementation
Test content v2 - CHANGED
"""
    (packets_dir / "TEST-P1.md").write_text(packet_content_v2)

    # Second sync: hash changed, should detect and update resume state
    result2 = BacklogController.sync(adapter, dry_run=False)
    assert len(result2.changed_after_acceptance) == 1
    assert "TEST-P1-W01-IMPL" in result2.changed_after_acceptance

    packet2 = registry.load_packet("TEST-P1-W01-IMPL")
    assert packet2["registry_status"] == "changed_after_acceptance"
    assert packet2["source_hash"] != initial_hash
    assert packet2["resume_allowed"] is False
    assert packet2["resume_block_reason"] == "contract_changed"
    assert packet2["recommended_rework_mode"] == "bounded_fresh"


def test_sync_updates_resume_state_on_blocked_retry(tmp_path):
    """
    Verify sync updates resume state when blocked packet hash changes.
    """
    repo_root = tmp_path / "repo"
    packets_dir = repo_root / "packets"
    packets_dir.mkdir(parents=True)
    state_root = tmp_path / "state"

    packet_content_v1 = """# Execution Packet: Test Implementation

## Objective
Test objective

## Slice
- packet_id: `TEST-P2-W01-IMPL`
- feature_id: `TEST-P2`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- src/

## Frozen Scope
- tests/

## Must Preserve
- existing tests

## Verification
pytest

## Expected Evidence
- tests passed

## Escalation Triggers
- scope violation

# Implementation
Test content v1
"""
    (packets_dir / "TEST-P2.md").write_text(packet_content_v1)

    adapter = MockProjectAdapter(
        repo_root=str(repo_root),
        packets_dir="packets",
        runtime_state_root=str(state_root),
    )

    # First sync
    result1 = BacklogController.sync(adapter, dry_run=False)
    assert len(result1.ready) == 1

    registry = PacketRegistryStore(state_root / "state")
    packet1 = registry.load_packet("TEST-P2-W01-IMPL")
    initial_hash = packet1["source_hash"]

    # Simulate blocked status
    registry.upsert_packet({
        **packet1,
        "registry_status": "blocked",
        "last_executed_source_hash": initial_hash,
    })

    # Change packet content
    packet_content_v2 = """# Execution Packet: Test Implementation

## Objective
Test objective CHANGED

## Slice
- packet_id: `TEST-P2-W01-IMPL`
- feature_id: `TEST-P2`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- src/

## Frozen Scope
- tests/

## Must Preserve
- existing tests

## Verification
pytest

## Expected Evidence
- tests passed

## Escalation Triggers
- scope violation

# Implementation
Test content v2 - CHANGED
"""
    (packets_dir / "TEST-P2.md").write_text(packet_content_v2)

    # Second sync: hash changed, should mark ready_for_retry and update resume state
    result2 = BacklogController.sync(adapter, dry_run=False)
    assert len(result2.ready_for_retry) == 1
    assert "TEST-P2-W01-IMPL" in result2.ready_for_retry

    packet2 = registry.load_packet("TEST-P2-W01-IMPL")
    assert packet2["registry_status"] == "ready_for_retry"
    assert packet2["source_hash"] != initial_hash
    assert packet2["resume_allowed"] is False
    assert packet2["resume_block_reason"] == "contract_changed"
    assert packet2["recommended_rework_mode"] == "bounded_fresh"


def test_sync_preserves_resume_state_when_hash_unchanged(tmp_path):
    """
    Verify sync preserves resume state when source hash is unchanged.
    """
    repo_root = tmp_path / "repo"
    packets_dir = repo_root / "packets"
    packets_dir.mkdir(parents=True)
    state_root = tmp_path / "state"

    packet_content = """# Execution Packet: Test Implementation

## Objective
Test objective

## Slice
- packet_id: `TEST-P3-W01-IMPL`
- feature_id: `TEST-P3`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- src/

## Frozen Scope
- tests/

## Must Preserve
- existing tests

## Verification
pytest

## Expected Evidence
- tests passed

## Escalation Triggers
- scope violation

# Implementation
Test content
"""
    (packets_dir / "TEST-P3.md").write_text(packet_content)

    adapter = MockProjectAdapter(
        repo_root=str(repo_root),
        packets_dir="packets",
        runtime_state_root=str(state_root),
    )

    # First sync
    result1 = BacklogController.sync(adapter, dry_run=False)
    assert len(result1.ready) == 1

    registry = PacketRegistryStore(state_root / "state")
    packet1 = registry.load_packet("TEST-P3-W01-IMPL")
    initial_hash = packet1["source_hash"]

    # Simulate accepted with resume state
    registry.upsert_packet({
        **packet1,
        "registry_status": "accepted",
        "last_executed_source_hash": initial_hash,
    })
    registry.update_resume_state(
        packet_id="TEST-P3-W01-IMPL",
        resume_allowed=True,
        latest_coder_session_id="session-123",
    )

    # Second sync: no changes, should preserve resume state
    result2 = BacklogController.sync(adapter, dry_run=False)
    assert len(result2.accepted) == 1
    assert "TEST-P3-W01-IMPL" in result2.accepted

    packet2 = registry.load_packet("TEST-P3-W01-IMPL")
    assert packet2["registry_status"] == "accepted"
    assert packet2["source_hash"] == initial_hash
    assert packet2["resume_allowed"] is True
    assert packet2["latest_coder_session_id"] == "session-123"
