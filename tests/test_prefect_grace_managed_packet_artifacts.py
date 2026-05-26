"""
Tests for managed_packet_artifacts module.

Verifies artifact publication for managed packet runs.
"""

from prefect_grace.tasks.managed_packet_artifacts import (
    publish_managed_packet_run_artifact,
    _build_artifact_markdown,
    _get_create_markdown_artifact,
)


def test_get_create_markdown_artifact_returns_none_when_prefect_unavailable(monkeypatch):
    """Verify _get_create_markdown_artifact returns None when Prefect unavailable."""
    # Mock importlib.import_module to raise ImportError
    import importlib
    original_import = importlib.import_module

    def mock_import(name):
        if name == "prefect.artifacts":
            raise ImportError("Prefect not available")
        return original_import(name)

    monkeypatch.setattr(importlib, "import_module", mock_import)

    result = _get_create_markdown_artifact()
    assert result is None


def test_build_artifact_markdown_passed_status():
    """Verify artifact markdown for passed status."""
    result = {
        "ok": True,
        "domain_status": "passed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": ["file1.py", "file2.py"],
        "agent_result": {
            "returncode": 0,
            "termination_reason": "completed",
            "session_mode": "exec",
            "thread_id": "thread-123",
        },
        "lifecycle_result": {
            "status": "passed",
        },
        "scope_guard": {},
        "blocker_reason": None,
    }

    markdown = _build_artifact_markdown(result)

    assert "# Managed Packet Run: ✅ PASSED" in markdown
    assert "**Packet ID:** `TEST-PACKET`" in markdown
    assert "**Attempt:** `1`" in markdown
    assert "**Domain Status:** `passed`" in markdown
    assert "**Path:** `/tmp/worktree`" in markdown
    assert "**Branch:** `test-branch`" in markdown
    assert "**Total:** 2" in markdown
    assert "- `file1.py`" in markdown
    assert "- `file2.py`" in markdown
    assert "**Return Code:** `0`" in markdown
    assert "**Termination Reason:** `completed`" in markdown
    assert "**Session Mode:** `exec`" in markdown
    assert "**Thread ID:** `thread-123`" in markdown


def test_build_artifact_markdown_scope_blocked_status():
    """Verify artifact markdown for scope_blocked status."""
    result = {
        "ok": False,
        "domain_status": "scope_blocked",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": ["frozen.py", "outside.py"],
        "agent_result": {
            "returncode": 0,
            "termination_reason": "completed",
        },
        "lifecycle_result": {
            "status": "scope_blocked",
        },
        "scope_guard": {
            "frozen_violations": [
                {"file_path": "frozen.py", "matched_pattern": "frozen/**"},
            ],
            "outside_allowed": [
                {"file_path": "outside.py"},
            ],
            "invalid_paths": [],
        },
        "blocker_reason": "Scope violations detected",
    }

    markdown = _build_artifact_markdown(result)

    assert "# Managed Packet Run: 🚫 SCOPE_BLOCKED" in markdown
    assert "**Domain Status:** `scope_blocked`" in markdown
    assert "## Scope Violations" in markdown
    assert "### 🚫 Frozen Violations (1)" in markdown
    assert "- `frozen.py` (matched: `frozen/**`)" in markdown
    assert "### ⚠️ Outside Allowed Scope (1)" in markdown
    assert "- `outside.py`" in markdown
    assert "## Blocker Reason" in markdown
    assert "Scope violations detected" in markdown


def test_build_artifact_markdown_agent_failed_status():
    """Verify artifact markdown for agent_failed status."""
    result = {
        "ok": False,
        "domain_status": "agent_failed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": [],
        "agent_result": {
            "returncode": 1,
            "termination_reason": "stall_killed",
        },
        "lifecycle_result": {
            "status": "passed",
        },
        "scope_guard": {},
        "blocker_reason": "Agent failed: returncode=1",
    }

    markdown = _build_artifact_markdown(result)

    assert "# Managed Packet Run: ❌ AGENT_FAILED" in markdown
    assert "**Domain Status:** `agent_failed`" in markdown
    assert "**Return Code:** `1`" in markdown
    assert "**Termination Reason:** `stall_killed`" in markdown
    assert "Agent failed: returncode=1" in markdown


def test_build_artifact_markdown_runner_error_status():
    """Verify artifact markdown for runner_error status."""
    result = {
        "ok": False,
        "domain_status": "runner_error",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "",
        "branch_name": "",
        "changed_files": [],
        "agent_result": {},
        "lifecycle_result": {},
        "scope_guard": {},
        "blocker_reason": "Worktree creation failed",
    }

    markdown = _build_artifact_markdown(result)

    assert "# Managed Packet Run: ⚠️ RUNNER_ERROR" in markdown
    assert "**Domain Status:** `runner_error`" in markdown
    assert "Worktree creation failed" in markdown


