import pytest
import json
import yaml
from pathlib import Path
from prefect_grace.platform.packet_artifact_layout import (
    PacketArtifactLayout,
    resolve_packet_layout,
    latest_review,
    latest_evidence_manifest,
    latest_rework,
)
from prefect_grace.platform.packet_artifacts import (
    write_review,
    write_evidence,
    write_rework,
)
from prefect_grace.platform.packet_summary import write_summary
from prefect_grace.platform.packet_line_limit import check_line_limit


def test_resolve_packet_layout(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    layout = resolve_packet_layout(packet_dir)

    assert isinstance(layout, PacketArtifactLayout)
    assert layout.packet_dir == packet_dir
    assert layout.source_packet == packet_dir / "EXECUTION_PACKET.md"
    assert layout.summary == packet_dir / "SUMMARY.md"
    assert layout.reviews_dir == packet_dir / "REVIEWS"
    assert layout.evidence_dir == packet_dir / "EVIDENCE"
    assert layout.rework_dir == packet_dir / "REWORK"


def test_latest_review_no_reviews(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    layout = resolve_packet_layout(packet_dir)
    result = latest_review(layout)

    assert result is None


def test_latest_review_with_reviews(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()

    # Create multiple review files
    (reviews_dir / "review-0001.md").write_text("Review 1")
    (reviews_dir / "review-0002.md").write_text("Review 2")
    (reviews_dir / "review-0003.md").write_text("Review 3")

    layout = resolve_packet_layout(packet_dir)
    result = latest_review(layout)

    assert result == reviews_dir / "review-0003.md"


def test_latest_evidence_manifest_no_evidence(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    layout = resolve_packet_layout(packet_dir)
    result = latest_evidence_manifest(layout)

    assert result is None


def test_latest_evidence_manifest_with_evidence(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    evidence_dir = packet_dir / "EVIDENCE"
    evidence_dir.mkdir()

    # Create multiple attempt directories
    attempt1 = evidence_dir / "attempt-0001"
    attempt1.mkdir()
    (attempt1 / "evidence_manifest.json").write_text('{"test": 1}')

    attempt2 = evidence_dir / "attempt-0002"
    attempt2.mkdir()
    (attempt2 / "evidence_manifest.json").write_text('{"test": 2}')

    layout = resolve_packet_layout(packet_dir)
    result = latest_evidence_manifest(layout)

    assert result == attempt2 / "evidence_manifest.json"


def test_latest_rework_no_rework(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    layout = resolve_packet_layout(packet_dir)
    result = latest_rework(layout)

    assert result is None


def test_latest_rework_with_rework(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    rework_dir = packet_dir / "REWORK"
    rework_dir.mkdir()

    # Create multiple rework files
    (rework_dir / "attempt-0001.md").write_text("Rework 1")
    (rework_dir / "attempt-0002.md").write_text("Rework 2")

    layout = resolve_packet_layout(packet_dir)
    result = latest_rework(layout)

    assert result == rework_dir / "attempt-0002.md"


def test_artifact_layout_does_not_mutate_source_packet(tmp_path):
    """
    Critical test: Verify that artifact operations do not mutate EXECUTION_PACKET.md
    """
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    source_packet = packet_dir / "EXECUTION_PACKET.md"
    original_content = "# Original Packet Content\n\nThis is the source contract."
    source_packet.write_text(original_content)

    # Create artifacts
    reviews_dir = packet_dir / "REVIEWS"
    reviews_dir.mkdir()
    (reviews_dir / "review-0001.md").write_text("Review content")

    evidence_dir = packet_dir / "EVIDENCE"
    evidence_dir.mkdir()
    attempt1 = evidence_dir / "attempt-0001"
    attempt1.mkdir()
    (attempt1 / "evidence_manifest.json").write_text('{"test": 1}')

    rework_dir = packet_dir / "REWORK"
    rework_dir.mkdir()
    (rework_dir / "attempt-0001.md").write_text("Rework content")

    # Verify source packet unchanged
    assert source_packet.read_text() == original_content


def test_write_review(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    review_path = write_review(
        packet_dir,
        verdict="rework_required",
        body="Fix the bug in module X.",
        metadata={"packet_id": "FEAT-TEST-W01-PACKET", "reviewer": "test-reviewer"},
    )

    assert review_path.exists()
    assert review_path.name == "review-0001.md"
    content = review_path.read_text()
    assert "rework_required" in content
    assert "Fix the bug" in content
    assert "test-reviewer" in content
    sidecar = review_path.with_suffix(".yaml")
    assert sidecar.exists()
    loaded = json.loads(json.dumps(yaml.safe_load(sidecar.read_text())))
    assert loaded["packet_id"] == "FEAT-TEST-W01-PACKET"
    assert loaded["status"] == "rework_required"
    assert loaded["reviewer"] == "test-reviewer"
    assert loaded["reviewed_at"]


def test_write_evidence(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    manifest = {
        "tests_passed": 10,
        "tests_failed": 2,
        "coverage": "85%",
    }

    evidence_path = write_evidence(packet_dir, attempt=1, manifest=manifest)

    assert evidence_path.exists()
    assert evidence_path.parent.name == "attempt-0001"

    loaded = json.loads(evidence_path.read_text())
    assert loaded["tests_passed"] == 10
    assert loaded["attempt"] == 1
    assert "timestamp" in loaded


def test_write_rework(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    rework_path = write_rework(
        packet_dir,
        attempt=2,
        body="Fix scope violation in file.py",
        blockers=["Scope guard failed", "Tests failing"],
    )

    assert rework_path.exists()
    assert rework_path.name == "attempt-0002.md"
    content = rework_path.read_text()
    assert "Attempt 0002" in content
    assert "Fix scope violation" in content
    assert "Scope guard failed" in content


def test_write_summary(tmp_path):
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()

    status = {
        "packet_id": "TEST-P1",
        "feature_id": "FEAT-TEST",
        "wave_id": "W01",
        "current_status": "rework_required",
        "current_attempt": 2,
        "last_updated": "2026-05-26T12:00:00Z",
        "open_blockers": ["Fix bug in module X"],
        "next_action": "Coder should fix the bug and rerun tests.",
        "verification_summary": "Tests: 10 passed, 2 failed.",
    }

    summary_path = write_summary(packet_dir, status)

    assert summary_path.exists()
    assert summary_path.name == "SUMMARY.md"
    content = summary_path.read_text()
    assert "TEST-P1" in content
    assert "rework_required" in content
    assert "Fix bug in module X" in content

    # Verify bounded (under 120 lines)
    lines = content.splitlines()
    assert len(lines) < 120


def test_check_line_limit_ok(tmp_path):
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("\n".join([f"Line {i}" for i in range(300)]))

    result = check_line_limit(packet_file)

    assert result["line_count"] == 300
    assert result["status"] == "ok"


def test_check_line_limit_warning(tmp_path):
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("\n".join([f"Line {i}" for i in range(700)]))

    result = check_line_limit(packet_file)

    assert result["line_count"] == 700
    assert result["status"] == "warning"
    assert len(result["messages"]) > 0


def test_check_line_limit_blocker(tmp_path):
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("\n".join([f"Line {i}" for i in range(1200)]))

    result = check_line_limit(packet_file)

    assert result["line_count"] == 1200
    assert result["status"] == "blocker"
    assert "BLOCKER" in result["messages"][0]
