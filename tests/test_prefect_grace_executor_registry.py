"""
Tests for executor registry module.

Validates executor spec loading, selection logic, rotation, and history recording.
"""

import pytest
from pathlib import Path
from prefect_grace.platform.executor_registry import (
    ExecutorSpec,
    ExecutorSelection,
    load_executor_specs,
    select_executor_for_packet,
    record_executor_attempt,
    _is_executor_failure,
    _count_consecutive_failures,
)
from prefect_grace.platform.project_adapter import ProjectAdapterConfig, AgentExecutorConfig, PrefectConfig
from prefect_grace.platform.state_store import ExecutorHistoryStore


def test_executor_spec_to_dict():
    """Verify ExecutorSpec.to_dict() serialization."""
    spec = ExecutorSpec(
        executor_id="test-executor",
        kind="codex",
        command="codex1",
        model="gpt-5.4",
        reasoning="high",
        roles=["coder", "verifier"],
        enabled=True,
        priority=100,
        max_consecutive_failures=2,
        metadata={"key": "value"},
    )

    result = spec.to_dict()

    assert result["executor_id"] == "test-executor"
    assert result["kind"] == "codex"
    assert result["command"] == "codex1"
    assert result["model"] == "gpt-5.4"
    assert result["reasoning"] == "high"
    assert result["roles"] == ["coder", "verifier"]
    assert result["enabled"] is True
    assert result["priority"] == 100
    assert result["max_consecutive_failures"] == 2
    assert result["metadata"] == {"key": "value"}


def test_executor_selection_to_dict():
    """Verify ExecutorSelection.to_dict() serialization."""
    spec = ExecutorSpec(
        executor_id="test-executor",
        kind="codex",
        command="codex1",
    )

    selection = ExecutorSelection(
        ok=True,
        packet_id="TEST-PACKET",
        role="coder",
        selected=spec,
        candidate_ids=["test-executor"],
        reason="selected",
    )

    result = selection.to_dict()

    assert result["ok"] is True
    assert result["packet_id"] == "TEST-PACKET"
    assert result["role"] == "coder"
    assert result["selected"]["executor_id"] == "test-executor"
    assert result["candidate_ids"] == ["test-executor"]
    assert result["reason"] == "selected"


def test_load_executor_specs_backward_compatible():
    """Verify backward compatibility: synthesize from legacy default/command."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
        workflow_runtime="prefect",
        prefect=PrefectConfig(
            work_pool="test-pool",
            live_queue="test-live",
            monitoring_queue="test-monitoring",
        ),
        agent_executor=AgentExecutorConfig(
            default="codex-cli",
            command="codex1",
            executors=None,
        ),
    )

    specs = load_executor_specs(project)

    assert len(specs) == 1
    assert specs[0].executor_id == "codex-cli"
    assert specs[0].kind == "codex"
    assert specs[0].command == "codex1"
    assert specs[0].enabled is True
    assert specs[0].roles == []
    assert specs[0].priority == 100
    assert specs[0].max_consecutive_failures == 2


def test_load_executor_specs_from_config():
    """Verify loading executor specs from config."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-cli",
                    "kind": "codex",
                    "command": "codex1",
                    "model": "gpt-5.4",
                    "reasoning": "high",
                    "roles": ["coder", "verifier"],
                    "enabled": True,
                    "priority": 100,
                    "max_consecutive_failures": 2,
                },
                {
                    "executor_id": "claude-sonnet",
                    "kind": "claude",
                    "command": "claude",
                    "model": "sonnet",
                    "roles": ["coder"],
                    "enabled": False,
                    "priority": 200,
                },
            ],
        ),
    )

    specs = load_executor_specs(project)

    assert len(specs) == 2
    assert specs[0].executor_id == "codex-cli"
    assert specs[0].kind == "codex"
    assert specs[0].enabled is True
    assert specs[0].roles == ["coder", "verifier"]
    assert specs[1].executor_id == "claude-sonnet"
    assert specs[1].kind == "claude"
    assert specs[1].enabled is False


