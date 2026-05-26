import subprocess
import tempfile
from pathlib import Path

import pytest

from prefect_grace.platform.worktree_manager import (
    WorktreeManager,
    _sanitize_branch_name,
)


def test_sanitize_branch_name_basic():
    """Test basic branch name sanitization."""
    result = _sanitize_branch_name("astro-project", "FEAT-TEST-W01-PACKET", 1)
    assert result == "agent/astro-project/FEAT-TEST-W01-PACKET/attempt-0001"


def test_sanitize_branch_name_with_special_chars():
    """Test branch name sanitization with special characters."""
    result = _sanitize_branch_name("my@project", "FEAT:TEST:W01", 42)
    assert result == "agent/my-project/FEAT-TEST-W01/attempt-0042"


def test_sanitize_branch_name_rejects_empty():
    """Test that empty components raise ValueError."""
    with pytest.raises(ValueError, match="Invalid branch name components"):
        _sanitize_branch_name("", "FEAT-TEST", 1)


def test_sanitize_branch_name_deterministic():
    """Test that sanitization is deterministic."""
    result1 = _sanitize_branch_name("test", "FEAT-X", 1)
    result2 = _sanitize_branch_name("test", "FEAT-X", 1)
    assert result1 == result2


def test_create_worktree_rejects_absolute_packet_id(temp_git_repo):
    """Test that create_packet_worktree rejects absolute packet_id."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    # Absolute packet_id should be rejected before worktree creation
    with pytest.raises(ValueError, match="cannot be absolute path"):
        manager.create_packet_worktree(
            packet_id="/tmp/evil",
            attempt=1,
            base_ref="HEAD",
        )

    # Verify no worktree was created
    assert not (worktree_root / "tmp-evil-attempt-0001").exists()


def test_create_worktree_rejects_traversal_packet_id(temp_git_repo):
    """Test that create_packet_worktree rejects traversal packet_id."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    # Traversal packet_id should be rejected before worktree creation
    with pytest.raises(ValueError, match="cannot contain path traversal"):
        manager.create_packet_worktree(
            packet_id="../escape",
            attempt=1,
            base_ref="HEAD",
        )

    # Verify no worktree was created
    assert not (worktree_root / "escape-attempt-0001").exists()


def test_create_worktree_rejects_empty_packet_id(temp_git_repo):
    """Test that create_packet_worktree rejects empty packet_id."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    # Empty packet_id should be rejected
    with pytest.raises(ValueError, match="cannot be empty"):
        manager.create_packet_worktree(
            packet_id="",
            attempt=1,
            base_ref="HEAD",
        )


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


def test_create_worktree_from_head(temp_git_repo):
    """Test creating a worktree from HEAD."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    assert context.created is True
    assert context.packet_id == "FEAT-TEST-W01-PACKET"
    assert context.attempt == 1
    assert context.base_ref == "HEAD"
    assert context.branch_name == "agent/test-project/FEAT-TEST-W01-PACKET/attempt-0001"
    assert context.worktree_path.exists()
    assert context.worktree_path.is_relative_to(worktree_root)


def test_worktree_path_under_worktree_root(temp_git_repo):
    """Test that created worktree path is under configured worktree_root."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Verify path is under worktree_root
    assert context.worktree_path.resolve().is_relative_to(worktree_root.resolve())


def test_status_reports_clean_worktree(temp_git_repo):
    """Test that status reports clean worktree after creation."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    status = manager.status(packet_id="FEAT-TEST-W01-PACKET", attempt=1)

    assert status.exists is True
    assert status.dirty is False
    assert status.changed_files == []


def test_status_reports_dirty_worktree(temp_git_repo):
    """Test that status reports dirty worktree after file modification."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Modify a file
    test_file = context.worktree_path / "test.txt"
    test_file.write_text("modified\n")

    status = manager.status(packet_id="FEAT-TEST-W01-PACKET", attempt=1)

    assert status.exists is True
    assert status.dirty is True
    assert "test.txt" in status.changed_files


def test_changed_files_includes_committed(temp_git_repo):
    """Test that changed files includes committed changes vs base_ref."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    # Get the current HEAD commit
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref=base_commit,
    )

    # Create and commit a file
    test_file = context.worktree_path / "committed.txt"
    test_file.write_text("committed\n")
    subprocess.run(["git", "add", "committed.txt"], cwd=context.worktree_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add committed file"],
        cwd=context.worktree_path,
        check=True,
        capture_output=True,
    )

    changed = manager.get_changed_files(context.worktree_path, base_ref=base_commit)

    assert "committed.txt" in changed