def test_build_artifact_markdown_with_run_artifacts():
    """Verify artifact markdown includes run artifacts paths."""
    result = {
        "ok": True,
        "domain_status": "passed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": [],
        "agent_result": {
            "returncode": 0,
            "termination_reason": "completed",
            "stdout_path": "/tmp/stdout.txt",
            "stderr_path": "/tmp/stderr.txt",
            "last_message_path": "/tmp/last_message.txt",
        },
        "lifecycle_result": {
            "status": "passed",
        },
        "scope_guard": {},
        "blocker_reason": None,
    }

    markdown = _build_artifact_markdown(result)

    assert "**Run Artifacts:**" in markdown
    assert "- Stdout: `/tmp/stdout.txt`" in markdown
    assert "- Stderr: `/tmp/stderr.txt`" in markdown
    assert "- Last Message: `/tmp/last_message.txt`" in markdown


def test_build_artifact_markdown_truncates_long_lists():
    """Verify artifact markdown truncates long file lists."""
    changed_files = [f"file{i}.py" for i in range(25)]
    frozen_violations = [{"file_path": f"frozen{i}.py"} for i in range(15)]

    result = {
        "ok": False,
        "domain_status": "scope_blocked",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": changed_files,
        "agent_result": {},
        "lifecycle_result": {
            "status": "scope_blocked",
        },
        "scope_guard": {
            "frozen_violations": frozen_violations,
            "outside_allowed": [],
            "invalid_paths": [],
        },
        "blocker_reason": None,
    }

    markdown = _build_artifact_markdown(result)

    # Changed files truncated at 20
    assert "- `file19.py`" in markdown
    assert "- ... and 5 more" in markdown

    # Frozen violations truncated at 10
    assert "- `frozen9.py`" in markdown
    assert "- ... and 5 more" in markdown


def test_publish_managed_packet_run_artifact_returns_empty_when_prefect_unavailable(monkeypatch):
    """Verify publish returns empty list when Prefect unavailable."""
    # Mock _get_create_markdown_artifact to return None
    import prefect_grace.tasks.managed_packet_artifacts as module
    monkeypatch.setattr(module, "_get_create_markdown_artifact", lambda: None)

    result = {
        "ok": True,
        "domain_status": "passed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": [],
        "agent_result": {},
        "lifecycle_result": {},
        "scope_guard": {},
        "blocker_reason": None,
    }

    artifact_ids = publish_managed_packet_run_artifact(result)
    assert artifact_ids == []


def test_publish_managed_packet_run_artifact_returns_empty_on_exception(monkeypatch):
    """Verify publish returns empty list on exception."""
    # Mock _get_create_markdown_artifact to return a function that raises
    def mock_create_artifact(**kwargs):
        raise RuntimeError("Artifact creation failed")

    import prefect_grace.tasks.managed_packet_artifacts as module
    monkeypatch.setattr(module, "_get_create_markdown_artifact", lambda: mock_create_artifact)

    result = {
        "ok": True,
        "domain_status": "passed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": [],
        "agent_result": {},
        "lifecycle_result": {},
        "scope_guard": {},
        "blocker_reason": None,
    }

    artifact_ids = publish_managed_packet_run_artifact(result)
    assert artifact_ids == []


def test_publish_managed_packet_run_artifact_success(monkeypatch):
    """Verify publish returns artifact ID on success."""
    # Mock _get_create_markdown_artifact to return a function that returns an ID
    def mock_create_artifact(**kwargs):
        return "artifact-123"

    import prefect_grace.tasks.managed_packet_artifacts as module
    monkeypatch.setattr(module, "_get_create_markdown_artifact", lambda: mock_create_artifact)

    result = {
        "ok": True,
        "domain_status": "passed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": [],
        "agent_result": {},
        "lifecycle_result": {},
        "scope_guard": {},
        "blocker_reason": None,
    }

    artifact_ids = publish_managed_packet_run_artifact(result)
    assert artifact_ids == ["artifact-123"]


def test_publish_managed_packet_run_artifact_returns_empty_when_artifact_id_none(monkeypatch):
    """Verify publish returns empty list when artifact ID is None."""
    # Mock _get_create_markdown_artifact to return a function that returns None
    def mock_create_artifact(**kwargs):
        return None

    import prefect_grace.tasks.managed_packet_artifacts as module
    monkeypatch.setattr(module, "_get_create_markdown_artifact", lambda: mock_create_artifact)

    result = {
        "ok": True,
        "domain_status": "passed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": [],
        "agent_result": {},
        "lifecycle_result": {},
        "scope_guard": {},
        "blocker_reason": None,
    }

    artifact_ids = publish_managed_packet_run_artifact(result)
    assert artifact_ids == []
