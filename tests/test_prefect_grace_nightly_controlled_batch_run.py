# ############################################################################
# AI_HEADER: test_prefect_grace_nightly_controlled_batch_run
# ROLE: Unit tests for controlled nightly batch runner with injected runners.
# ############################################################################

from __future__ import annotations

from pathlib import Path

from prefect_grace.platform.nightly_batch_execution_guard import (
    BatchExecutionResult,
    PacketExecutionSummary,
)
from prefect_grace.platform.nightly_batch_recheck import (
    NightlyBatchRecheckResult,
    PacketRecheckSummary,
)
from prefect_grace.platform.nightly_controlled_batch_run import (
    DEFAULT_MAX_PACKETS,
    run_nightly_controlled_batch,
)
from prefect_grace.platform.runtime_lock import RuntimeLockResult


def _project(tmp_path: Path) -> Path:
    (tmp_path / "prefect_grace" / "packets").mkdir(parents=True)
    project = tmp_path / "prefect_grace" / "project.yaml"
    project.write_text(
        "\n".join([
            "version: 1",
            "project_key: controlled-test",
            f"repo_root: {tmp_path}",
            "default_branch: main",
            "grace_dir: grace",
            "packets_dir: prefect_grace/packets",
            f"runtime_state_root: {tmp_path / 'runtime'}",
            f"artifact_root: {tmp_path / 'artifacts'}",
            f"worktree_root: {tmp_path / 'worktrees'}",
            "workflow_runtime: prefect",
            "prefect:",
            "  work_pool: test-pool",
            "  live_queue: grace-live",
            "  monitoring_queue: grace-monitoring",
        ]),
        encoding="utf-8",
    )
    return project


def _recheck(*packet_ids: str, ok: bool = True) -> NightlyBatchRecheckResult:
    samples = [
        PacketRecheckSummary(packet_id=packet_id, status="confirmed")
        for packet_id in packet_ids
    ]
    return NightlyBatchRecheckResult(
        ok=ok,
        project_key="controlled-test",
        preflight_status="ready" if ok else "blocked",
        selected_total=len(packet_ids),
        confirmed_total=len(packet_ids) if ok else 0,
        blocked_total=0 if ok else 1,
        packet_samples=samples,
        packet_samples_total=len(samples),
        side_effects={
            "registry_updates": 0,
            "prefect_runs_created": 0,
            "live_agents_started": 0,
            "worktrees_created": 0,
            "git_mutations_count": 0,
        },
        blockers=[] if ok else [{"code": "RECHECK_BLOCKED", "message": "blocked"}],
    )


def _execution_result(*packet_ids: str, ok: bool = True, stop_reason: str = "all_packets_executed") -> BatchExecutionResult:
    summaries = [
        PacketExecutionSummary(
            packet_id=packet_id,
            status="completed" if ok else "blocked",
            dry_run=False,
            live_opt_in_confirmed=True,
            git_mutation_requested=False,
            flow_run_id=f"flow-{packet_id}",
            agent_count=1,
            domain_status="passed" if ok else "scope_blocked",
            scope_status="passed" if ok else "blocked",
            evidence_status="valid",
            review_status="accepted",
            branch_push_status="not_requested",
            stop_reason=None if ok else "scope_guard_failed",
            changed_files_sample=["prefect_grace/platform/example.py"],
        )
        for packet_id in packet_ids
    ]
    return BatchExecutionResult(
        ok=ok,
        project_key="controlled-test",
        dry_run=False,
        live_opt_in_confirmed=True,
        selected_total=len(packet_ids),
        executed_total=len(packet_ids),
        passed_total=len(packet_ids) if ok else 0,
        blocked_total=0 if ok else 1,
        failed_total=0,
        stop_reason=stop_reason,
        lock_acquired=True,
        lock_released=True,
        live_agents_started=len(packet_ids) if ok else 0,
        prefect_runs_created=len(packet_ids) if ok else 0,
        packet_summaries=summaries,
        packet_summaries_total=len(summaries),
    )


class _UnavailableLock:
    release_calls: list[RuntimeLockResult] = []

    def __init__(self, *args, **kwargs) -> None:
        pass

    def acquire(self) -> RuntimeLockResult:
        return RuntimeLockResult(
            path="/tmp/controlled-unavailable.lock",
            acquired=False,
            already_running=True,
            errors=[{"code": "controller_already_running", "message": "busy"}],
        )

    def release(self, result: RuntimeLockResult) -> RuntimeLockResult:
        self.release_calls.append(result)
        result.released = True
        return result


def test_controlled_batch_dry_run_executes_nothing(tmp_path: Path) -> None:
    calls: list[str] = []

    def execution_runner(**kwargs):
        calls.append("execution")
        return _execution_result("FEAT-ONE-W01")

    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        recheck_runner=lambda **kwargs: _recheck("FEAT-ONE-W01", "FEAT-TWO-W01"),
        execution_runner=execution_runner,
    )

    assert result.ok is True
    assert result.dry_run is True
    assert result.stop_reason == "dry_run_complete"
    assert result.executed_total == 0
    assert result.live_agents_started == 0
    assert result.prefect_runs_created == 0
    assert calls == []
    assert result.lock_acquired is True
    assert result.lock_released is True