def test_is_executor_failure():
    """Verify _is_executor_failure() logic."""
    # Failure: returncode != 0
    assert _is_executor_failure({"returncode": 1}) is True

    # Failure: domain_status == "agent_failed"
    assert _is_executor_failure({"domain_status": "agent_failed"}) is True

    # Failure: termination_reason in failure list
    assert _is_executor_failure({"termination_reason": "stall_killed"}) is True
    assert _is_executor_failure({"termination_reason": "timeout"}) is True
    assert _is_executor_failure({"termination_reason": "rate_limit_exceeded"}) is True

    # NOT failure: scope_blocked
    assert _is_executor_failure({"domain_status": "scope_blocked"}) is False

    # NOT failure: status == "skipped"
    assert _is_executor_failure({"status": "skipped"}) is False

    # NOT failure: returncode == 0
    assert _is_executor_failure({"returncode": 0}) is False

    # NOT failure: empty record
    assert _is_executor_failure({}) is False


def test_select_executor_default():
    """Verify default executor selection (highest priority enabled)."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-high",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 50,
                },
                {
                    "executor_id": "codex-low",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 200,
                },
            ],
        ),
    )

    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    selection = select_executor_for_packet(project=project, packet=packet, history=[])

    assert selection.ok is True
    assert selection.selected.executor_id == "codex-high"
    assert selection.reason == "selected"


def test_select_executor_requested():
    """Verify requested executor selection."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-a",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 50,
                },
                {
                    "executor_id": "codex-b",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 100,
                },
            ],
        ),
    )

    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    selection = select_executor_for_packet(
        project=project,
        packet=packet,
        history=[],
        requested_executor="codex-b",
    )

    assert selection.ok is True
    assert selection.selected.executor_id == "codex-b"
    assert selection.reason == "requested"


def test_select_executor_role_filter():
    """Verify role filtering."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-coder",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 50,
                    "roles": ["coder"],
                },
                {
                    "executor_id": "codex-reviewer",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 100,
                    "roles": ["reviewer"],
                },
            ],
        ),
    )

    # Select for coder role
    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    selection = select_executor_for_packet(project=project, packet=packet, history=[])

    assert selection.ok is True
    assert selection.selected.executor_id == "codex-coder"

    # Select for reviewer role
    packet = {"packet_id": "TEST-PACKET", "role": "reviewer"}
    selection = select_executor_for_packet(project=project, packet=packet, history=[])

    assert selection.ok is True
    assert selection.selected.executor_id == "codex-reviewer"


def test_select_executor_disabled_skipped():
    """Verify disabled executors are skipped."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-disabled",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": False,
                    "priority": 50,
                },
                {
                    "executor_id": "codex-enabled",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 100,
                },
            ],
        ),
    )

    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    selection = select_executor_for_packet(project=project, packet=packet, history=[])

    assert selection.ok is True
    assert selection.selected.executor_id == "codex-enabled"


def test_select_executor_no_candidate():
    """Verify ok=false when no executor available."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-reviewer",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "roles": ["reviewer"],
                },
            ],
        ),
    )

    # Request coder role, but only reviewer available
    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    selection = select_executor_for_packet(project=project, packet=packet, history=[])

    assert selection.ok is False
    assert selection.selected is None
    assert selection.reason == "no_executor_available"


def test_record_executor_attempt(tmp_path):
    """Verify record_executor_attempt() appends to history store."""
    state_root = tmp_path / "state"
    state_root.mkdir()

    result = {
        "feature_id": "FEAT-1",
        "wave_id": "W01",
        "source_hash": "sha256:abc123",
        "executor_kind": "codex",
        "returncode": 0,
        "termination_reason": "completed",
        "domain_status": "passed",
    }

    record = record_executor_attempt(
        state_root=state_root,
        packet_id="TEST-PACKET",
        role="coder",
        executor_id="codex-cli",
        result=result,
        attempt=1,
    )

    assert record["packet_id"] == "TEST-PACKET"
    assert record["role"] == "coder"
    assert record["executor_id"] == "codex-cli"
    assert record["attempt"] == 1
    assert record["returncode"] == 0
    assert "recorded_at" in record

    # Verify it was written to history store
    history_store = ExecutorHistoryStore(state_root)
    history = history_store.list_executions()
    assert len(history) == 1
    assert history[0]["packet_id"] == "TEST-PACKET"


def test_select_executor_rotation_after_failures():
    """Verify rotation after max_consecutive_failures."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-a",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 50,
                    "max_consecutive_failures": 2,
                },
                {
                    "executor_id": "codex-b",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 100,
                },
            ],
        ),
    )

    # History with 2 consecutive failures for codex-a
    history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:01:00Z",
        },
    ]

    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    selection = select_executor_for_packet(project=project, packet=packet, history=history)

    # Should rotate to codex-b
    assert selection.ok is True
    assert selection.selected.executor_id == "codex-b"


