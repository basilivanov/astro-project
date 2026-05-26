"""Tests for CLI handoff command."""

from pathlib import Path
import json
import subprocess
import pytest


def test_run_handoff_cli_help():
    """Test run-handoff CLI help."""
    result = subprocess.run(
        ["python3", "-m", "prefect_grace.cli", "run-handoff", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "run-handoff" in result.stdout
    assert "--packet-dir" in result.stdout
    assert "--packet" in result.stdout
    assert "--attempt" in result.stdout
    assert "--coder-result" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--fake-verifier-output" in result.stdout
    assert "--fake-reviewer-output" in result.stdout
    assert "--json" in result.stdout


def test_run_handoff_cli_dry_run_missing_fake_outputs(tmp_path):
    """Test run-handoff CLI in dry-run mode without fake outputs."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    coder_result_file = tmp_path / "coder_result.json"
    coder_result_file.write_text(json.dumps({
        "packet_id": "TEST-001",
        "worktree_path": None,
    }))

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-handoff",
            "--packet-dir", str(packet_dir),
            "--packet", str(packet_file),
            "--attempt", "1",
            "--coder-result", str(coder_result_file),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert len(output["errors"]) == 1
    assert "fake" in output["errors"][0]["message"].lower()


def test_run_handoff_cli_dry_run_accepted(tmp_path):
    """Test run-handoff CLI in dry-run mode with accepted verdict."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    # Create artifact
    artifact_dir = packet_dir / "artifacts"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "test.txt"
    artifact_file.write_text("test output")

    coder_result_file = tmp_path / "coder_result.json"
    coder_result_file.write_text(json.dumps({
        "packet_id": "TEST-001",
        "worktree_path": None,
    }))

    verifier_output_file = tmp_path / "verifier_output.txt"
    verifier_output_file.write_text("""
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
""")

    reviewer_output_file = tmp_path / "reviewer_output.txt"
    reviewer_output_file.write_text("""
FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "accepted",
  "route_classification": null,
  "rework_mode": null,
  "reasons": []
}
END_FINAL_PACKET_DECISION_JSON
""")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-handoff",
            "--packet-dir", str(packet_dir),
            "--packet", str(packet_file),
            "--attempt", "1",
            "--coder-result", str(coder_result_file),
            "--dry-run",
            "--fake-verifier-output", str(verifier_output_file),
            "--fake-reviewer-output", str(reviewer_output_file),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["result"]["domain_status"] == "accepted"


def test_run_handoff_cli_dry_run_rework_required(tmp_path):
    """Test run-handoff CLI in dry-run mode with rework_required verdict."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    # Create artifact
    artifact_dir = packet_dir / "artifacts"
    artifact_dir.mkdir()
    artifact_file = artifact_dir / "test.txt"
    artifact_file.write_text("test output")

    coder_result_file = tmp_path / "coder_result.json"
    coder_result_file.write_text(json.dumps({
        "packet_id": "TEST-001",
        "worktree_path": None,
    }))

    verifier_output_file = tmp_path / "verifier_output.txt"
    verifier_output_file.write_text("""
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
""")

    reviewer_output_file = tmp_path / "reviewer_output.txt"
    reviewer_output_file.write_text("""
FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "rework_required",
  "route_classification": "self_resolvable_rework",
  "rework_mode": "bounded_fresh",
  "reasons": ["Missing test coverage"]
}
END_FINAL_PACKET_DECISION_JSON
""")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-handoff",
            "--packet-dir", str(packet_dir),
            "--packet", str(packet_file),
            "--attempt", "1",
            "--coder-result", str(coder_result_file),
            "--dry-run",
            "--fake-verifier-output", str(verifier_output_file),
            "--fake-reviewer-output", str(reviewer_output_file),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["result"]["domain_status"] == "rework_required"


def test_run_handoff_cli_dry_run_verifier_failed(tmp_path):
    """Test run-handoff CLI in dry-run mode with verifier failure."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    coder_result_file = tmp_path / "coder_result.json"
    coder_result_file.write_text(json.dumps({
        "packet_id": "TEST-001",
        "worktree_path": None,
    }))

    verifier_output_file = tmp_path / "verifier_output.txt"
    verifier_output_file.write_text("No marker here")

    reviewer_output_file = tmp_path / "reviewer_output.txt"
    reviewer_output_file.write_text("")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-handoff",
            "--packet-dir", str(packet_dir),
            "--packet", str(packet_file),
            "--attempt", "1",
            "--coder-result", str(coder_result_file),
            "--dry-run",
            "--fake-verifier-output", str(verifier_output_file),
            "--fake-reviewer-output", str(reviewer_output_file),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["domain_status"] == "verifier_failed"


def test_run_handoff_cli_live_mode_not_implemented(tmp_path):
    """Test run-handoff CLI in live mode (not implemented)."""
    packet_dir = tmp_path / "packet"
    packet_dir.mkdir()
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("# Packet")

    coder_result_file = tmp_path / "coder_result.json"
    coder_result_file.write_text(json.dumps({
        "packet_id": "TEST-001",
        "worktree_path": None,
    }))

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-handoff",
            "--packet-dir", str(packet_dir),
            "--packet", str(packet_file),
            "--attempt", "1",
            "--coder-result", str(coder_result_file),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Should fail because --dry-run defaults to True but fake outputs are missing
    assert result.returncode == 2
