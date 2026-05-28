"""
CLI contract tests for run-single-live-packet-pilot command.

Verifies CLI argument parsing, JSON envelope format, and exit codes.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


def _create_minimal_packet(path: Path, packet_id: str = "TEST-W01-PACKET") -> None:
    """Create minimal valid packet for testing."""
    path.write_text(f"""# Test Packet

- packet_id: {packet_id}
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for CLI contract tests.

## Allowed Write Scope
- src/**

## Frozen Scope
- backend/**

## Must Preserve
- Existing tests pass

## Verification
Run tests.

## Expected Evidence
- Test output

## Escalation Triggers
- Tests fail
""")


def test_cli_dry_run_json_envelope(tmp_path):
    """Verify CLI dry run returns valid JSON envelope."""
    # Create temp git repo
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    # Initialize git
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    # Create initial commit
    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    # Create packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    # Run CLI command
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "run-single-live-packet-pilot",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--target-branch", "master",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)

    # Verify JSON envelope structure
    assert "ok" in output
    assert "command" in output
    assert "project_key" in output
    assert "result" in output
    assert "data" in output
    assert "warnings" in output
    assert "errors" in output

    # Verify command name
    assert output["command"] == "run-single-live-packet-pilot"
    assert output["project_key"] == "test-project"

    # Verify result == data
    assert output["result"] == output["data"]

    # Verify result structure
    result_data = output["result"]
    assert "ok" in result_data
    assert "packet_id" in result_data
    assert "status" in result_data
    assert "dry_run" in result_data
    assert "live_opt_in_confirmed" in result_data
    assert "git_mutation_requested" in result_data
    assert "managed_runner_status" in result_data
    assert "worktree_path" in result_data
    assert "branch_name" in result_data
    assert "live_agents_started" in result_data
    assert "prefect_runs_created" in result_data
    assert "blockers" in result_data

    # Verify dry run values
    assert result_data["packet_id"] == "TEST-W01-PACKET"
    assert result_data["dry_run"] is True
    assert result_data["live_agents_started"] == 0
    assert result_data["prefect_runs_created"] == 0

    # Exit code should be 0 for successful dry run
    assert result.returncode == 0


def test_cli_missing_execute_agent_no_dry_run_flag_blocks(tmp_path):
    """Verify CLI blocks when --execute-agent is used without explicit --no-dry-run."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    # Run CLI command with --execute-agent but without --no-dry-run
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "run-single-live-packet-pilot",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--target-branch", "master",
            "--execute-agent",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)

    # Verify error
    assert output["ok"] is False
    assert len(output["errors"]) == 1
    assert output["errors"][0]["code"] == "MISSING_EXPLICIT_NO_DRY_RUN"

    # Exit code should be 2 for command error
    assert result.returncode == 2


def test_cli_missing_opt_in_blocks(tmp_path):
    """Verify CLI blocks when live opt-in requirements are missing."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    # Run CLI command with --execute-agent and --no-dry-run but missing opt-ins
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "run-single-live-packet-pilot",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--target-branch", "master",
            "--execute-agent",
            "--no-dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        env={"PATH": subprocess.os.environ["PATH"]},  # Clear GRACE_LIVE_AGENT_OPT_IN
    )

    # Parse JSON output
    output = json.loads(result.stdout)

    # Verify blocked
    assert output["ok"] is False
    result_data = output["result"]
    assert result_data["status"] == "blocked"
    assert result_data["live_opt_in_confirmed"] is False
    assert result_data["live_agents_started"] == 0
    assert len(result_data["blockers"]) >= 1

    # Exit code should be 1 for blocked
    assert result.returncode == 1


def test_cli_git_mutation_dry_run(tmp_path):
    """Verify CLI Git mutation dry run returns planned status."""
    # Create temp git repo
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    # Initialize git
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    # Create initial commit
    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    # Create packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    # Run CLI command with --commit and --push
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "run-single-live-packet-pilot",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--target-branch", "master",
            "--dry-run",
            "--commit",
            "--push",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Parse JSON output
    output = json.loads(result.stdout)

    # Verify result
    result_data = output["result"]
    assert result_data["git_mutation_requested"] is True
    assert result_data["dry_run"] is True

    # Git gate should be invoked
    assert "git_gate_result" in result_data


def test_cli_text_output_format(tmp_path):
    """Verify CLI text output format."""
    # Create temp git repo
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    # Initialize git
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    # Create initial commit
    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    # Create packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    # Run CLI command without --json
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "run-single-live-packet-pilot",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--target-branch", "master",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    # Verify text output contains expected fields
    assert "Single live packet pilot:" in result.stdout
    assert "Packet: TEST-W01-PACKET" in result.stdout
    assert "Attempt: 1" in result.stdout
    assert "Dry run: True" in result.stdout
    assert "Live opt-in confirmed:" in result.stdout
    assert "Git mutation requested:" in result.stdout
    assert "Live agents started: 0" in result.stdout
    assert "Prefect runs created: 0" in result.stdout

    # Exit code should be 0
    assert result.returncode == 0


def test_cli_required_arguments():
    """Verify CLI requires all mandatory arguments."""
    # Run CLI command without required arguments
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli",
            "run-single-live-packet-pilot",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Should fail with non-zero exit code
    assert result.returncode != 0

    # Error message should mention required arguments
    assert "required" in result.stderr.lower() or "error" in result.stderr.lower()