def test_select_executor_scope_blocked_not_failure():
    """Verify scope_blocked with nonzero returncode doesn't rotate executor."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-a",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 50,
                    "max_consecutive_failures": 2,
                },
                {
                    "executor_id": "codex-b",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 100,
                    "max_consecutive_failures": 2,
                },
            ],
        ),
    )

    # History with scope_blocked and returncode=1 should be skipped for rotation.
    history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "scope_blocked",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "scope_blocked",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:01:00Z",
        },
    ]

    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    selection = select_executor_for_packet(project=project, packet=packet, history=history)

    # Should NOT rotate to codex-b.
    assert selection.ok is True
    assert selection.selected.executor_id == "codex-a"


def test_select_executor_source_hash_filter():
    """Verify stale source_hash history doesn't rotate."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-a",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 50,
                    "max_consecutive_failures": 2,
                },
            ],
        ),
    )

    # History with failures for OLD source_hash
    history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "source_hash": "sha256:old123",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "source_hash": "sha256:old123",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:01:00Z",
        },
    ]

    # Packet with NEW source_hash
    packet = {
        "packet_id": "TEST-PACKET",
        "role": "coder",
        "source_hash": "sha256:new456",
    }
    selection = select_executor_for_packet(project=project, packet=packet, history=history)

    # Should NOT rotate, old failures don't count for new source_hash
    assert selection.ok is True
    assert selection.selected.executor_id == "codex-a"


def test_count_consecutive_failures():
    """Verify _count_consecutive_failures() logic."""
    history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:03:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 0,  # Success, stop counting
            "recorded_at": "2026-05-26T12:01:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 1,  # Older failure, should not count
            "recorded_at": "2026-05-26T12:00:00Z",
        },
    ]

    count = _count_consecutive_failures(history, "codex-a", None)

    # Should count 2 consecutive failures, stop at success
    assert count == 2


def test_count_consecutive_failures_skips_scope_blocked_nonzero_returncode():
    """Verify scope_blocked returncode=1 records do not affect streaks."""
    history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "scope_blocked",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:03:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "scope_blocked",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
    ]

    count = _count_consecutive_failures(history, "codex-a", None)

    assert count == 0


def test_count_consecutive_failures_skips_scope_blocked_without_resetting():
    """Verify scope_blocked is ignored and success still stops counting."""
    history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "scope_blocked",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:04:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "agent_failed",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:03:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 0,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "agent_failed",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:01:00Z",
        },
    ]

    count = _count_consecutive_failures(history, "codex-a", None)

    assert count == 1


def test_select_executor_mixed_scope_blocked_history_rotates_only_on_true_failures():
    """Verify scope_blocked is skipped while true failures still rotate."""
    project = ProjectAdapterConfig(
        version=1,
        project_key="test-project",
        repo_root="/opt/test",
        default_branch="main",
        grace_dir="grace",
        packets_dir="grace/packets",
        runtime_state_root="/var/lib/grace",
        artifact_root="/var/lib/grace/artifacts",
        worktree_root="/var/lib/grace/worktrees",
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
                    "executor_id": "codex-a",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 50,
                    "max_consecutive_failures": 2,
                },
                {
                    "executor_id": "codex-b",
                    "kind": "codex",
                    "command": "codex1",
                    "enabled": True,
                    "priority": 100,
                    "max_consecutive_failures": 2,
                },
            ],
        ),
    )
    packet = {"packet_id": "TEST-PACKET", "role": "coder"}
    mixed_history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "scope_blocked",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:04:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "agent_failed",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:03:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 0,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "agent_failed",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:01:00Z",
        },
    ]

    selection = select_executor_for_packet(project=project, packet=packet, history=mixed_history)

    assert selection.ok is True
    assert selection.selected.executor_id == "codex-a"

    threshold_history = [
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "scope_blocked",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:04:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "domain_status": "agent_failed",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:03:00Z",
        },
        {
            "packet_id": "TEST-PACKET",
            "role": "coder",
            "executor_id": "codex-a",
            "returncode": 1,
            "recorded_at": "2026-05-26T12:02:00Z",
        },
    ]

    selection = select_executor_for_packet(project=project, packet=packet, history=threshold_history)

    assert selection.ok is True
    assert selection.selected.executor_id == "codex-b"
