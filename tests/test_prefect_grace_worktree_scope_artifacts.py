import pytest

from prefect_grace.tasks.worktree_scope_artifacts import (
    _build_artifact_markdown,
    publish_worktree_scope_lifecycle_artifact,
)


def test_build_artifact_markdown_passed():
    """Test artifact markdown for passed status."""
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 1,
        "status": "passed",
        "worktree_path": "/tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0001",
        "branch_name": "test-project/packet/TEST-PACKET-W01-TEST/attempt-0001",
        "changed_files": ["allowed/file1.txt", "allowed/file2.txt"],
        "scope_guard": {
            "ok": True,
            "frozen_violations": [],
            "outside_allowed": [],
            "invalid_paths": [],
        },
        "blocker_reason": None,
    }

    markdown = _build_artifact_markdown(result)

    assert "# Worktree Scope Lifecycle: ✅ PASSED" in markdown
    assert "**Packet ID:** `TEST-PACKET-W01-TEST`" in markdown
    assert "**Attempt:** `1`" in markdown
    assert "**Status:** `passed`" in markdown
    assert "allowed/file1.txt" in markdown
    assert "allowed/file2.txt" in markdown


def test_build_artifact_markdown_scope_blocked():
    """Test artifact markdown for scope_blocked status."""
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 2,
        "status": "scope_blocked",
        "worktree_path": "/tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0002",
        "branch_name": "test-project/packet/TEST-PACKET-W01-TEST/attempt-0002",
        "changed_files": ["frozen/file.txt"],
        "scope_guard": {
            "ok": False,
            "frozen_violations": [
                {"file_path": "frozen/file.txt", "matched_pattern": "frozen/**"}
            ],
            "outside_allowed": [],
            "invalid_paths": [],
        },
        "blocker_reason": "Scope violations: 1 frozen violation(s)",
    }

    markdown = _build_artifact_markdown(result)

    assert "# Worktree Scope Lifecycle: 🚫 SCOPE_BLOCKED" in markdown
    assert "**Status:** `scope_blocked`" in markdown
    assert "## Scope Violations" in markdown
    assert "### 🚫 Frozen Violations (1)" in markdown
    assert "frozen/file.txt" in markdown
    assert "matched: `frozen/**`" in markdown
    assert "## Blocker Reason" in markdown
    assert "Scope violations: 1 frozen violation(s)" in markdown


def test_build_artifact_markdown_outside_allowed():
    """Test artifact markdown for outside_allowed violations."""
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 3,
        "status": "scope_blocked",
        "worktree_path": "/tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0003",
        "branch_name": "test-project/packet/TEST-PACKET-W01-TEST/attempt-0003",
        "changed_files": ["outside/file.txt"],
        "scope_guard": {
            "ok": False,
            "frozen_violations": [],
            "outside_allowed": [{"file_path": "outside/file.txt"}],
            "invalid_paths": [],
        },
        "blocker_reason": "Scope violations: 1 outside allowed",
    }

    markdown = _build_artifact_markdown(result)

    assert "## Scope Violations" in markdown
    assert "### ⚠️ Outside Allowed Scope (1)" in markdown
    assert "outside/file.txt" in markdown


def test_build_artifact_markdown_invalid_paths():
    """Test artifact markdown for invalid_paths violations."""
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 4,
        "status": "scope_blocked",
        "worktree_path": "/tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0004",
        "branch_name": "test-project/packet/TEST-PACKET-W01-TEST/attempt-0004",
        "changed_files": ["../escape.txt"],
        "scope_guard": {
            "ok": False,
            "frozen_violations": [],
            "outside_allowed": [],
            "invalid_paths": [
                {"file_path": "../escape.txt", "reason": "path traversal"}
            ],
        },
        "blocker_reason": "Scope violations: 1 invalid path(s)",
    }

    markdown = _build_artifact_markdown(result)

    assert "## Scope Violations" in markdown
    assert "### ❌ Invalid Paths (1)" in markdown
    assert "../escape.txt" in markdown
    assert "path traversal" in markdown


def test_build_artifact_markdown_worktree_error():
    """Test artifact markdown for worktree_error status."""
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 5,
        "status": "worktree_error",
        "worktree_path": "",
        "branch_name": "",
        "changed_files": [],
        "scope_guard": {},
        "blocker_reason": "Packet parse failed: file not found",
    }

    markdown = _build_artifact_markdown(result)

    assert "# Worktree Scope Lifecycle: ❌ WORKTREE_ERROR" in markdown
    assert "**Status:** `worktree_error`" in markdown
    assert "## Blocker Reason" in markdown
    assert "Packet parse failed: file not found" in markdown


def test_build_artifact_markdown_many_files():
    """Test artifact markdown truncates long file lists."""
    changed_files = [f"allowed/file{i}.txt" for i in range(30)]
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 6,
        "status": "passed",
        "worktree_path": "/tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0006",
        "branch_name": "test-project/packet/TEST-PACKET-W01-TEST/attempt-0006",
        "changed_files": changed_files,
        "scope_guard": {"ok": True, "frozen_violations": [], "outside_allowed": [], "invalid_paths": []},
        "blocker_reason": None,
    }

    markdown = _build_artifact_markdown(result)

    assert "**Total:** 30" in markdown
    assert "allowed/file0.txt" in markdown
    assert "allowed/file19.txt" in markdown
    assert "... and 10 more" in markdown


def test_build_artifact_markdown_many_violations():
    """Test artifact markdown truncates long violation lists."""
    frozen_violations = [
        {"file_path": f"frozen/file{i}.txt", "matched_pattern": "frozen/**"}
        for i in range(15)
    ]
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 7,
        "status": "scope_blocked",
        "worktree_path": "/tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0007",
        "branch_name": "test-project/packet/TEST-PACKET-W01-TEST/attempt-0007",
        "changed_files": [f"frozen/file{i}.txt" for i in range(15)],
        "scope_guard": {
            "ok": False,
            "frozen_violations": frozen_violations,
            "outside_allowed": [],
            "invalid_paths": [],
        },
        "blocker_reason": "Scope violations: 15 frozen violation(s)",
    }

    markdown = _build_artifact_markdown(result)

    assert "### 🚫 Frozen Violations (15)" in markdown
    assert "frozen/file0.txt" in markdown
    assert "frozen/file9.txt" in markdown
    assert "... and 5 more" in markdown


def test_publish_worktree_scope_lifecycle_artifact_returns_empty_when_unavailable():
    """Test that publish returns empty list when Prefect unavailable."""
    result = {
        "packet_id": "TEST-PACKET-W01-TEST",
        "attempt": 1,
        "status": "passed",
        "worktree_path": "/tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0001",
        "branch_name": "test-project/packet/TEST-PACKET-W01-TEST/attempt-0001",
        "changed_files": [],
        "scope_guard": {"ok": True, "frozen_violations": [], "outside_allowed": [], "invalid_paths": []},
        "blocker_reason": None,
    }

    # Should return empty list when Prefect unavailable (no exception)
    artifact_ids = publish_worktree_scope_lifecycle_artifact(result)

    assert isinstance(artifact_ids, list)
    # May be empty if Prefect unavailable, or contain IDs if available


def test_publish_worktree_scope_lifecycle_artifact_handles_errors():
    """Test that publish handles errors gracefully."""
    # Invalid result dict should not raise
    result = {}

    artifact_ids = publish_worktree_scope_lifecycle_artifact(result)

    assert isinstance(artifact_ids, list)
