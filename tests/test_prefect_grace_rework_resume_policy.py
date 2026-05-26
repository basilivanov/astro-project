import pytest
from pathlib import Path
from prefect_grace.platform.rework_resume_policy import (
    ReworkResumeDecision,
    decide_rework_resume,
)


def test_missing_last_executed_hash_blocks_resume(tmp_path):
    """
    Rule 1: Missing last executed hash -> no resume, bounded_fresh
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")
    (packet_dir / "SUMMARY.md").write_text("# Summary")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:abc123",
        last_executed_source_hash=None,
        requested_rework_mode="light_resume",
        rework_reason="reviewer_feedback",
        packet_dir=packet_dir,
    )

    assert decision.resume_allowed is False
    assert decision.resume_block_reason == "missing_last_executed_hash"
    assert decision.recommended_rework_mode == "bounded_fresh"
    assert decision.context_mode == "bounded_fresh"
    assert len(decision.context_paths) >= 2  # At least source + summary


def test_changed_source_hash_blocks_resume(tmp_path):
    """
    Rule 2: Source hash changed -> contract changed -> no resume
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")
    (packet_dir / "SUMMARY.md").write_text("# Summary")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:new_hash",
        last_executed_source_hash="sha256:old_hash",
        requested_rework_mode="light_resume",
        rework_reason="reviewer_feedback",
        packet_dir=packet_dir,
    )

    assert decision.resume_allowed is False
    assert decision.resume_block_reason == "contract_changed"
    assert decision.recommended_rework_mode == "bounded_fresh"
    assert decision.context_mode == "bounded_fresh"
    assert decision.current_source_hash == "sha256:new_hash"
    assert decision.last_executed_source_hash == "sha256:old_hash"


def test_same_hash_reviewer_feedback_allows_resume(tmp_path):
    """
    Rule 3: Same hash + light_resume + reviewer feedback + session exists -> allow resume
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:same",
        last_executed_source_hash="sha256:same",
        requested_rework_mode="light_resume",
        rework_reason="reviewer_feedback",
        packet_dir=packet_dir,
        latest_coder_session_id="session-123",
    )

    assert decision.resume_allowed is True
    assert decision.resume_block_reason is None
    assert decision.recommended_rework_mode == "light_resume"
    assert decision.context_mode == "normal_latest"
    assert decision.context_paths == []  # Resume uses existing session


def test_same_hash_implementation_fix_allows_resume(tmp_path):
    """
    Rule 3: Same hash + light_resume + implementation_fix + session exists -> allow resume
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:same",
        last_executed_source_hash="sha256:same",
        requested_rework_mode="light_resume",
        rework_reason="implementation_fix",
        packet_dir=packet_dir,
        latest_coder_session_id="session-456",
    )

    assert decision.resume_allowed is True
    assert decision.resume_block_reason is None
    assert decision.recommended_rework_mode == "light_resume"


def test_same_hash_missing_session_blocks_resume(tmp_path):
    """
    Rule 3: Same hash + light_resume + reviewer feedback but NO session -> block resume
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")
    (packet_dir / "SUMMARY.md").write_text("# Summary")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:same",
        last_executed_source_hash="sha256:same",
        requested_rework_mode="light_resume",
        rework_reason="reviewer_feedback",
        packet_dir=packet_dir,
        latest_coder_session_id=None,
    )

    assert decision.resume_allowed is False
    assert decision.resume_block_reason == "missing_session"
    assert decision.recommended_rework_mode == "bounded_fresh"


def test_same_hash_non_reviewer_reason_blocks_resume(tmp_path):
    """
    Rule 4: Same hash but not reviewer reason -> bounded_fresh
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")
    (packet_dir / "SUMMARY.md").write_text("# Summary")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:same",
        last_executed_source_hash="sha256:same",
        requested_rework_mode="light_resume",
        rework_reason="contract_changed",
        packet_dir=packet_dir,
        latest_coder_session_id="session-789",
    )

    assert decision.resume_allowed is False
    assert decision.resume_block_reason == "decision_required"
    assert decision.recommended_rework_mode == "bounded_fresh"


def test_same_hash_bounded_fresh_requested(tmp_path):
    """
    Rule 4: Same hash but bounded_fresh explicitly requested
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")
    (packet_dir / "SUMMARY.md").write_text("# Summary")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:same",
        last_executed_source_hash="sha256:same",
        requested_rework_mode="bounded_fresh",
        rework_reason="reviewer_feedback",
        packet_dir=packet_dir,
        latest_coder_session_id=None,
    )

    assert decision.resume_allowed is False
    assert decision.recommended_rework_mode == "bounded_fresh"
    assert decision.context_mode == "bounded_fresh"


def test_context_paths_include_latest_artifacts(tmp_path):
    """
    Verify context paths include latest artifacts when resume blocked
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")
    (packet_dir / "SUMMARY.md").write_text("# Summary")

    # Create artifacts
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("Review 1")

    rework_dir = packet_dir / "REWORK"
    rework_dir.mkdir()
    (rework_dir / "attempt-0001.md").write_text("Rework 1")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:new",
        last_executed_source_hash="sha256:old",
        requested_rework_mode="light_resume",
        rework_reason="reviewer_feedback",
        packet_dir=packet_dir,
    )

    assert decision.resume_allowed is False
    assert len(decision.context_paths) >= 2
    # Should include source packet and summary at minimum
    assert any("EXECUTION_PACKET.md" in p for p in decision.context_paths)
    assert any("SUMMARY.md" in p for p in decision.context_paths)


def test_decision_model_fields(tmp_path):
    """
    Verify ReworkResumeDecision has all required fields
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    (packet_dir / "EXECUTION_PACKET.md").write_text("# Source contract")

    decision = decide_rework_resume(
        packet_id="TEST-P1",
        current_source_hash="sha256:abc",
        last_executed_source_hash="sha256:def",
        requested_rework_mode="light_resume",
        rework_reason="reviewer_feedback",
        packet_dir=packet_dir,
    )

    # Verify all required fields exist
    assert hasattr(decision, "packet_id")
    assert hasattr(decision, "current_source_hash")
    assert hasattr(decision, "last_executed_source_hash")
    assert hasattr(decision, "resume_allowed")
    assert hasattr(decision, "resume_block_reason")
    assert hasattr(decision, "recommended_rework_mode")
    assert hasattr(decision, "context_mode")
    assert hasattr(decision, "context_paths")
