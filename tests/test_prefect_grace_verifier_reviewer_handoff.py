"""Tests for verifier-reviewer handoff controller."""

from pathlib import Path
import json
import pytest
from prefect_grace.platform.verifier_reviewer_handoff import (
    HandoffAgentResult,
    PacketHandoffResult,
    parse_verifier_evidence_marker,
    parse_reviewer_decision_marker,
    validate_verifier_evidence,
    run_verifier_reviewer_handoff,
)


def test_parse_verifier_evidence_marker_valid():
    """Test parsing valid verifier evidence marker."""
    raw_output = """
Some verifier output here.

FINAL_VERIFIER_EVIDENCE_JSON
{
  "packet_id": "TEST-001",
  "generated_by": "verifier",
  "requirement_results": [
    {
      "id": "EV-TEST-001",
      "status": "collected",
      "stage": "packet_local",
      "producer": "pytest",
      "artifact_paths": ["artifacts/test.txt"],
      "summary": "Tests passed"
    }
  ]
}
END_FINAL_VERIFIER_EVIDENCE_JSON

More output.
"""
    parsed, marker_found, errors = parse_verifier_evidence_marker(raw_output)

    assert marker_found is True
    assert len(errors) == 0
    assert parsed is not None
    assert parsed["packet_id"] == "TEST-001"
    assert len(parsed["requirement_results"]) == 1


def test_parse_verifier_evidence_marker_missing():
    """Test parsing when marker is missing."""
    raw_output = "No marker here."

    parsed, marker_found, errors = parse_verifier_evidence_marker(raw_output)

    assert marker_found is False
    assert len(errors) == 1
    assert "marker not found" in errors[0].lower()
    assert parsed is None


def test_parse_verifier_evidence_marker_invalid_json():
    """Test parsing when JSON is invalid."""
    raw_output = """
FINAL_VERIFIER_EVIDENCE_JSON
{ invalid json here
END_FINAL_VERIFIER_EVIDENCE_JSON
"""

    parsed, marker_found, errors = parse_verifier_evidence_marker(raw_output)

    assert marker_found is True
    assert len(errors) == 1
    assert "invalid json" in errors[0].lower()
    assert parsed is None


def test_parse_reviewer_decision_marker_valid():
    """Test parsing valid reviewer decision marker."""
    raw_output = """
Reviewer analysis.

FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "accepted",
  "route_classification": "self_resolvable_rework",
  "rework_mode": null,
  "reasons": []
}
END_FINAL_PACKET_DECISION_JSON
"""

    parsed, marker_found, errors = parse_reviewer_decision_marker(raw_output)

    assert marker_found is True
    assert len(errors) == 0
    assert parsed is not None
    assert parsed["packet_verdict"] == "accepted"


def test_parse_reviewer_decision_marker_missing():
    """Test parsing when marker is missing."""
    raw_output = "No marker here."

    parsed, marker_found, errors = parse_reviewer_decision_marker(raw_output)

    assert marker_found is False
    assert len(errors) == 1
    assert "marker not found" in errors[0].lower()
    assert parsed is None


def test_validate_verifier_evidence_valid(tmp_path):
    """Test validating valid evidence."""
    # Create artifact file
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "test.txt"
    artifact_file.write_text("test output")

    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["artifacts/test.txt"],
                "summary": "Tests passed"
            }
        ]
    }

    ok, errors = validate_verifier_evidence(
        evidence_json,
        tmp_path,
        [tmp_path]
    )

    assert ok is True
    assert len(errors) == 0


def test_validate_verifier_evidence_missing_artifact(tmp_path):
    """Test validating evidence with missing artifact."""
    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["artifacts/missing.txt"],
                "summary": "Tests passed"
            }
        ]
    }

    ok, errors = validate_verifier_evidence(
        evidence_json,
        tmp_path,
        [tmp_path]
    )

    assert ok is False
    assert len(errors) == 1
    assert "does not exist" in errors[0].lower()


