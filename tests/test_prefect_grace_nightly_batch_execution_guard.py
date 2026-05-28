# ############################################################################
# AI_HEADER: test_prefect_grace_nightly_batch_execution_guard
# ROLE: Unit tests for nightly batch execution guard with injected pilot runners.
# ############################################################################

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from prefect_grace.platform.nightly_batch_execution_guard import (
    BatchExecutionResult,
    PacketExecutionSummary,
    execute_batch_with_guard,
)
from prefect_grace.platform.nightly_batch_selection import (
    BatchSelectionResult,
    BatchLimits,
)
from prefect_grace.platform.single_live_packet_pilot import (
    SingleLivePacketPilotResult,
)


def _fake_pilot_success(**kwargs) -> SingleLivePacketPilotResult:
    """Fake pilot runner that always succeeds."""
    packet_id = kwargs.get("packet", Path("UNKNOWN")).parent.name
    dry_run = kwargs.get("dry_run", True)
    execute_agent = kwargs.get("execute_agent", False)
    commit = kwargs.get("commit", False)
    push = kwargs.get("push", False)

    return SingleLivePacketPilotResult(
        ok=True,
        packet_id=packet_id,
        status="planned" if dry_run else "completed",
        dry_run=dry_run,
        live_opt_in_confirmed=True,
        git_mutation_requested=commit or push,
        managed_runner_status="passed",
        scope_status="passed",
        evidence_status="valid",
        review_status="accepted",
        git_gate_status="planned" if dry_run else "applied",
        worktree_path=f"/tmp/worktree-{packet_id}",
        branch_name=f"packet-{packet_id}",
        live_agents_started=1 if execute_agent and not dry_run else 0,
        prefect_runs_created=0,
    )


def _fake_pilot_blocked(**kwargs) -> SingleLivePacketPilotResult:
    """Fake pilot runner that always blocks."""
    packet_id = kwargs.get("packet", Path("UNKNOWN")).parent.name
    dry_run = kwargs.get("dry_run", True)

    return SingleLivePacketPilotResult(
        ok=False,
        packet_id=packet_id,
        status="blocked",
        dry_run=dry_run,
        live_opt_in_confirmed=True,
        git_mutation_requested=False,
        managed_runner_status="scope_blocked",
        scope_status="blocked",
        blocker_reason="scope_guard_failed",
        blockers=[{"code": "scope_guard_failed", "message": "Scope check failed"}],
    )


def _fake_pilot_failed(**kwargs) -> SingleLivePacketPilotResult:
    """Fake pilot runner that always fails."""
    packet_id = kwargs.get("packet", Path("UNKNOWN")).parent.name
    dry_run = kwargs.get("dry_run", True)

    return SingleLivePacketPilotResult(
        ok=False,
        packet_id=packet_id,
        status="blocked",
        dry_run=dry_run,
        live_opt_in_confirmed=True,
        git_mutation_requested=False,
        managed_runner_status="agent_failed",
        blocker_reason="agent_failed",
        blockers=[{"code": "agent_failed", "message": "Agent execution failed"}],
    )


def test_batch_execution_dry_run_default():
    """Test that dry-run is the default mode."""
    # Use real packet IDs that exist
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=[
            "FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE",
            "FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE",
        ],
        selected_total=2,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        pilot_runner=_fake_pilot_success,
    )

    assert result.dry_run is True
    assert result.live_opt_in_confirmed is True
    assert result.selected_total == 2
    assert result.executed_total == 2
    assert result.passed_total == 2
    assert result.live_agents_started == 0
    assert result.lock_acquired is True
    assert result.lock_released is True


def test_batch_execution_missing_live_approval():
    """Test that missing live approval blocks execution."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=["FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE"],
        selected_total=1,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        dry_run=False,
        execute=True,
        acknowledge_live_batch=False,  # Missing acknowledgement
        opt_in_token="0",  # Wrong token
        pilot_runner=_fake_pilot_success,
    )

    assert result.ok is False
    assert result.live_opt_in_confirmed is False
    assert result.executed_total == 0
    assert result.live_agents_started == 0
    assert result.stop_reason == "live_opt_in_blocked"
    assert len(result.blockers) == 2
    assert any(b["code"] == "LIVE_BATCH_ACK_REQUIRED" for b in result.blockers)
    assert any(b["code"] == "LIVE_BATCH_TOKEN_REQUIRED" for b in result.blockers)


def test_batch_execution_live_with_approval():
    """Test that live execution works with proper approval."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=["FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE"],
        selected_total=1,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        dry_run=False,
        execute=True,
        acknowledge_live_batch=True,
        opt_in_token="1",
        pilot_runner=_fake_pilot_success,
    )

    assert result.ok is True
    assert result.live_opt_in_confirmed is True
    assert result.dry_run is False
    assert result.executed_total == 1
    assert result.passed_total == 1
    assert result.live_agents_started == 1