def test_missing_live_approval_starts_zero_agents_and_runs(tmp_path: Path) -> None:
    calls: list[str] = []

    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        dry_run=False,
        execute=True,
        acknowledge_live_batch=False,
        opt_in_token="0",
        recheck_runner=lambda **kwargs: calls.append("recheck") or _recheck("FEAT-ONE-W01"),
        execution_runner=lambda **kwargs: calls.append("execution") or _execution_result("FEAT-ONE-W01"),
    )

    assert result.ok is False
    assert result.stop_reason == "live_opt_in_blocked"
    assert result.live_opt_in_confirmed is False
    assert result.live_agents_started == 0
    assert result.prefect_runs_created == 0
    assert result.executed_total == 0
    assert calls == []
    assert result.lock_released is True


def test_controlled_batch_lock_unavailable_calls_release(tmp_path: Path) -> None:
    _UnavailableLock.release_calls = []
    calls: list[str] = []

    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        recheck_runner=lambda **kwargs: calls.append("recheck") or _recheck("FEAT-ONE-W01"),
        execution_runner=lambda **kwargs: calls.append("execution") or _execution_result("FEAT-ONE-W01"),
        lock_factory=_UnavailableLock,
    )

    assert result.ok is False
    assert result.stop_reason == "lock_unavailable"
    assert result.lock_acquired is False
    assert result.lock_released is True
    assert result.executed_total == 0
    assert calls == []
    assert len(_UnavailableLock.release_calls) == 1


def test_live_delegation_is_concurrency_one_no_merge_and_bounded(tmp_path: Path) -> None:
    seen: dict = {}

    def execution_runner(**kwargs):
        seen.update(kwargs)
        return _execution_result("FEAT-ONE-W01")

    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        dry_run=False,
        execute=True,
        acknowledge_live_batch=True,
        opt_in_token="1",
        recheck_runner=lambda **kwargs: _recheck("FEAT-ONE-W01", "FEAT-TWO-W01"),
        execution_runner=execution_runner,
    )

    assert result.ok is True
    assert seen["concurrency"] == 1
    assert seen["max_packets"] == DEFAULT_MAX_PACKETS
    assert seen["timeout_seconds_per_packet"] == 1800
    assert seen["max_failures"] == 1
    assert seen["stop_on_degradation"] is True
    assert seen["allow_git_merge"] is False
    assert seen["batch_selection"].selected_packets == ["FEAT-ONE-W01", "FEAT-TWO-W01"]
    assert result.packet_summaries[0].flow_run_id == "flow-FEAT-ONE-W01"
    assert result.packet_summaries[0].changed_files_sample == ["prefect_grace/platform/example.py"]


def test_live_respects_max_packets_and_branch_push_delegation(tmp_path: Path) -> None:
    seen: dict = {}
    packet_ids = [f"FEAT-{index}-W01" for index in range(5)]

    def execution_runner(**kwargs):
        seen.update(kwargs)
        return _execution_result(*kwargs["batch_selection"].selected_packets)

    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        max_packets=3,
        dry_run=False,
        execute=True,
        acknowledge_live_batch=True,
        opt_in_token="1",
        allow_git_commit=True,
        allow_git_push=True,
        recheck_runner=lambda **kwargs: _recheck(*packet_ids),
        execution_runner=execution_runner,
    )

    assert result.executed_total == 3
    assert seen["batch_selection"].selected_packets == packet_ids[:3]
    assert seen["allow_git_commit"] is True
    assert seen["allow_git_push"] is True
    assert seen["allow_git_merge"] is False


def test_live_surfaces_stop_conditions_from_guard(tmp_path: Path) -> None:
    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        dry_run=False,
        execute=True,
        acknowledge_live_batch=True,
        opt_in_token="1",
        recheck_runner=lambda **kwargs: _recheck("FEAT-ONE-W01", "FEAT-TWO-W01"),
        execution_runner=lambda **kwargs: _execution_result(
            "FEAT-ONE-W01",
            ok=False,
            stop_reason="unexpected_degradation",
        ),
    )

    assert result.ok is False
    assert result.stop_reason == "unexpected_degradation"
    assert result.blocked_total == 1
    assert result.live_agents_started == 0


def test_controlled_batch_blocks_non_one_concurrency(tmp_path: Path) -> None:
    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        concurrency=2,
        recheck_runner=lambda **kwargs: _recheck("FEAT-ONE-W01"),
        execution_runner=lambda **kwargs: _execution_result("FEAT-ONE-W01"),
    )

    assert result.ok is False
    assert result.stop_reason == "control_blocked"
    assert any(blocker["code"] == "CONCURRENCY_MUST_BE_ONE" for blocker in result.blockers)
    assert result.executed_total == 0
    assert result.lock_released is True


def test_controlled_output_is_bounded(tmp_path: Path) -> None:
    packet_ids = [f"FEAT-{index}-W01" for index in range(40)]

    result = run_nightly_controlled_batch(
        project_config=_project(tmp_path),
        recheck_runner=lambda **kwargs: _recheck(*packet_ids),
    )

    payload = result.to_dict()
    assert result.packet_summaries_total == 40
    assert len(payload["packet_summaries"]) == 25
    assert payload["allow_merge"] is False
