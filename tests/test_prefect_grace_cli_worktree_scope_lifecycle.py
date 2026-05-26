import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for CLI testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        repo_path.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        readme = repo_path / "README.md"
        readme.write_text("# Test Repo\n")
        subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def temp_packet_file(temp_git_repo):
    """Create a temporary packet file for testing."""
    packet_dir = temp_git_repo / "packets" / "TEST-PACKET"
    packet_dir.mkdir(parents=True)

    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_content = """# Execution Packet: Test Packet

packet_id: TEST-PACKET-W01-TEST
feature_id: TEST-PACKET
wave_id: W01
title: Test Packet
objective: Test packet for lifecycle gate
status: ready
phase: TEST-PHASE

## Allowed Write Scope

- allowed/file.txt
- allowed/**

## Frozen Scope

- frozen/file.txt
- frozen/**

## Must Preserve

- Test preservation rule

## Verification

Test verification

## Expected Evidence

Test evidence
"""
    packet_file.write_text(packet_content)
    return packet_file


def test_cli_worktree_scope_check_json_success(temp_git_repo, temp_packet_file):
    """Test worktree-scope-check CLI with JSON output for success case."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            str(temp_packet_file),
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "1",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "worktree-scope-check"
    assert output["result"]["status"] == "passed"
    assert output["result"]["packet_id"] == "TEST-PACKET-W01-TEST"
    assert output["result"]["attempt"] == 1


def test_cli_worktree_scope_check_json_scope_violation(temp_git_repo, temp_packet_file):
    """Test worktree-scope-check CLI with JSON output for scope violation."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # First create worktree
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            str(temp_packet_file),
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "2",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Add frozen file to worktree
    worktree_path = worktree_root / "TEST-PACKET-W01-TEST-attempt-0002"
    frozen_file = worktree_path / "frozen" / "file.txt"
    frozen_file.parent.mkdir(parents=True, exist_ok=True)
    frozen_file.write_text("frozen content\n")

    # Re-run check
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            str(temp_packet_file),
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "2",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["status"] == "scope_blocked"
    assert output["result"]["blocker_reason"] is not None
    assert len(output["result"]["scope_guard"]["frozen_violations"]) > 0


def test_cli_worktree_scope_check_text_mode_passed(temp_git_repo, temp_packet_file):
    """Test worktree-scope-check CLI with text output for passed case."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            str(temp_packet_file),
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "3",
            "--base-ref",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Lifecycle: PASSED" in result.stdout
    assert "Packet: TEST-PACKET-W01-TEST" in result.stdout
    assert "Attempt: 3" in result.stdout


def test_cli_worktree_scope_check_text_mode_blocked(temp_git_repo, temp_packet_file):
    """Test worktree-scope-check CLI with text output for blocked case."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # First create worktree
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            str(temp_packet_file),
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "4",
            "--base-ref",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Add outside file to worktree
    worktree_path = worktree_root / "TEST-PACKET-W01-TEST-attempt-0004"
    outside_file = worktree_path / "outside" / "file.txt"
    outside_file.parent.mkdir(parents=True, exist_ok=True)
    outside_file.write_text("outside content\n")

    # Re-run check
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            str(temp_packet_file),
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "4",
            "--base-ref",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Lifecycle: SCOPE BLOCKED" in result.stdout
    assert "Blocker:" in result.stdout
    assert "Outside allowed:" in result.stdout


def test_cli_worktree_scope_check_invalid_packet(temp_git_repo):
    """Test worktree-scope-check CLI with invalid packet path."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            "/nonexistent/packet.md",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "5",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["status"] == "worktree_error"


def test_cli_worktree_scope_check_exit_codes(temp_git_repo, temp_packet_file):
    """Test that CLI exits with correct codes: 0=passed, 1=blocked, 2=error."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Test exit 0 for passed
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            str(temp_packet_file),
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "6",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    # Test exit 2 for error (invalid packet)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-scope-check",
            "--packet",
            "/nonexistent/packet.md",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "TEST-PACKET-W01-TEST",
            "--attempt",
            "7",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
