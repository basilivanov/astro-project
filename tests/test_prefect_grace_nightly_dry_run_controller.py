from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from prefect_grace.platform.nightly_dry_run_controller import run_nightly_dry_run
from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.runtime_lock import RuntimeLock
from prefect_grace.platform.state_store import PacketRegistryStore


def _write_project_config(path: Path, *, repo_root: Path, packets_dir: Path, runtime_root: Path) -> None:
    path.write_text(
        f"""version: 1
project_key: test-project
repo_root: {repo_root}
default_branch: main
grace_dir: grace
packets_dir: {packets_dir.relative_to(repo_root)}
runtime_state_root: {runtime_root}
artifact_root: {runtime_root / "artifacts"}
worktree_root: {runtime_root / "worktrees"}
workflow_runtime: prefect
prefect:
  work_pool: test-process
  live_queue: test-live
  monitoring_queue: test-monitoring
agent_executor:
  default: codex-cli
  command: codex1
""",
        encoding="utf-8",
    )


def _fixture_project(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repo_root = tmp_path / "repo"
    packets_dir = repo_root / "packets"
    runtime_root = tmp_path / "runtime"
    repo_root.mkdir()
    config = tmp_path / "project.yaml"
    _write_project_config(config, repo_root=repo_root, packets_dir=packets_dir, runtime_root=runtime_root)
    return config, repo_root, packets_dir, runtime_root


def _write_strict_packet(
    packets_dir: Path,
    feature_id: str,
    packet_id: str,
    *,
    depends_on: list[str] | None = None,
) -> Path:
    packet_dir = packets_dir / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    dependency_line = f"- depends_on: `{', '.join(depends_on)}`\n" if depends_on else ""
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(
        f"""# Execution Packet: {packet_id}

## Objective
Nightly test packet.

## Slice
- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `ready`
{dependency_line}
## Allowed Write Scope
- prefect_grace/platform/example.py

## Frozen Scope
- backend/**

## Must Preserve
- Source packet files are immutable.

## Verification
pytest

## Expected Evidence
- test output

## Escalation Triggers
- missing evidence
""",
        encoding="utf-8",
    )
    return packet_path


def _registry_record(packet_path: Path, status: str) -> dict:
    parsed = parse_packet_markdown(packet_path)
    return {
        "packet_id": parsed.packet_id,
        "feature_id": parsed.feature_id,
        "wave_id": parsed.wave_id,
        "title": parsed.title,
        "depends_on": parsed.depends_on,
        "source_hash": parsed.source_hash,
        "path": str(packet_path),
        "registry_status": status,
    }


def test_nightly_all_accepted_registry_has_no_runnable_packets(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    p1 = _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")
    p2 = _write_strict_packet(packets_dir, "FEAT-TWO", "FEAT-TWO-W01-PACKET")
    registry = PacketRegistryStore(runtime_root / "state")
    registry.upsert_packet(_registry_record(p1, "accepted"))
    registry.upsert_packet(_registry_record(p2, "accepted"))

    result = run_nightly_dry_run(project_config=config, until_blocked=True)

    assert result.ok is True
    assert result.preflight_status == "ready"
    assert result.plan["would_submit_total"] == 0
    assert result.plan["stop_reason"] == "nothing_runnable"
    assert result.side_effects["prefect_runs_created"] == 0
    assert result.side_effects["registry_updates"] == 0
    assert result.lock["acquired"] is True
    assert result.lock["released"] is True
    assert not Path(result.lock["path"]).exists()


def test_nightly_stale_source_runtime_blocks_ready_verdict(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, _runtime_root = _fixture_project(tmp_path)
    packet = _write_strict_packet(packets_dir, "FEAT-ACCEPTED", "FEAT-ACCEPTED-W01-PACKET")
    (packet.parent / "SUMMARY.md").write_text("current_status: accepted\n", encoding="utf-8")

    result = run_nightly_dry_run(project_config=config, until_blocked=True)

    assert result.ok is True
    assert result.preflight_status == "blocked"
    assert result.plan["stop_reason"] == "source_runtime_mismatch"
    assert result.runtime["stale_source_runtime_mismatches_total"] == 1
    assert result.runtime["accepted_source_still_ready_or_blocked"] == ["FEAT-ACCEPTED-W01-PACKET"]
    assert result.side_effects["prefect_runs_created"] == 0


def test_nightly_runnable_dependency_chain_is_ordered_without_submission(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    parent = _write_strict_packet(packets_dir, "FEAT-PARENT", "FEAT-PARENT-W01-PACKET")
    child = _write_strict_packet(
        packets_dir,
        "FEAT-CHILD",
        "FEAT-CHILD-W01-PACKET",
        depends_on=["FEAT-PARENT-W01-PACKET"],
    )
    registry = PacketRegistryStore(runtime_root / "state")
    registry.upsert_packet(_registry_record(parent, "accepted"))
    registry.upsert_packet(_registry_record(child, "ready"))

    result = run_nightly_dry_run(project_config=config)

    assert result.ok is True
    assert result.preflight_status == "ready"
    assert result.plan["would_submit"] == ["FEAT-CHILD-W01-PACKET"]
    assert result.plan["submission_order"] == ["FEAT-CHILD-W01-PACKET"]
    assert result.side_effects["prefect_runs_created"] == 0


def test_nightly_blocked_dependency_stays_blocked(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    parent = _write_strict_packet(packets_dir, "FEAT-BLOCKED", "FEAT-BLOCKED-W01-PACKET")
    child = _write_strict_packet(
        packets_dir,
        "FEAT-WAITING",
        "FEAT-WAITING-W01-PACKET",
        depends_on=["FEAT-BLOCKED-W01-PACKET"],
    )
    registry = PacketRegistryStore(runtime_root / "state")
    registry.upsert_packet(_registry_record(parent, "blocked"))
    registry.upsert_packet(_registry_record(child, "waiting_for_dependencies"))

    result = run_nightly_dry_run(project_config=config, until_blocked=True)

    assert result.ok is True
    assert result.preflight_status == "ready"
    assert result.plan["would_submit_total"] == 0
    assert result.plan["blocked_packets"] == ["FEAT-BLOCKED-W01-PACKET"]
    assert result.runtime["blocked"] == 1
    assert result.runtime["waiting"] == 1


def test_nightly_reports_already_running_lock(tmp_path: Path) -> None:
    config, _repo_root, _packets_dir, runtime_root = _fixture_project(tmp_path)
    lock = RuntimeLock(runtime_root, owner="existing-controller")
    acquired = lock.acquire()
    assert acquired.acquired is True

    result = run_nightly_dry_run(project_config=config)

    assert result.ok is False
    assert result.lock["already_running"] is True
    assert result.errors[0]["code"] == "controller_already_running"
    lock.release(acquired)


def test_nightly_replaces_stale_lock_and_releases_it(tmp_path: Path) -> None:
    config, _repo_root, packets_dir, runtime_root = _fixture_project(tmp_path)
    _write_strict_packet(packets_dir, "FEAT-ONE", "FEAT-ONE-W01-PACKET")
    lock_path = runtime_root / "state" / "locks" / "backlog-controller.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(
        json.dumps(
            {
                "owner": "stale-controller",
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            }
        ),
        encoding="utf-8",
    )

    result = run_nightly_dry_run(project_config=config, lock_max_age_seconds=1)

    assert result.lock["acquired"] is True
    assert result.lock["stale_replaced"] is True
    assert result.lock["released"] is True
    assert not lock_path.exists()


def test_nightly_releases_lock_on_planning_failure(tmp_path: Path) -> None:
    config, _repo_root, _packets_dir, runtime_root = _fixture_project(tmp_path)

    result = run_nightly_dry_run(project_config=config)

    assert result.ok is False
    assert result.lock["acquired"] is True
    assert result.lock["released"] is True
    assert not Path(result.lock["path"]).exists()
