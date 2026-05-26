import pytest
from pathlib import Path
from prefect_grace.platform.state_store import PacketRegistryStore


def test_upsert_packet_preserves_resume_state(tmp_path):
    """
    Verify upsert_packet preserves existing resume state fields.
    """
    store = PacketRegistryStore(tmp_path / "state")

    # Initial packet with resume state
    store.upsert_packet({
        "packet_id": "TEST-P1",
        "status": "ready",
        "source_hash": "sha256:abc123",
        "last_executed_source_hash": "sha256:old123",
        "resume_allowed": False,
    })

    # Update status without touching resume state
    store.upsert_packet({
        "packet_id": "TEST-P1",
        "status": "in_progress",
    })

    packet = store.load_packet("TEST-P1")
    assert packet["status"] == "in_progress"
    assert packet["source_hash"] == "sha256:abc123"
    assert packet["last_executed_source_hash"] == "sha256:old123"
    assert packet["resume_allowed"] is False


def test_update_resume_state_new_fields(tmp_path):
    """
    Verify update_resume_state adds resume tracking fields.
    """
    store = PacketRegistryStore(tmp_path / "state")

    # Create packet without resume state
    store.upsert_packet({
        "packet_id": "TEST-P1",
        "status": "ready",
    })

    # Update resume state
    store.update_resume_state(
        packet_id="TEST-P1",
        source_hash="sha256:abc123",
        last_executed_source_hash="sha256:old123",
        latest_coder_session_id="session-456",
        resume_allowed=False,
        resume_block_reason="contract_changed",
        recommended_rework_mode="bounded_fresh",
    )

    packet = store.load_packet("TEST-P1")
    assert packet["source_hash"] == "sha256:abc123"
    assert packet["last_executed_source_hash"] == "sha256:old123"
    assert packet["latest_coder_session_id"] == "session-456"
    assert packet["resume_allowed"] is False
    assert packet["resume_block_reason"] == "contract_changed"
    assert packet["recommended_rework_mode"] == "bounded_fresh"


def test_update_resume_state_partial_update(tmp_path):
    """
    Verify update_resume_state can update individual fields.
    """
    store = PacketRegistryStore(tmp_path / "state")

    store.upsert_packet({
        "packet_id": "TEST-P1",
        "status": "ready",
        "source_hash": "sha256:abc123",
        "resume_allowed": False,
    })

    # Update only session_id
    store.update_resume_state(
        packet_id="TEST-P1",
        latest_coder_session_id="session-789",
    )

    packet = store.load_packet("TEST-P1")
    assert packet["source_hash"] == "sha256:abc123"
    assert packet["resume_allowed"] is False
    assert packet["latest_coder_session_id"] == "session-789"


def test_update_resume_state_missing_packet(tmp_path):
    """
    Verify update_resume_state raises error for missing packet.
    """
    store = PacketRegistryStore(tmp_path / "state")

    with pytest.raises(ValueError, match="not found in registry"):
        store.update_resume_state(
            packet_id="MISSING-P1",
            source_hash="sha256:abc123",
        )


def test_update_resume_state_after_execution(tmp_path):
    """
    Verify update_resume_state tracks execution state changes.
    """
    store = PacketRegistryStore(tmp_path / "state")

    # Initial packet
    store.upsert_packet({
        "packet_id": "TEST-P1",
        "status": "ready",
        "source_hash": "sha256:abc123",
    })

    # After first execution
    store.update_resume_state(
        packet_id="TEST-P1",
        last_executed_source_hash="sha256:abc123",
        latest_coder_session_id="session-001",
    )

    packet = store.load_packet("TEST-P1")
    assert packet["last_executed_source_hash"] == "sha256:abc123"
    assert packet["latest_coder_session_id"] == "session-001"

    # After contract change
    store.update_resume_state(
        packet_id="TEST-P1",
        source_hash="sha256:new456",
        resume_allowed=False,
        resume_block_reason="contract_changed",
    )

    packet = store.load_packet("TEST-P1")
    assert packet["source_hash"] == "sha256:new456"
    assert packet["last_executed_source_hash"] == "sha256:abc123"
    assert packet["resume_allowed"] is False
    assert packet["resume_block_reason"] == "contract_changed"


def test_backward_compatibility_no_resume_fields(tmp_path):
    """
    Verify registry works with packets that don't have resume fields.
    """
    store = PacketRegistryStore(tmp_path / "state")

    # Old-style packet without resume fields
    store.upsert_packet({
        "packet_id": "TEST-P1",
        "status": "ready",
        "feature_id": "FEAT-001",
    })

    packet = store.load_packet("TEST-P1")
    assert packet["packet_id"] == "TEST-P1"
    assert packet["status"] == "ready"
    assert "source_hash" not in packet
    assert "resume_allowed" not in packet
