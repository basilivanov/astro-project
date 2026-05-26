"""
Tests for managed packet runner integration with executor registry.

Validates executor selection, recording, and fail-closed behavior.
"""

import pytest
from pathlib import Path
from prefect_grace.platform.executor_registry import select_executor_for_packet, record_executor_attempt
from prefect_grace.platform.project_adapter import ProjectAdapterConfig, AgentExecutorConfig, PrefectConfig
from prefect_grace.platform.state_store import ExecutorHistoryStore
from prefect_grace.platform.managed_packet_runner import run_managed_packet


def _create_minimal_packet_file(tmp_path):
    """Create a minimal valid packet file for testing."""
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Execution Packet: Test Packet

## Objective
Test packet for executor registry integration.

## Slice
- packet_id: TEST-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01

## Must Preserve
- No changes to frozen scope

## Allowed Write Scope
- test/**

## Frozen Scope
- frozen/**

## Verification
Run tests.

## Expected Evidence
- Test output

## Escalation Triggers
- None
""")
    return packet_file


def _init_git_repo(repo_root):
    """Initialize a git repo with main branch."""
    import subprocess
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=repo_root, check=True, capture_output=True)


def test_managed_runner_backward_compatible(tmp_path):
    """Verify managed runner works without project parameter."""
    packet_file = _create_minimal_packet_file(tmp_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    # Mock launcher
    def fake_launcher(packet_id, **kwargs):
        return {
            "packet_id": packet_id,
            "returncode": 0,
            "termination_reason": "completed",
        }

    # Run without project parameter (backward compatible)
    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET",
        attempt=1,
        base_ref="main",
        dry_run=True,
        execute_agent=False,
        launcher=fake_launcher,
        project=None,  # No project = backward compatible mode
    )

    # Should work without executor selection
    assert result.ok is True or result.domain_status in ["passed", "scope_blocked"]


def test_managed_runner_selects_executor(tmp_path):
    """Verify managed runner selects executor from project config."""
    packet_file = _create_minimal_packet_file(tmp_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    state_root = tmp_path / "state"
    state_root.mkdir()

    # Create project config
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root=str(repo_root),
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root=str(state_root),
        artifact_root=str(state_root / "artifacts"),
        worktree_root=str(worktree_root),
        workflow_runtime="prefect",
        prefect=PrefectConfig(
            work_pool="test-pool",
            live_queue="test-live",
            monitoring_queue="test-monitoring",
        ),
        agent_executor=AgentExecutorConfig(
            default="codex-cli",
            command="codex1",
            executors=[
                {
                    "executor_id": "test-executor",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                },
            ],
        ),
    )

    # Mock launcher
    def fake_launcher(packet_id, **kwargs):
        return {
            "packet_id": packet_id,
            "returncode": 0,
            "termination_reason": "completed",
        }

    # Run with project parameter
    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET",
        attempt=1,
        base_ref="main",
        dry_run=True,
        execute_agent=False,
        launcher=fake_launcher,
        project=project,
    )

    # Should select executor and include metadata
    assert "executor_id" in result.agent_result
    assert result.agent_result["executor_id"] == "test-executor"
    assert result.agent_result["executor_kind"] == "codex"


def test_managed_runner_records_executor_attempt(tmp_path):
    """Verify managed runner records executor attempt to history store."""
    packet_file = _create_minimal_packet_file(tmp_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    state_root = tmp_path / "state"
    state_root.mkdir()

    # Create project config
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root=str(repo_root),
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root=str(state_root),
        artifact_root=str(state_root / "artifacts"),
        worktree_root=str(worktree_root),
        workflow_runtime="prefect",
        prefect=PrefectConfig(
            work_pool="test-pool",
            live_queue="test-live",
            monitoring_queue="test-monitoring",
        ),
        agent_executor=AgentExecutorConfig(
            default="codex-cli",
            command="codex1",
            executors=None,  # Use backward compatible mode
        ),
    )

    # Mock launcher
    def fake_launcher(packet_id, **kwargs):
        return {
            "packet_id": packet_id,
            "returncode": 0,
            "termination_reason": "completed",
        }

    # Run with project parameter
    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET",
        attempt=1,
        base_ref="main",
        dry_run=True,
        execute_agent=False,
        launcher=fake_launcher,
        project=project,
    )

    # Verify history was recorded
    history_store = ExecutorHistoryStore(state_root)
    history = history_store.list_executions()
    assert len(history) == 1
    assert history[0]["packet_id"] == "TEST-PACKET"
    assert history[0]["executor_id"] == "codex-cli"


def test_managed_runner_unsupported_kind_fails_closed(tmp_path):
    """Verify unsupported executor kinds return runner_error."""
    packet_file = _create_minimal_packet_file(tmp_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    state_root = tmp_path / "state"
    state_root.mkdir()

    # Create project config with unsupported executor kind
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root=str(repo_root),
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root=str(state_root),
        artifact_root=str(state_root / "artifacts"),
        worktree_root=str(worktree_root),
        workflow_runtime="prefect",
        prefect=PrefectConfig(
            work_pool="test-pool",
            live_queue="test-live",
            monitoring_queue="test-monitoring",
        ),
        agent_executor=AgentExecutorConfig(
            default="claude-sonnet",
            command="claude",
            executors=[
                {
                    "executor_id": "claude-sonnet",
                    "kind": "claude",  # Unsupported kind
                    "command": "claude",
                    "enabled": True,
                },
            ],
        ),
    )

    # Mock launcher (should not be called)
    def fake_launcher(packet_id, **kwargs):
        raise AssertionError("Launcher should not be called for unsupported kind")

    # Run with unsupported executor
    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET",
        attempt=1,
        base_ref="main",
        dry_run=True,
        execute_agent=False,
        launcher=fake_launcher,
        project=project,
    )

    # Should fail closed with runner_error
    assert result.ok is False
    assert result.domain_status == "runner_error"
    assert "unsupported_executor_kind:claude" in result.blocker_reason


def test_managed_runner_no_executor_available(tmp_path):
    """Verify runner_error when no executor available."""
    packet_file = _create_minimal_packet_file(tmp_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    state_root = tmp_path / "state"
    state_root.mkdir()

    # Create project config with role-incompatible executor
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root=str(repo_root),
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root=str(state_root),
        artifact_root=str(state_root / "artifacts"),
        worktree_root=str(worktree_root),
        workflow_runtime="prefect",
        prefect=PrefectConfig(
            work_pool="test-pool",
            live_queue="test-live",
            monitoring_queue="test-monitoring",
        ),
        agent_executor=AgentExecutorConfig(
            default="codex-reviewer",
            command="codex1",
            executors=[
                {
                    "executor_id": "codex-reviewer",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "roles": ["reviewer"],  # Only reviewer role
                },
            ],
        ),
    )

    # Mock launcher (should not be called)
    def fake_launcher(packet_id, **kwargs):
        raise AssertionError("Launcher should not be called when no executor available")

    # Run with coder role (no compatible executor)
    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET",
        attempt=1,
        base_ref="main",
        dry_run=True,
        execute_agent=False,
        launcher=fake_launcher,
        project=project,
    )

    # Should fail with no_executor_available
    assert result.ok is False
    assert result.domain_status == "runner_error"
    assert "no_executor_available" in result.blocker_reason


def test_managed_runner_mock_executor_with_injected_launcher(tmp_path):
    """Verify mock executor kind works with injected launcher."""
    packet_file = _create_minimal_packet_file(tmp_path)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    worktree_root = tmp_path / "worktrees"
    worktree_root.mkdir()

    state_root = tmp_path / "state"
    state_root.mkdir()

    # Create project config with mock executor
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root=str(repo_root),
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root=str(state_root),
        artifact_root=str(state_root / "artifacts"),
        worktree_root=str(worktree_root),
        workflow_runtime="prefect",
        prefect=PrefectConfig(
            work_pool="test-pool",
            live_queue="test-live",
            monitoring_queue="test-monitoring",
        ),
        agent_executor=AgentExecutorConfig(
            default="mock-executor",
            command="mock",
            executors=[
                {
                    "executor_id": "mock-executor",
                    "kind": "mock",
                    "command": "mock",
                    "enabled": True,
                },
            ],
        ),
    )

    # Mock launcher for mock executor
    def fake_launcher(packet_id, **kwargs):
        return {
            "packet_id": packet_id,
            "returncode": 0,
            "termination_reason": "completed",
        }

    # Run with mock executor
    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-PACKET",
        attempt=1,
        base_ref="main",
        dry_run=True,
        execute_agent=False,
        launcher=fake_launcher,
        project=project,
    )

    # Should work with mock executor
    assert result.agent_result["executor_id"] == "mock-executor"
    assert result.agent_result["executor_kind"] == "mock"
