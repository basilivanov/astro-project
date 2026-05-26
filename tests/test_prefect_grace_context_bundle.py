import pytest
from pathlib import Path
from prefect_grace.platform.context_bundle import build_context_bundle


def test_build_context_bundle_empty_dir(tmp_path):
    packet_dir = tmp_path / "nonexistent"

    bundle = build_context_bundle(packet_dir)

    assert bundle == []


def test_build_context_bundle_coder_normal_mode(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    # Create source packet and summary
    (packet_dir / "EXECUTION_PACKET.md").write_text("Source contract")
    (packet_dir / "SUMMARY.md").write_text("Current state")

    # Create artifacts
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("Review 1")
    (reviews_dir / "review-0002.md").write_text("Review 2")

    evidence_dir = packet_dir / "EVIDENCE"
    evidence_dir.mkdir()
    attempt1 = evidence_dir / "attempt-0001"
    attempt1.mkdir()
    (attempt1 / "evidence_manifest.json").write_text('{"test": 1}')

    rework_dir = packet_dir / "REWORK"
    rework_dir.mkdir()
    (rework_dir / "attempt-0001.md").write_text("Rework 1")
    (rework_dir / "attempt-0002.md").write_text("Rework 2")

    bundle = build_context_bundle(packet_dir, role="coder", mode="normal")

    # Coder normal mode: source, summary, latest review, latest rework, latest evidence
    assert packet_dir / "EXECUTION_PACKET.md" in bundle
    assert packet_dir / "SUMMARY.md" in bundle
    assert reviews_dir / "review-0002.md" in bundle
    assert rework_dir / "attempt-0002.md" in bundle
    assert attempt1 / "evidence_manifest.json" in bundle

    # Should NOT include old reviews/rework
    assert reviews_dir / "review-0001.md" not in bundle
    assert rework_dir / "attempt-0001.md" not in bundle


def test_build_context_bundle_reviewer_normal_mode(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    # Create source packet and summary
    (packet_dir / "EXECUTION_PACKET.md").write_text("Source contract")
    (packet_dir / "SUMMARY.md").write_text("Current state")

    # Create evidence
    evidence_dir = packet_dir / "EVIDENCE"
    evidence_dir.mkdir()
    attempt1 = evidence_dir / "attempt-0001"
    attempt1.mkdir()
    (attempt1 / "evidence_manifest.json").write_text('{"test": 1}')

    bundle = build_context_bundle(packet_dir, role="reviewer", mode="normal")

    # Reviewer normal mode: source, summary, latest evidence
    assert packet_dir / "EXECUTION_PACKET.md" in bundle
    assert packet_dir / "SUMMARY.md" in bundle
    assert attempt1 / "evidence_manifest.json" in bundle


def test_build_context_bundle_architect_normal_mode(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    # Create source packet and summary
    (packet_dir / "EXECUTION_PACKET.md").write_text("Source contract")
    (packet_dir / "SUMMARY.md").write_text("Current state")

    # Create review and rework
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("Review 1")

    rework_dir = packet_dir / "REWORK"
    rework_dir.mkdir()
    (rework_dir / "attempt-0001.md").write_text("Rework 1")

    bundle = build_context_bundle(packet_dir, role="architect", mode="normal")

    # Architect normal mode: source, summary, latest review, latest rework
    assert packet_dir / "EXECUTION_PACKET.md" in bundle
    assert packet_dir / "SUMMARY.md" in bundle
    assert reviews_dir / "review-0001.md" in bundle
    assert rework_dir / "attempt-0001.md" in bundle


def test_build_context_bundle_audit_mode(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    # Create source packet and summary
    (packet_dir / "EXECUTION_PACKET.md").write_text("Source contract")
    (packet_dir / "SUMMARY.md").write_text("Current state")

    # Create multiple artifacts
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("Review 1")
    (reviews_dir / "review-0002.md").write_text("Review 2")

    evidence_dir = packet_dir / "EVIDENCE"
    evidence_dir.mkdir()
    attempt1 = evidence_dir / "attempt-0001"
    attempt1.mkdir()
    (attempt1 / "evidence_manifest.json").write_text('{"test": 1}')
    attempt2 = evidence_dir / "attempt-0002"
    attempt2.mkdir()
    (attempt2 / "evidence_manifest.json").write_text('{"test": 2}')

    rework_dir = packet_dir / "REWORK"
    rework_dir.mkdir()
    (rework_dir / "attempt-0001.md").write_text("Rework 1")
    (rework_dir / "attempt-0002.md").write_text("Rework 2")

    bundle = build_context_bundle(packet_dir, role="coder", mode="audit")

    # Audit mode: includes ALL history
    assert packet_dir / "EXECUTION_PACKET.md" in bundle
    assert packet_dir / "SUMMARY.md" in bundle
    assert reviews_dir / "review-0001.md" in bundle
    assert reviews_dir / "review-0002.md" in bundle
    assert attempt1 / "evidence_manifest.json" in bundle
    assert attempt2 / "evidence_manifest.json" in bundle
    assert rework_dir / "attempt-0001.md" in bundle
    assert rework_dir / "attempt-0002.md" in bundle


def test_context_bundle_minimal_for_normal_mode(tmp_path):
    """
    Critical test: Verify context bundle is minimal in normal mode (not full history)
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    (packet_dir / "EXECUTION_PACKET.md").write_text("Source")
    (packet_dir / "SUMMARY.md").write_text("Summary")

    # Create 10 old reviews
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    for i in range(1, 11):
        (reviews_dir / f"review-{i:04d}.md").write_text(f"Review {i}")

    bundle = build_context_bundle(packet_dir, role="coder", mode="normal")

    # Should only include latest review, not all 10
    review_files = [f for f in bundle if "review-" in str(f)]
    assert len(review_files) == 1
    assert reviews_dir / "review-0010.md" in bundle
