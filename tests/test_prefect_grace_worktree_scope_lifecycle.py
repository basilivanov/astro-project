import subprocess
import tempfile
from pathlib import Path

import pytest

from prefect_grace.platform.status_model import DomainStatus
from prefect_grace.platform.worktree_scope_lifecycle import evaluate_worktree_scope


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
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


def test_lifecycle_passes_when_changed_file_is_allowed(temp_git_repo, temp_packet_file):
    """Test that lifecycle passes when changed file is in allowed scope."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Evaluate lifecycle (will create worktree)
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=1,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result.worktree_path)
    assert worktree_path.exists()

    # Add allowed file in worktree
    allowed_file = worktree_path / "allowed" / "file.txt"
    allowed_file.parent.mkdir(parents=True, exist_ok=True)
    allowed_file.write_text("allowed content\n")

    # Re-evaluate with existing worktree
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=1,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    assert result.ok is True
    assert result.status == "passed"
    assert result.blocker_reason is None
    assert "allowed/file.txt" in result.changed_files
    assert result.scope_guard["ok"] is True


def test_lifecycle_blocks_when_changed_file_is_frozen(temp_git_repo, temp_packet_file):
    """Test that lifecycle blocks when changed file is in frozen scope."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Evaluate lifecycle (will create worktree)
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=2,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result.worktree_path)
    assert worktree_path.exists()

    # Add frozen file in worktree
    frozen_file = worktree_path / "frozen" / "file.txt"
    frozen_file.parent.mkdir(parents=True, exist_ok=True)
    frozen_file.write_text("frozen content\n")

    # Re-evaluate with existing worktree
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=2,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    assert result.ok is False
    assert result.status == "scope_blocked"
    assert result.blocker_reason is not None
    assert "frozen violation" in result.blocker_reason.lower()
    assert "frozen/file.txt" in result.changed_files
    assert result.scope_guard["ok"] is False
    assert len(result.scope_guard["frozen_violations"]) > 0


def test_lifecycle_blocks_when_changed_file_is_outside_allowed(temp_git_repo, temp_packet_file):
    """Test that lifecycle blocks when changed file is outside allowed scope."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Evaluate lifecycle (will create worktree)
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=3,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result.worktree_path)
    assert worktree_path.exists()

    # Add file outside allowed scope
    outside_file = worktree_path / "outside" / "file.txt"
    outside_file.parent.mkdir(parents=True, exist_ok=True)
    outside_file.write_text("outside content\n")

    # Re-evaluate with existing worktree
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=3,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    assert result.ok is False
    assert result.status == "scope_blocked"
    assert result.blocker_reason is not None
    assert "outside allowed" in result.blocker_reason.lower()
    assert "outside/file.txt" in result.changed_files
    assert result.scope_guard["ok"] is False
    assert len(result.scope_guard["outside_allowed"]) > 0


def test_lifecycle_preserves_blocked_worktree_by_default(temp_git_repo, temp_packet_file):
    """Test that lifecycle preserves blocked worktree by default."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Evaluate lifecycle (will create worktree)
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=4,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result.worktree_path)
    assert worktree_path.exists()

    # Add frozen file to trigger block
    frozen_file = worktree_path / "frozen" / "file.txt"
    frozen_file.parent.mkdir(parents=True, exist_ok=True)
    frozen_file.write_text("frozen content\n")

    # Re-evaluate with existing worktree
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=4,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    assert result.status == "scope_blocked"

    # Worktree should still exist after block
    assert worktree_path.exists()
    assert frozen_file.exists()


def test_lifecycle_output_includes_changed_files_and_scope_details(temp_git_repo, temp_packet_file):
    """Test that lifecycle output includes changed files and scope guard details."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Evaluate lifecycle (will create worktree)
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=5,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Worktree should be created
    worktree_path = Path(result.worktree_path)
    assert worktree_path.exists()

    # Add multiple files
    allowed_file = worktree_path / "allowed" / "file1.txt"
    allowed_file.parent.mkdir(parents=True, exist_ok=True)
    allowed_file.write_text("allowed\n")

    frozen_file = worktree_path / "frozen" / "file2.txt"
    frozen_file.parent.mkdir(parents=True, exist_ok=True)
    frozen_file.write_text("frozen\n")

    # Re-evaluate
    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=5,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Check output structure
    assert result.packet_id == "TEST-PACKET-W01-TEST"
    assert result.attempt == 5
    assert result.worktree_path != ""
    assert result.branch_name != ""
    assert len(result.changed_files) == 2
    assert "allowed/file1.txt" in result.changed_files
    assert "frozen/file2.txt" in result.changed_files
    assert "ok" in result.scope_guard
    assert "frozen_violations" in result.scope_guard
    assert "outside_allowed" in result.scope_guard


def test_lifecycle_returns_error_on_invalid_packet_path(temp_git_repo):
    """Test that lifecycle returns worktree_error on invalid packet path."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = evaluate_worktree_scope(
        packet_file=Path("/nonexistent/packet.md"),
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=6,
        base_ref="HEAD",
        keep_on_failure=True,
    )

    assert result.ok is False
    assert result.status == "worktree_error"
    assert result.blocker_reason is not None
    assert "parse failed" in result.blocker_reason.lower()


def test_lifecycle_to_dict_serialization(temp_git_repo, temp_packet_file):
    """Test that lifecycle result can be serialized to dict."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Get base commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    result = evaluate_worktree_scope(
        packet_file=temp_packet_file,
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET-W01-TEST",
        attempt=7,
        base_ref=base_commit,
        keep_on_failure=True,
    )

    # Convert to dict
    result_dict = result.to_dict()

    # Check structure
    assert isinstance(result_dict, dict)
    assert "ok" in result_dict
    assert "packet_id" in result_dict
    assert "attempt" in result_dict
    assert "worktree_path" in result_dict
    assert "branch_name" in result_dict
    assert "changed_files" in result_dict
    assert "scope_guard" in result_dict
    assert "status" in result_dict
    assert "blocker_reason" in result_dict
    assert isinstance(result_dict["status"], str)
    assert result_dict["status"] == DomainStatus.CHECK_PASSED.value