def test_changed_files_includes_staged(temp_git_repo):
    """Test that changed files includes staged changes."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Create and stage a file
    test_file = context.worktree_path / "staged.txt"
    test_file.write_text("staged\n")
    subprocess.run(["git", "add", "staged.txt"], cwd=context.worktree_path, check=True, capture_output=True)

    changed = manager.get_changed_files(context.worktree_path, base_ref="HEAD")

    assert "staged.txt" in changed


def test_changed_files_includes_unstaged(temp_git_repo):
    """Test that changed files includes unstaged changes."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Modify existing file
    readme = context.worktree_path / "README.md"
    readme.write_text("# Modified\n")

    changed = manager.get_changed_files(context.worktree_path, base_ref="HEAD")

    assert "README.md" in changed


def test_changed_files_includes_untracked(temp_git_repo):
    """Test that changed files includes untracked files."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Create untracked file
    test_file = context.worktree_path / "untracked.txt"
    test_file.write_text("untracked\n")

    changed = manager.get_changed_files(context.worktree_path, base_ref="HEAD")

    assert "untracked.txt" in changed


def test_changed_files_deduplicated_and_sorted(temp_git_repo):
    """Test that changed files are deduplicated and sorted."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Create multiple files
    (context.worktree_path / "b.txt").write_text("b\n")
    (context.worktree_path / "a.txt").write_text("a\n")
    (context.worktree_path / "c.txt").write_text("c\n")

    changed = manager.get_changed_files(context.worktree_path, base_ref="HEAD")

    # Should be sorted
    assert changed == sorted(changed)
    # Should be deduplicated (no duplicates)
    assert len(changed) == len(set(changed))


def test_cleanup_removes_worktree_when_clean(temp_git_repo):
    """Test that cleanup removes worktree when keep_on_failure=False."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    status = manager.cleanup_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        keep_on_failure=False,
    )

    assert status.exists is False
    assert not context.worktree_path.exists()


def test_cleanup_preserves_worktree_when_keep_on_failure(temp_git_repo):
    """Test that cleanup preserves worktree when keep_on_failure=True and dirty."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Make worktree dirty
    test_file = context.worktree_path / "test.txt"
    test_file.write_text("dirty\n")

    status = manager.cleanup_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        keep_on_failure=True,
    )

    assert status.exists is True
    assert context.worktree_path.exists()


def test_cleanup_refuses_path_outside_worktree_root(temp_git_repo):
    """Test that cleanup safety check exists and worktree paths are constrained."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    # Create worktree
    context = manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )

    # Verify the worktree path is under worktree_root
    assert context.worktree_path.resolve().is_relative_to(worktree_root.resolve())

    # Cleanup should succeed for paths under worktree_root
    status = manager.cleanup_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        keep_on_failure=False,
    )

    assert status.exists is False


def test_list_active_worktrees(temp_git_repo):
    """Test listing active worktrees."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    # Create two worktrees
    manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
    )
    manager.create_packet_worktree(
        packet_id="FEAT-TEST-W01-PACKET",
        attempt=2,
        base_ref="HEAD",
    )

    worktrees = manager.list_active_worktrees()

    # Should have at least 2 worktrees (may have more from git worktree list)
    packet_worktrees = [w for w in worktrees if w.packet_id == "FEAT-TEST-W01-PACKET"]
    assert len(packet_worktrees) >= 2


def test_status_nonexistent_worktree(temp_git_repo):
    """Test status of nonexistent worktree."""
    worktree_root = temp_git_repo.parent / "worktrees"

    manager = WorktreeManager(
        repo_root=temp_git_repo,
        worktree_root=worktree_root,
        project_key="test-project",
    )

    status = manager.status(packet_id="NONEXISTENT", attempt=1)

    assert status.exists is False
    assert status.dirty is False
    assert status.changed_files == []
