"""Unit tests for prefect_grace.platform.scope_guard module."""

from pathlib import Path

import pytest

from prefect_grace.platform.scope_guard import (
    ScopeGuardResult,
    ScopeGuardViolation,
    validate_scope,
    _normalize_path,
    _matches_pattern,
)


def test_exact_allowed_file_passes(tmp_path):
    """Test exact file match in allowed scope passes."""
    result = validate_scope(
        changed_files=["prefect_grace/cli.py"],
        allowed_scope=["prefect_grace/cli.py"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1
    assert result.allowed_files[0] == "prefect_grace/cli.py"
    assert len(result.frozen_violations) == 0
    assert len(result.outside_allowed) == 0


def test_directory_glob_allowed_passes(tmp_path):
    """Test directory glob pattern matches."""
    result = validate_scope(
        changed_files=["prefect_grace/platform/scope_guard.py"],
        allowed_scope=["prefect_grace/platform/**"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1
    assert result.allowed_files[0] == "prefect_grace/platform/scope_guard.py"


def test_file_glob_allowed_passes(tmp_path):
    """Test file glob pattern matches."""
    result = validate_scope(
        changed_files=["prefect_grace/platform/scope_guard.py"],
        allowed_scope=["prefect_grace/platform/*.py"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1


def test_nested_glob_allowed_passes(tmp_path):
    """Test nested glob pattern matches."""
    result = validate_scope(
        changed_files=["prefect_grace/platform/subdir/file.py"],
        allowed_scope=["prefect_grace/**/*.py"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1


def test_frozen_blocks_even_when_allowed(tmp_path):
    """Test frozen scope wins over allowed scope."""
    result = validate_scope(
        changed_files=["prefect_grace/platform/state_store.py"],
        allowed_scope=["prefect_grace/platform/**"],
        frozen_scope=["prefect_grace/platform/state_store.py"],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.frozen_violations) == 1
    assert result.frozen_violations[0].file_path == "prefect_grace/platform/state_store.py"
    assert result.frozen_violations[0].matched_pattern == "prefect_grace/platform/state_store.py"
    assert len(result.allowed_files) == 0


def test_outside_allowed_blocks(tmp_path):
    """Test file outside allowed scope is blocked."""
    result = validate_scope(
        changed_files=["backend/app/main.py"],
        allowed_scope=["prefect_grace/platform/**"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.outside_allowed) == 1
    assert result.outside_allowed[0].file_path == "backend/app/main.py"
    assert result.outside_allowed[0].reason == "File is outside allowed write scope"


def test_empty_allowed_blocks_all(tmp_path):
    """Test empty allowed scope blocks all files."""
    result = validate_scope(
        changed_files=["prefect_grace/cli.py"],
        allowed_scope=[],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.outside_allowed) == 1
    assert result.outside_allowed[0].reason == "Allowed write scope is empty"


def test_path_traversal_blocks(tmp_path):
    """Test path traversal is rejected."""
    result = validate_scope(
        changed_files=["../secret"],
        allowed_scope=["**"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.invalid_paths) == 1
    assert result.invalid_paths[0].file_path == "../secret"


def test_absolute_outside_repo_blocks(tmp_path):
    """Test absolute path outside repo is rejected."""
    result = validate_scope(
        changed_files=["/etc/passwd"],
        allowed_scope=["**"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.invalid_paths) == 1


def test_absolute_inside_repo_normalizes(tmp_path):
    """Test absolute path inside repo normalizes correctly."""
    test_file = tmp_path / "prefect_grace" / "cli.py"
    result = validate_scope(
        changed_files=[str(test_file)],
        allowed_scope=["prefect_grace/cli.py"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1
    assert result.allowed_files[0] == "prefect_grace/cli.py"


def test_deleted_file_checked_by_path(tmp_path):
    """Test nonexistent file is still validated by path."""
    result = validate_scope(
        changed_files=["prefect_grace/deleted_file.py"],
        allowed_scope=["prefect_grace/**"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1


def test_deterministic_output_ordering(tmp_path):
    """Test results are sorted consistently."""
    result = validate_scope(
        changed_files=["z.py", "a.py", "m.py"],
        allowed_scope=["*.py"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert result.changed_files == ["a.py", "m.py", "z.py"]
    assert result.allowed_files == ["a.py", "m.py", "z.py"]


def test_repeated_slashes_normalized(tmp_path):
    """Test repeated slashes are normalized."""
    result = validate_scope(
        changed_files=["prefect_grace//cli.py"],
        allowed_scope=["prefect_grace/cli.py"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1


def test_dot_slash_normalized(tmp_path):
    """Test ./path is normalized."""
    result = validate_scope(
        changed_files=["./prefect_grace/cli.py"],
        allowed_scope=["prefect_grace/cli.py"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is True
    assert len(result.allowed_files) == 1


def test_empty_path_rejected(tmp_path):
    """Test empty path is rejected."""
    result = validate_scope(
        changed_files=[""],
        allowed_scope=["**"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.invalid_paths) == 1


def test_nul_byte_rejected(tmp_path):
    """Test path with NUL byte is rejected."""
    result = validate_scope(
        changed_files=["file\0.py"],
        allowed_scope=["**"],
        frozen_scope=[],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.invalid_paths) == 1


def test_to_dict_serialization(tmp_path):
    """Test ScopeGuardResult.to_dict() produces JSON-safe output."""
    result = validate_scope(
        changed_files=["backend/app/main.py"],
        allowed_scope=["prefect_grace/**"],
        frozen_scope=["backend/**"],
        repo_root=tmp_path,
    )
    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert result_dict["ok"] is False
    assert isinstance(result_dict["changed_files"], list)
    assert isinstance(result_dict["frozen_violations"], list)
    assert len(result_dict["frozen_violations"]) == 1
    assert result_dict["frozen_violations"][0]["file_path"] == "backend/app/main.py"
    assert result_dict["frozen_violations"][0]["matched_pattern"] == "backend/**"


def test_normalize_path_helper(tmp_path):
    """Test _normalize_path helper function."""
    # Valid relative path
    assert _normalize_path("prefect_grace/cli.py", tmp_path) == "prefect_grace/cli.py"

    # Valid absolute path inside repo
    test_file = tmp_path / "test.py"
    assert _normalize_path(str(test_file), tmp_path) == "test.py"

    # Invalid: outside repo
    assert _normalize_path("/etc/passwd", tmp_path) is None

    # Invalid: empty
    assert _normalize_path("", tmp_path) is None

    # Invalid: NUL byte
    assert _normalize_path("file\0.py", tmp_path) is None


def test_matches_pattern_helper():
    """Test _matches_pattern helper function."""
    # Exact match
    assert _matches_pattern("prefect_grace/cli.py", "prefect_grace/cli.py") is True
    assert _matches_pattern("prefect_grace/cli.py", "prefect_grace/other.py") is False

    # Directory glob
    assert _matches_pattern("prefect_grace/platform/scope_guard.py", "prefect_grace/platform/**") is True
    assert _matches_pattern("prefect_grace/cli.py", "prefect_grace/platform/**") is False

    # File glob
    assert _matches_pattern("prefect_grace/cli.py", "prefect_grace/*.py") is True
    assert _matches_pattern("prefect_grace/platform/scope_guard.py", "prefect_grace/*.py") is False

    # Nested glob
    assert _matches_pattern("prefect_grace/platform/scope_guard.py", "prefect_grace/**/*.py") is True
    assert _matches_pattern("prefect_grace/cli.py", "prefect_grace/**/*.py") is True


def test_multiple_violations(tmp_path):
    """Test multiple violations are reported correctly."""
    result = validate_scope(
        changed_files=[
            "backend/app/main.py",
            "frontend/src/App.tsx",
            "prefect_grace/platform/state_store.py",
            "scripts/deploy.sh",
        ],
        allowed_scope=["prefect_grace/platform/**"],
        frozen_scope=["prefect_grace/platform/state_store.py", "backend/**", "frontend/**"],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.frozen_violations) == 3
    assert len(result.outside_allowed) == 1
    assert result.outside_allowed[0].file_path == "scripts/deploy.sh"


def test_frozen_glob_pattern(tmp_path):
    """Test frozen scope with glob pattern."""
    result = validate_scope(
        changed_files=["backend/app/main.py", "backend/app/models.py"],
        allowed_scope=["backend/**"],
        frozen_scope=["backend/**"],
        repo_root=tmp_path,
    )
    assert result.ok is False
    assert len(result.frozen_violations) == 2
    assert all(v.matched_pattern == "backend/**" for v in result.frozen_violations)

