from pathlib import Path

from prefect_grace.platform.live_opt_in_single_scratch_packet import (
    FROZEN_SCOPE,
    PACKET_ID,
    SCRATCH_ALLOWED_SCOPE,
    run_live_opt_in_single_scratch_packet,
)
from prefect_grace.platform.packet_parser import parse_packet_markdown


def _write_project_config(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_path = tmp_path / "project.yaml"
    config_path.write_text(f"""
version: 1
project_key: test-project
repo_root: {repo_root}
default_branch: main
grace_dir: grace
packets_dir: packets
runtime_state_root: {tmp_path / "project-state"}
artifact_root: {tmp_path / "artifacts"}
worktree_root: {tmp_path / "project-worktrees"}
workflow_runtime: prefect
prefect:
  work_pool: test-pool
  live_queue: test-live
  monitoring_queue: test-monitoring
agent_executor:
  default: codex-cli
  command: codex1
""", encoding="utf-8")
    return config_path


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    return tmp_path / "state", tmp_path / "worktrees", tmp_path / "packets"


def _fake_runner(calls: list[dict], *, scope_verdict: str = "passed", ok: bool = True):
    def runner(**kwargs):
        calls.append(kwargs)
        scratch_file = kwargs["project_root"] / "scratch" / "grace-live-opt-in-single-scratch" / "evidence.txt"
        scratch_file.parent.mkdir(parents=True, exist_ok=True)
        scratch_file.write_text("live opt-in single scratch evidence\n", encoding="utf-8")
        return {
            "ok": ok,
            "domain_status": "accepted" if ok else "scope_blocked",
            "scope_verdict": scope_verdict,
            "changed_files": ["scratch/grace-live-opt-in-single-scratch/evidence.txt"],
            "deployment_name": "e2e-packet-runner/live",
            "work_queue_name": "test-live",
            "flow_run_id": "injected-flow-run",
            "flow_run_name": f"e2e-packet:{PACKET_ID}:attempt-1",
            "flow_run_url": "http://prefect.local/flow-runs/injected-flow-run",
        }
    return runner


def test_live_opt_in_single_scratch_fails_closed_without_execute_agent(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
    )

    assert result.ok is False
    assert result.opt_in_confirmed is False
    assert result.agent_launch_count == 0
    assert result.errors[0]["code"] == "LIVE_OPT_IN_EXECUTE_AGENT_REQUIRED"
    assert calls == []
    assert not packet_root.exists()


def test_live_opt_in_single_scratch_fails_closed_without_ack(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "LIVE_OPT_IN_ACK_REQUIRED"
    assert calls == []


def test_live_opt_in_single_scratch_fails_closed_without_token(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token=None,
        runner=_fake_runner(calls),
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "LIVE_OPT_IN_TOKEN_REQUIRED"
    assert calls == []


def test_live_opt_in_single_scratch_rejects_unsafe_roots_after_gates(tmp_path: Path) -> None:
    calls: list[dict] = []

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=Path("/var/lib/grace-orchestrator/live-opt-in-single-scratch"),
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
    )

    assert result.ok is False
    assert result.opt_in_confirmed is True
    assert result.errors[0]["code"] == "UNSAFE_STATE_ROOT"
    assert calls == []


def test_live_opt_in_single_scratch_rejects_repo_root_worktree(tmp_path: Path) -> None:
    config_path = _write_project_config(tmp_path)
    calls: list[dict] = []

    result = run_live_opt_in_single_scratch_packet(
        project_config=config_path,
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "repo" / "worktrees",
        packet_root=tmp_path / "packets",
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "UNSAFE_WORKTREE_ROOT"
    assert calls == []


def test_live_opt_in_single_scratch_writes_exact_synthetic_packet_scope(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
    )

    packet_path = packet_root / "packets" / PACKET_ID / "EXECUTION_PACKET.md"
    parsed = parse_packet_markdown(packet_path, mode="strict")
    assert result.ok is True
    assert parsed.packet_id == PACKET_ID
    assert parsed.allowed_write_scope == [SCRATCH_ALLOWED_SCOPE]
    assert parsed.frozen_scope == FROZEN_SCOPE
    assert parsed.objective == "Write one tiny deterministic scratch evidence file only."


def test_live_opt_in_single_scratch_registry_plan_selects_one_packet(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
    )

    assert result.ok is True
    assert result.selected_packet_id == PACKET_ID
    assert result.submit_plan["packets_to_submit"] == [PACKET_ID]
    assert PACKET_ID in result.registry_before


def test_live_opt_in_single_scratch_rejects_extra_ready_packet(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
        extra_ready_packet=True,
    )

    assert result.ok is False
    assert result.selected_packet_id is None
    assert any(error["code"] == "LIVE_OPT_IN_PACKET_COUNT_INVALID" for error in result.errors)
    assert calls == []


def test_live_opt_in_single_scratch_records_one_injected_live_launch(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls),
    )

    assert result.ok is True
    assert result.agent_launch_count == 1
    assert result.scope_verdict == "passed"
    assert result.domain_status == "accepted"
    assert result.changed_files == ["scratch/grace-live-opt-in-single-scratch/evidence.txt"]
    assert result.writes_outside_temp_roots == []
    assert len(calls) == 1
    assert calls[0]["dry_run"] is False
    assert calls[0]["execute_agent"] is True


def test_live_opt_in_single_scratch_scope_failure_blocks_ok(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner(calls, scope_verdict="failed", ok=True),
    )

    assert result.ok is False
    assert any(error["code"] == "LIVE_OPT_IN_SCOPE_NOT_PASSED" for error in result.errors)
    assert result.agent_launch_count == 1


def test_live_opt_in_single_scratch_rejects_changed_files_outside_scratch(tmp_path: Path) -> None:
    calls: list[dict] = []
    state_root, worktree_root, packet_root = _roots(tmp_path)

    def runner(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "domain_status": "accepted",
            "scope_verdict": "passed",
            "changed_files": ["backend/app.py"],
        }

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=runner,
    )

    assert result.ok is False
    assert result.agent_launch_count == 1
    assert any(error["code"] == "LIVE_OPT_IN_CHANGED_FILES_OUTSIDE_SCRATCH" for error in result.errors)


def test_live_opt_in_single_scratch_result_does_not_serialize_token(tmp_path: Path) -> None:
    state_root, worktree_root, packet_root = _roots(tmp_path)

    result = run_live_opt_in_single_scratch_packet(
        project_config=_write_project_config(tmp_path),
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="single-scratch",
        runner=_fake_runner([]),
    )

    assert result.ok is True
    serialized = result.to_dict()
    assert "opt_in_token" not in serialized
    assert "GRACE_LIVE_AGENT_OPT_IN" not in str(serialized)
