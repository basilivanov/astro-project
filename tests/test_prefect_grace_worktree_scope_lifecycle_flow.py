import subprocess
import tempfile
from pathlib import Path

import pytest

from prefect_grace.flows.worktree_scope_lifecycle_flow import (
    worktree_scope_lifecycle_flow,
)


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for flow testing."""
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
objective: Test packet for flow
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


def test_flow_returns_passed_for_allowed_file(temp_git_repo, temp_packet_file):
    """Test that flow returns domain_status=passed for allowed changed file."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Run flow (creates worktree)
    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=1,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result["worktree_path"])
    assert worktree_path.exists()

    # Add allowed file in worktree
    allowed_file = worktree_path / "allowed" / "file.txt"
    allowed_file.parent.mkdir(parents=True, exist_ok=True)
    allowed_file.write_text("allowed content\n")

    # Re-run flow with existing worktree
    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=1,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    assert result["ok"] is True
    assert result["domain_status"] == "passed"
    assert result["packet_id"] == "TEST-PACKET-W01-TEST"
    assert result["attempt"] == 1
    assert "allowed/file.txt" in result["changed_files"]
    assert result["scope_guard"]["ok"] is True
    assert "artifact_ids" in result


def test_flow_returns_scope_blocked_for_frozen_file(temp_git_repo, temp_packet_file):
    """Test that flow returns domain_status=scope_blocked for frozen changed file."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Run flow (creates worktree)
    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=2,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result["worktree_path"])
    assert worktree_path.exists()

    # Add frozen file in worktree
    frozen_file = worktree_path / "frozen" / "file.txt"
    frozen_file.parent.mkdir(parents=True, exist_ok=True)
    frozen_file.write_text("frozen content\n")

    # Re-run flow with existing worktree
    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=2,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "scope_blocked"
    assert result["packet_id"] == "TEST-PACKET-W01-TEST"
    assert result["attempt"] == 2
    assert "frozen/file.txt" in result["changed_files"]
    assert result["scope_guard"]["ok"] is False
    assert len(result["scope_guard"]["frozen_violations"]) > 0


def test_flow_preserves_blocked_worktree(temp_git_repo, temp_packet_file):
    """Test that flow preserves blocked worktree by default."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Run flow (creates worktree)
    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=3,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result["worktree_path"])
    assert worktree_path.exists()

    # Add frozen file to trigger block
    frozen_file = worktree_path / "frozen" / "file.txt"
    frozen_file.parent.mkdir(parents=True, exist_ok=True)
    frozen_file.write_text("frozen content\n")

    # Re-run flow with existing worktree
    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=3,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    assert result["domain_status"] == "scope_blocked"

    # Worktree should still exist after block
    assert worktree_path.exists()
    assert frozen_file.exists()


def test_flow_includes_artifact_ids(temp_git_repo, temp_packet_file):
    """Test that flow includes artifact_ids in result."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Run flow
    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=4,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # artifact_ids should be present (may be empty if Prefect unavailable)
    assert "artifact_ids" in result
    assert isinstance(result["artifact_ids"], list)


def test_flow_returns_worktree_error_on_invalid_packet(temp_git_repo):
    """Test that flow returns domain_status=worktree_error on invalid packet."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = worktree_scope_lifecycle_flow(
        packet_file="/nonexistent/packet.md",
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=5,
        base_ref="HEAD",
        keep_on_failure=True,
    )

    assert result["ok"] is False
    assert result["domain_status"] == "worktree_error"
    assert result["packet_id"] == "TEST-PACKET-W01-TEST"
    assert result["attempt"] == 5


def test_flow_result_structure(temp_git_repo, temp_packet_file):
    """Test that flow result has expected structure."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    result = worktree_scope_lifecycle_flow(
        packet_file=str(temp_packet_file),
        repo_root=str(temp_git_repo),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=6,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Check required fields
    assert "ok" in result
    assert "domain_status" in result
    assert "packet_id" in result
    assert "attempt" in result
    assert "worktree_path" in result
    assert "branch_name" in result
    assert "changed_files" in result
    assert "scope_guard" in result
    assert "artifact_ids" in result

    # Check types
    assert isinstance(result["ok"], bool)
    assert isinstance(result["domain_status"], str)
    assert isinstance(result["packet_id"], str)
    assert isinstance(result["attempt"], int)
    assert isinstance(result["worktree_path"], str)
    assert isinstance(result["branch_name"], str)
    assert isinstance(result["changed_files"], list)
    assert isinstance(result["scope_guard"], dict)
    assert isinstance(result["artifact_ids"], list)