def test_validate_verifier_evidence_invalid_status(tmp_path):
    """Test validating evidence with invalid status."""
    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "invalid_status",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": [],
                "summary": "Tests passed"
            }
        ]
    }

    ok, errors = validate_verifier_evidence(
        evidence_json,
        tmp_path,
        [tmp_path]
    )

    assert ok is False
    assert len(errors) == 1
    assert "invalid status" in errors[0].lower()


def test_validate_verifier_evidence_invalid_stage(tmp_path):
    """Test validating evidence with invalid stage."""
    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "invalid_stage",
                "producer": "pytest",
                "artifact_paths": [],
                "summary": "Tests passed"
            }
        ]
    }

    ok, errors = validate_verifier_evidence(
        evidence_json,
        tmp_path,
        [tmp_path]
    )

    assert ok is False
    assert len(errors) == 1
    assert "invalid stage" in errors[0].lower()


def test_validate_verifier_evidence_absolute_path_outside_root(tmp_path):
    """Test that absolute paths outside allowed roots are rejected."""
    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["/etc/passwd"],
                "summary": "Tests passed"
            }
        ]
    }

    ok, errors = validate_verifier_evidence(
        evidence_json,
        tmp_path,
        [tmp_path]
    )

    assert ok is False
    assert len(errors) == 1
    assert "/etc/passwd" in errors[0]
    assert "does not exist" in errors[0]


def test_validate_verifier_evidence_relative_path_traversal(tmp_path):
    """Test that relative path traversal outside root is rejected."""
    # Create file outside tmp_path
    outside_dir = tmp_path.parent / "outside"
    outside_dir.mkdir(exist_ok=True)
    outside_file = outside_dir / "outside.txt"
    outside_file.write_text("outside content")

    evidence_json = {
        "requirement_results": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["../outside/outside.txt"],
                "summary": "Tests passed"
            }
        ]
    }

    ok, errors = validate_verifier_evidence(
        evidence_json,
        tmp_path,
        [tmp_path]
    )

    # artifact_validator should reject this because it resolves outside allowed root
    assert ok is False
    assert len(errors) == 1
    assert "../outside/outside.txt" in errors[0]


def test_handoff_agent_result_to_dict():
    """Test HandoffAgentResult serialization."""
    result = HandoffAgentResult(
        ok=True,
        role="verifier",
        packet_id="TEST-001",
        raw_output="output",
        parsed_json={"key": "value"},
        marker_found=True,
        errors=[]
    )

    data = result.to_dict()

    assert data["ok"] is True
    assert data["role"] == "verifier"
    assert data["packet_id"] == "TEST-001"
    assert data["parsed_json"]["key"] == "value"


def test_packet_handoff_result_to_dict():
    """Test PacketHandoffResult serialization."""
    verifier = HandoffAgentResult(
        ok=True,
        role="verifier",
        packet_id="TEST-001",
        raw_output="output",
        parsed_json={},
        marker_found=True,
        errors=[]
    )

    result = PacketHandoffResult(
        ok=True,
        domain_status="accepted",
        packet_id="TEST-001",
        attempt=1,
        verifier=verifier,
        reviewer=None,
        evidence_manifest_path="/path/to/evidence.json",
        review_path="/path/to/review.md",
        rework_path=None,
    )

    data = result.to_dict()

    assert data["ok"] is True
    assert data["domain_status"] == "accepted"
    assert data["packet_id"] == "TEST-001"
    assert data["verifier"]["ok"] is True


def test_run_verifier_reviewer_handoff_accepted(tmp_path):
    """Test complete handoff flow with accepted verdict."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    # Create artifact
    artifact_dir = packet_dir / "artifacts"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "test.txt"
    artifact_file.write_text("test output")

    coder_result = {
        "packet_id": "TEST-001",
        "worktree_path": None,
    }

    verifier_output = """