def test_batch_execution_max_failures_stop():
    """Test that execution stops after max failures."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=[
            "FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE",
            "FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE",
            "FEAT-GRACE-STATUS-MODEL-MVP-W01-STATUS-MODEL",
            "FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD",
        ],
        selected_total=4,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        max_failures=2,
        pilot_runner=_fake_pilot_blocked,
    )

    assert result.executed_total == 2
    assert result.blocked_total == 2
    assert result.stop_reason == "max_failures_reached"


def test_batch_execution_max_packets_limit():
    """Test that execution respects max_packets limit."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=[
            "FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE",
            "FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE",
            "FEAT-GRACE-STATUS-MODEL-MVP-W01-STATUS-MODEL",
            "FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD",
            "FEAT-GRACE-WORKTREE-MANAGER-MVP-W01-WORKTREE-MANAGER",
        ],
        selected_total=5,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        max_packets=3,
        pilot_runner=_fake_pilot_success,
    )

    assert result.executed_total == 3
    assert result.passed_total == 3
    assert result.stop_reason == "max_packets_reached"


def test_batch_execution_no_packets_selected():
    """Test that execution handles empty batch gracefully."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=[],
        selected_total=0,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        pilot_runner=_fake_pilot_success,
    )

    assert result.ok is True
    assert result.executed_total == 0
    assert result.stop_reason == "no_packets_selected"


def test_batch_execution_git_mutations_tracking():
    """Test that Git mutations are tracked correctly."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=[
            "FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE",
            "FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE",
        ],
        selected_total=2,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        allow_git_commit=True,
        allow_git_push=True,
        pilot_runner=_fake_pilot_success,
    )

    assert result.executed_total == 2
    assert result.git_mutations_count == 2


def test_batch_execution_bounded_output():
    """Test that output is bounded to MAX_PACKET_SUMMARIES."""
    # Create batch with more packets than the limit
    packet_ids = [
        "FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE",
        "FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE",
        "FEAT-GRACE-STATUS-MODEL-MVP-W01-STATUS-MODEL",
    ]
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=packet_ids,
        selected_total=3,
        batch_limits=BatchLimits(max_packets=50),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        max_packets=3,
        pilot_runner=_fake_pilot_success,
    )

    assert result.packet_summaries_total == 3
    assert len(result.packet_summaries) == 3

    # Check that to_dict bounds the output (would matter with 30+ packets)
    result_dict = result.to_dict()
    assert len(result_dict["packet_summaries"]) == 3


def test_batch_execution_lock_release_on_error():
    """Test that lock is released even on errors."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=["FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE"],
        selected_total=1,
        batch_limits=BatchLimits(max_packets=10),
    )

    def _fake_pilot_exception(**kwargs):
        raise RuntimeError("Simulated pilot failure")

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        pilot_runner=_fake_pilot_exception,
    )

    assert result.lock_acquired is True
    assert result.lock_released is True
    assert result.executed_total == 0
    assert result.skipped_total == 1


def test_batch_execution_mixed_results():
    """Test batch with mixed success/blocked/failed results."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=[
            "FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE",
            "FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE",
            "FEAT-GRACE-STATUS-MODEL-MVP-W01-STATUS-MODEL",
        ],
        selected_total=3,
        batch_limits=BatchLimits(max_packets=10),
    )

    call_count = [0]

    def _fake_pilot_mixed(**kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return _fake_pilot_success(**kwargs)
        elif call_count[0] == 2:
            return _fake_pilot_blocked(**kwargs)
        else:
            return _fake_pilot_failed(**kwargs)

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        max_failures=10,  # Allow all to execute
        pilot_runner=_fake_pilot_mixed,
    )

    assert result.executed_total == 3
    assert result.passed_total == 1
    assert result.blocked_total == 1
    assert result.failed_total == 1


def test_batch_execution_timing_tracked():
    """Test that execution timing is tracked."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=["FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE"],
        selected_total=1,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        pilot_runner=_fake_pilot_success,
    )

    assert result.execution_start != ""
    assert result.execution_end != ""
    assert result.execution_time_seconds > 0
    assert len(result.packet_summaries) == 1
    assert result.packet_summaries[0].execution_time_seconds >= 0


def test_batch_execution_result_serialization():
    """Test that BatchExecutionResult serializes correctly."""
    batch_selection = BatchSelectionResult(
        ok=True,
        project_key="astro-project",
        selected_packets=["FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE"],
        selected_total=1,
        batch_limits=BatchLimits(max_packets=10),
    )

    result = execute_batch_with_guard(
        project_config=Path("/opt/astro-project/prefect_grace/project.yaml"),
        batch_selection=batch_selection,
        pilot_runner=_fake_pilot_success,
    )

    result_dict = result.to_dict()

    assert result_dict["ok"] is True
    assert result_dict["project_key"] == "astro-project"
    assert result_dict["mode"] == "nightly_batch_execution_guard"
    assert result_dict["dry_run"] is True
    assert result_dict["selected_total"] == 1
    assert result_dict["executed_total"] == 1
    assert result_dict["lock_acquired"] is True
    assert result_dict["lock_released"] is True
    assert isinstance(result_dict["packet_summaries"], list)
    assert len(result_dict["packet_summaries"]) == 1
