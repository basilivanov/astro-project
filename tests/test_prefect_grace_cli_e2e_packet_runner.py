"""Tests for prefect_grace CLI run-e2e-packet command."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True, capture_output=True)

        # Create initial commit
        (repo_root / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_root, check=True, capture_output=True)

        yield repo_root


@pytest.fixture
def temp_packet(temp_repo):
    """Create a temporary test packet."""
    packet_dir = temp_repo / "prefect_grace" / "packets" / "CLI-TEST"
    packet_dir.mkdir(parents=True)

    packet_content = """# Execution Packet: CLI Test Packet

## Objective
Test packet for CLI e2e runner testing.

## Slice
- packet_id: CLI-TEST-W01-E2E
- feature_id: CLI-TEST
- wave_id: W01
- status: ready

## Allowed Write Scope
- /tmp/**

## Frozen Scope
- /etc/**

## Must Preserve
- No live agents called

## Verification
Run pytest.

## Expected Evidence
- EV-001: Test output (stage: packet_local, producer: pytest)

## Escalation Triggers
- Live agents required
"""

    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(packet_content)

    return packet_path


def test_cli_run_e2e_packet_help():
    """Test run-e2e-packet --help."""
    result = subprocess.run(
        ["python3", "-m", "prefect_grace.cli", "run-e2e-packet", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "run-e2e-packet" in result.stdout
    assert "--project-root" in result.stdout
    assert "--packet" in result.stdout
    assert "--state-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--fake-verifier-output" in result.stdout
    assert "--fake-reviewer-output" in result.stdout


def test_cli_run_e2e_packet_json_output(temp_repo, temp_packet):
    """Test run-e2e-packet with JSON output."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-e2e-packet",
            "--project-root", str(temp_repo),
            "--packet", str(temp_packet),
            "--state-root", str(state_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "cli-test",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)

    assert output["ok"] is True
    assert output["command"] == "run-e2e-packet"
    assert "result" in output
    assert output["result"]["packet_id"] == "CLI-TEST-W01-E2E"
    assert output["result"]["domain_status"] == "accepted"
    assert output["result"]["runtime_status"] == "completed"
    assert result.returncode == 0


def test_cli_run_e2e_packet_exit_codes(temp_repo, temp_packet):
    """Test run-e2e-packet exit codes."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    # Test accepted (exit code 0)
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-e2e-packet",
            "--project-root", str(temp_repo),
            "--packet", str(temp_packet),
            "--state-root", str(state_root),
            "--worktree-root", str(worktree_root),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert output["result"]["domain_status"] == "accepted"
    assert result.returncode == 0

    # Test rework_required (exit code 1)
    fake_reviewer_file = temp_repo / "fake_reviewer_rework.txt"
    fake_reviewer_file.write_text("""
FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "rework_required",
  "route_classification": "quality_rework",
  "rework_mode": "light_resume",
  "reasons": ["Test"]
}
END_FINAL_PACKET_DECISION_JSON
""")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-e2e-packet",
            "--project-root", str(temp_repo),
            "--packet", str(temp_packet),
            "--state-root", str(state_root),
            "--worktree-root", str(worktree_root),
            "--fake-reviewer-output", str(fake_reviewer_file),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert output["result"]["domain_status"] == "rework_required"
    assert result.returncode == 1


def test_cli_run_e2e_packet_fake_outputs(temp_repo, temp_packet):
    """Test run-e2e-packet with custom fake outputs."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    # Create custom fake outputs
    fake_verifier_file = temp_repo / "custom_verifier.txt"
    fake_verifier_file.write_text("""
FINAL_VERIFIER_EVIDENCE_JSON
{
  "packet_id": "CLI-TEST-W01-E2E",
  "generated_by": "verifier",
  "requirement_results": [
    {
      "id": "EV-CLI-001",
      "status": "collected",
      "stage": "packet_local",
      "producer": "cli_test",
      "artifact_paths": [],
      "summary": "CLI test evidence"
    }
  ]
}
END_FINAL_VERIFIER_EVIDENCE_JSON
""")

    fake_reviewer_file = temp_repo / "custom_reviewer.txt"
    fake_reviewer_file.write_text("""
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
            "python3", "-m", "prefect_grace.cli", "run-e2e-packet",
            "--project-root", str(temp_repo),
            "--packet", str(temp_packet),
            "--state-root", str(state_root),
            "--worktree-root", str(worktree_root),
            "--fake-verifier-output", str(fake_verifier_file),
            "--fake-reviewer-output", str(fake_reviewer_file),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["result"]["domain_status"] == "accepted"
    assert result.returncode == 0


def test_cli_run_e2e_packet_missing_project_root():
    """Test run-e2e-packet with missing project root."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-e2e-packet",
            "--project-root", "/nonexistent/path",
            "--packet", "/nonexistent/packet.md",
            "--state-root", "/tmp/state",
            "--worktree-root", "/tmp/worktrees",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert "errors" in output
    assert result.returncode == 2


def test_cli_run_e2e_packet_human_readable_output(temp_repo, temp_packet):
    """Test run-e2e-packet with human-readable output."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-e2e-packet",
            "--project-root", str(temp_repo),
            "--packet", str(temp_packet),
            "--state-root", str(state_root),
            "--worktree-root", str(worktree_root),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    assert "E2E Packet Runner:" in result.stdout
    assert "accepted" in result.stdout
    assert "Packet:" in result.stdout
    assert "CLI-TEST-W01-E2E" in result.stdout
    assert result.returncode == 0


def test_cli_run_e2e_packet_default_values(temp_repo, temp_packet):
    """Test run-e2e-packet with default parameter values."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    # Run without specifying optional parameters
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-e2e-packet",
            "--project-root", str(temp_repo),
            "--packet", str(temp_packet),
            "--state-root", str(state_root),
            "--worktree-root", str(worktree_root),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["result"]["attempt"] == 1
    assert result.returncode == 0