FINAL_VERIFIER_EVIDENCE_JSON
{
  "packet_id": "TEST-001",
  "generated_by": "verifier",
  "requirement_results": [
    {
      "id": "EV-TEST-001",
      "status": "collected",
      "stage": "packet_local",
      "producer": "pytest",
      "artifact_paths": ["artifacts/test.txt"],
      "summary": "Tests passed"
    }
  ]
}
END_FINAL_VERIFIER_EVIDENCE_JSON
"""

    reviewer_output = """
FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "accepted",
  "route_classification": null,
  "rework_mode": null,
  "reasons": []
}
END_FINAL_PACKET_DECISION_JSON
"""

    def fake_verifier_launcher(**kwargs):
        return {"raw_output": verifier_output}

    def fake_reviewer_launcher(**kwargs):
        return {"raw_output": reviewer_output}

    result = run_verifier_reviewer_handoff(
        packet_dir=packet_dir,
        packet_file=packet_file,
        attempt=1,
        coder_result=coder_result,
        verifier_launcher=fake_verifier_launcher,
        reviewer_launcher=fake_reviewer_launcher,
        project=None,
        dry_run=True,
    )

    assert result.ok is True
    assert result.domain_status == "accepted"
    assert result.verifier.ok is True
    assert result.reviewer.ok is True
    assert result.evidence_manifest_path is not None
    assert result.review_path is not None


def test_run_verifier_reviewer_handoff_verifier_failed(tmp_path):
    """Test handoff flow when verifier fails."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    coder_result = {
        "packet_id": "TEST-001",
        "worktree_path": None,
    }

    verifier_output = "No marker here"

    def fake_verifier_launcher(**kwargs):
        return {"raw_output": verifier_output}

    def fake_reviewer_launcher(**kwargs):
        return {"raw_output": ""}

    result = run_verifier_reviewer_handoff(
        packet_dir=packet_dir,
        packet_file=packet_file,
        attempt=1,
        coder_result=coder_result,
        verifier_launcher=fake_verifier_launcher,
        reviewer_launcher=fake_reviewer_launcher,
        project=None,
        dry_run=True,
    )

    assert result.ok is False
    assert result.domain_status == "verifier_failed"
    assert result.verifier.ok is False
    assert result.reviewer is None


def test_run_verifier_reviewer_handoff_rework_required(tmp_path):
    """Test handoff flow with rework_required verdict."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    # Create artifact
    artifact_dir = packet_dir / "artifacts"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "test.txt"
    artifact_file.write_text("test output")

    coder_result = {
        "packet_id": "TEST-001",
        "worktree_path": None,
    }

    verifier_output = """
FINAL_VERIFIER_EVIDENCE_JSON
{
  "packet_id": "TEST-001",
  "generated_by": "verifier",
  "requirement_results": [
    {
      "id": "EV-TEST-001",
      "status": "collected",
      "stage": "packet_local",
      "producer": "pytest",
      "artifact_paths": ["artifacts/test.txt"],
      "summary": "Tests passed"
    }
  ]
}
END_FINAL_VERIFIER_EVIDENCE_JSON
"""

    reviewer_output = """
FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "rework_required",
  "route_classification": "self_resolvable_rework",
  "rework_mode": "bounded_fresh",
  "reasons": ["Missing test coverage"]
}
END_FINAL_PACKET_DECISION_JSON
"""

    def fake_verifier_launcher(**kwargs):
        return {"raw_output": verifier_output}

    def fake_reviewer_launcher(**kwargs):
        return {"raw_output": reviewer_output}

    result = run_verifier_reviewer_handoff(
        packet_dir=packet_dir,
        packet_file=packet_file,
        attempt=1,
        coder_result=coder_result,
        verifier_launcher=fake_verifier_launcher,
        reviewer_launcher=fake_reviewer_launcher,
        project=None,
        dry_run=True,
    )

    assert result.ok is True
    assert result.domain_status == "rework_required"
    assert result.verifier.ok is True
    assert result.reviewer.ok is True
    assert result.rework_path is not None
    assert result.route_classification == "self_resolvable_rework"
    assert result.rework_mode == "bounded_fresh"
