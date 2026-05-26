"""Tests for verifier-reviewer handoff Prefect flow."""

from pathlib import Path
import pytest


def test_verifier_reviewer_handoff_flow_accepted(tmp_path):
    """Test handoff flow with accepted verdict."""
    from prefect_grace.flows.verifier_reviewer_handoff_flow import verifier_reviewer_handoff_flow

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

    result = verifier_reviewer_handoff_flow(
        packet_dir=packet_dir,
        packet_file=packet_file,
        attempt=1,
        coder_result=coder_result,
        verifier_launcher=fake_verifier_launcher,
        reviewer_launcher=fake_reviewer_launcher,
        project=None,
        dry_run=True,
    )

    assert result["ok"] is True
    assert result["domain_status"] == "accepted"
    assert result["verifier"]["ok"] is True
    assert result["reviewer"]["ok"] is True


def test_verifier_reviewer_handoff_flow_verifier_failed(tmp_path):
    """Test handoff flow when verifier fails."""
    from prefect_grace.flows.verifier_reviewer_handoff_flow import verifier_reviewer_handoff_flow

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

    result = verifier_reviewer_handoff_flow(
        packet_dir=packet_dir,
        packet_file=packet_file,
        attempt=1,
        coder_result=coder_result,
        verifier_launcher=fake_verifier_launcher,
        reviewer_launcher=fake_reviewer_launcher,
        project=None,
        dry_run=True,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "verifier_failed"
    assert result["verifier"]["ok"] is False
    assert result["reviewer"] is None


def test_verifier_reviewer_handoff_flow_rework_required(tmp_path):
    """Test handoff flow with rework_required verdict."""
    from prefect_grace.flows.verifier_reviewer_handoff_flow import verifier_reviewer_handoff_flow

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

    result = verifier_reviewer_handoff_flow(
        packet_dir=packet_dir,
        packet_file=packet_file,
        attempt=1,
        coder_result=coder_result,
        verifier_launcher=fake_verifier_launcher,
        reviewer_launcher=fake_reviewer_launcher,
        project=None,
        dry_run=True,
    )

    assert result["ok"] is True
    assert result["domain_status"] == "rework_required"
    assert result["verifier"]["ok"] is True
    assert result["reviewer"]["ok"] is True
    assert result["rework_path"] is not None


def test_verifier_reviewer_handoff_flow_exception_handling(tmp_path):
    """Test handoff flow exception handling."""
    from prefect_grace.flows.verifier_reviewer_handoff_flow import verifier_reviewer_handoff_flow

    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    coder_result = {
        "packet_id": "TEST-001",
        "worktree_path": None,
    }

    def failing_verifier_launcher(**kwargs):
        raise RuntimeError("Verifier launcher failed")

    def fake_reviewer_launcher(**kwargs):
        return {"raw_output": ""}

    result = verifier_reviewer_handoff_flow(
        packet_dir=packet_dir,
        packet_file=packet_file,
        attempt=1,
        coder_result=coder_result,
        verifier_launcher=failing_verifier_launcher,
        reviewer_launcher=fake_reviewer_launcher,
        project=None,
        dry_run=True,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "handoff_error"
    assert "failed" in result["blocker_reason"].lower()
