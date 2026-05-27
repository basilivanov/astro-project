from pathlib import Path
import tempfile

from prefect_grace.platform.e2e_runner_registry_seeded_smoke import (
    PACKET_CHILD_BLOCKED_DEP,
    PACKET_CHILD_MISSING_DEP,
    PACKET_CHILD_RUNNABLE,
    PACKET_PARENT_ACCEPTED,
    PACKET_SOURCE_STATUS_ONLY,
    run_e2e_runner_registry_seeded_smoke,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_CONFIG = PROJECT_ROOT / "prefect_grace" / "project.yaml"


def test_e2e_runner_registry_seeded_smoke_runs_isolated_temp_roots(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
    )

    assert result.ok is True
    assert result.selected_packet_id == PACKET_CHILD_RUNNABLE
    assert result.bootstrap_apply_count == 6
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert result.writes_outside_temp_roots == []
    assert all(case.ok for case in result.cases)

    assert result.submit_plan["dry_run"] is True
    assert result.submit_plan["packets_planned"] == [PACKET_CHILD_RUNNABLE]
    assert result.submit_plan["packets_submitted"] == []

    assert result.registry_before[PACKET_PARENT_ACCEPTED]["registry_status"] == "accepted"
    assert result.registry_before[PACKET_CHILD_RUNNABLE]["registry_status"] == "ready"
    assert result.registry_before[PACKET_CHILD_MISSING_DEP]["registry_status"] == "waiting_for_dependencies"
    assert result.registry_before[PACKET_CHILD_BLOCKED_DEP]["registry_status"] == "waiting_for_dependencies"
    assert result.registry_before[PACKET_SOURCE_STATUS_ONLY]["registry_status"] != "accepted"

    assert result.e2e_result is not None
    assert result.e2e_result["domain_status"] == "accepted"
    assert result.e2e_result["registry_status"] == "accepted"
    assert result.e2e_result["registry_reason"] == "execution_accepted"
    assert result.e2e_result["managed_runner_result"]["agent_result"]["dry_run"] is True
    assert result.e2e_result["managed_runner_result"]["agent_result"]["execute_agent"] is False

    selected_after = result.registry_after[PACKET_CHILD_RUNNABLE]
    assert selected_after["registry_status"] == "accepted"
    assert selected_after["registry_reason"] == "execution_accepted"
    assert selected_after["domain_status"] == "accepted"
    assert selected_after["selected_for_e2e"] is True
    assert result.registry_after[PACKET_PARENT_ACCEPTED]["registry_status"] == "accepted"
    assert result.registry_after[PACKET_CHILD_MISSING_DEP]["registry_status"] == "waiting_for_dependencies"
    assert result.registry_after[PACKET_SOURCE_STATUS_ONLY]["registry_status"] != "accepted"


def test_e2e_runner_registry_seeded_smoke_rejects_unsafe_state_root(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=Path("/var/lib/grace-orchestrator/e2e-seeded-smoke"),
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
    )

    assert result.ok is False
    assert result.bootstrap_apply_count == 0
    assert result.errors[0]["code"] == "UNSAFE_STATE_ROOT"


def test_e2e_runner_registry_seeded_smoke_rejects_repo_root_state(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=PROJECT_ROOT,
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
    )

    assert result.ok is False
    assert result.bootstrap_apply_count == 0
    assert any(error["code"] == "UNSAFE_STATE_ROOT" for error in result.errors)


def test_e2e_runner_registry_seeded_smoke_rejects_broad_tmp_state_root(tmp_path: Path) -> None:
    tmp_root = Path(tempfile.gettempdir())
    sentinel = tmp_root / "grace-e2e-seeded-smoke-sentinel.txt"
    sentinel.write_text("do not delete", encoding="utf-8")
    try:
        result = run_e2e_runner_registry_seeded_smoke(
            project_config=PROJECT_CONFIG,
            state_root=tmp_root,
            worktree_root=tmp_path / "worktrees",
            packet_root=tmp_path / "packets",
        )
    finally:
        assert sentinel.exists()
        sentinel.unlink()

    assert result.ok is False
    assert any(error["code"] == "UNSAFE_STATE_ROOT" for error in result.errors)


def test_e2e_runner_registry_seeded_smoke_rejects_worktree_root_inside_repo(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=tmp_path / "state",
        worktree_root=PROJECT_ROOT,
        packet_root=tmp_path / "packets",
    )

    assert result.ok is False
    assert any(error["code"] == "UNSAFE_WORKTREE_ROOT" for error in result.errors)


def test_e2e_runner_registry_seeded_smoke_rejects_broad_tmp_worktree_root(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=tmp_path / "state",
        worktree_root=Path(tempfile.gettempdir()),
        packet_root=tmp_path / "packets",
    )

    assert result.ok is False
    assert any(error["code"] == "UNSAFE_WORKTREE_ROOT" for error in result.errors)


def test_e2e_runner_registry_seeded_smoke_rejects_packet_root_inside_repo(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=PROJECT_ROOT / "prefect_grace" / "packets" / "unsafe-smoke",
    )

    assert result.ok is False
    assert any(error["code"] == "UNSAFE_PACKET_ROOT" for error in result.errors)


def test_e2e_runner_registry_seeded_smoke_rejects_broad_tmp_packet_root(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=Path(tempfile.gettempdir()),
    )

    assert result.ok is False
    assert any(error["code"] == "UNSAFE_PACKET_ROOT" for error in result.errors)


def test_e2e_runner_registry_seeded_smoke_rejects_overlapping_temp_roots(tmp_path: Path) -> None:
    result = run_e2e_runner_registry_seeded_smoke(
        project_config=PROJECT_CONFIG,
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "state" / "worktrees",
        packet_root=tmp_path / "packets",
    )

    assert result.ok is False
    assert any(error["code"] == "OVERLAPPING_TEMP_ROOTS" for error in result.errors)
