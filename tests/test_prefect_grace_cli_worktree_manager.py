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


def test_cli_worktree_create_json(temp_git_repo):
    """Test worktree-create CLI with JSON output."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-create",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
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
    assert output["command"] == "worktree-create"
    assert output["result"]["packet_id"] == "FEAT-TEST-W01-PACKET"
    assert output["result"]["attempt"] == 1
    assert output["result"]["created"] is True
    assert "worktree_path" in output["result"]
    assert "branch_name" in output["result"]


def test_cli_worktree_create_text_mode(temp_git_repo):
    """Test worktree-create CLI with text output."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-create",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--base-ref",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Worktree created:" in result.stdout
    assert "Branch:" in result.stdout
    assert "Base ref:" in result.stdout


def test_cli_worktree_status_json(temp_git_repo):
    """Test worktree-status CLI with JSON output."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Create worktree first
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-create",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Get status
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-status",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "worktree-status"
    assert output["result"]["exists"] is True
    assert output["result"]["dirty"] is False


def test_cli_worktree_status_dirty(temp_git_repo):
    """Test worktree-status CLI reports dirty worktree."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Create worktree
    create_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-create",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    create_output = json.loads(create_result.stdout)
    worktree_path = Path(create_output["result"]["worktree_path"])

    # Make worktree dirty
    test_file = worktree_path / "test.txt"
    test_file.write_text("dirty\n")

    # Get status
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-status",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["result"]["dirty"] is True
    assert len(output["result"]["changed_files"]) > 0


def test_cli_worktree_cleanup_json(temp_git_repo):
    """Test worktree-cleanup CLI with JSON output."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Create worktree
    subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-create",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    # Cleanup
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-cleanup",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "worktree-cleanup"
    assert output["result"]["exists"] is False


def test_cli_worktree_cleanup_keep_on_failure(temp_git_repo):
    """Test worktree-cleanup CLI with --keep-on-failure flag."""
    worktree_root = temp_git_repo.parent / "worktrees"

    # Create worktree
    create_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-create",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--base-ref",
            "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    create_output = json.loads(create_result.stdout)
    worktree_path = Path(create_output["result"]["worktree_path"])

    # Make worktree dirty
    test_file = worktree_path / "test.txt"
    test_file.write_text("dirty\n")

    # Cleanup with keep-on-failure
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-cleanup",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--keep-on-failure",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["result"]["exists"] is True


def test_cli_worktree_status_nonexistent(temp_git_repo):
    """Test worktree-status CLI for nonexistent worktree."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-status",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "NONEXISTENT",
            "--attempt",
            "1",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["result"]["exists"] is False


def test_cli_worktree_create_invalid_base_ref(temp_git_repo):
    """Test worktree-create CLI with invalid base ref."""
    worktree_root = temp_git_repo.parent / "worktrees"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "worktree-create",
            "--repo-root",
            str(temp_git_repo),
            "--worktree-root",
            str(worktree_root),
            "--project-key",
            "test-project",
            "--packet-id",
            "FEAT-TEST-W01-PACKET",
            "--attempt",
            "1",
            "--base-ref",
            "INVALID-REF",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert len(output["errors"]) > 0
