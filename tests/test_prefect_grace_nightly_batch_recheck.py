# ############################################################################
# AI_HEADER: test_prefect_grace_nightly_batch_recheck
# ROLE: Unit tests for stale-safe nightly batch recheck.
# ############################################################################

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json

import pytest
import yaml

from prefect_grace.platform.nightly_batch_recheck import recheck_nightly_batch
from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.runtime_lock import RuntimeLockResult


def _packet_text(packet_id: str, *, depends_on: list[str] | None = None, extra: str = "") -> str:
    feature_id = packet_id.split("-W", 1)[0]
    depends = ", ".join(depends_on or [])
    return f"""# Execution Packet: {packet_id}

## Objective

Implement a bounded unit-test packet.
{extra}

## Slice

- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-TEST`
- depends_on: `{depends}`

## Allowed Write Scope

- tests/{packet_id.lower()}.py

## Frozen Scope

- backend/**

## Must Preserve

- Read-only orchestration.

## Verification

pytest -q tests/{packet_id.lower()}.py

## Expected Evidence

- pytest output

## Escalation Triggers

- stale state
"""


def _write_packet(repo: Path, packet_id: str, *, depends_on: list[str] | None = None, extra: str = "") -> Path:
    feature_id = packet_id.split("-W", 1)[0]
    packet_dir = repo / "prefect_grace" / "packets" / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(_packet_text(packet_id, depends_on=depends_on, extra=extra), encoding="utf-8")
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir()
    (reviews / "review-0001.md").write_text("verdict: accepted\n", encoding="utf-8")
    evidence = packet_dir / "EVIDENCE" / "attempt-0001"
    evidence.mkdir(parents=True)
    (evidence / "evidence_manifest.json").write_text("{}", encoding="utf-8")
    return packet_path


def _project(tmp_path: Path, packet_id: str = "FEAT-TEST-ONE-W01-READY", *, depends_on: list[str] | None = None) -> tuple[Path, dict]:
    repo = tmp_path
    packet_path = _write_packet(repo, packet_id, depends_on=depends_on)
    project_path = repo / "prefect_grace" / "project.yaml"
    project_path.parent.mkdir(parents=True, exist_ok=True)
    project_path.write_text(
        f"""version: 1
project_key: test-project
repo_root: {repo}
default_branch: test
grace_dir: grace
packets_dir: prefect_grace/packets
runtime_state_root: runtime
artifact_root: runtime/artifacts
worktree_root: runtime/worktrees
workflow_runtime: prefect
prefect:
  work_pool: test-process
  live_queue: grace-live
  monitoring_queue: grace-monitoring
agent_executor:
  default: codex-cli
  command: codex1
""",
        encoding="utf-8",
    )
    parsed = parse_packet_markdown(packet_path, mode="strict")
    state = repo / "runtime" / "state"
    state.mkdir(parents=True)
    registry = {
        packet_id: {
            "packet_id": packet_id,
            "path": str(packet_path.relative_to(repo)),
            "registry_status": "ready",
            "status": "ready",
            "source_hash": parsed.source_hash,
            "depends_on": depends_on or [],
        }
    }
    for dep_id in depends_on or []:
        dep_path = _write_packet(repo, dep_id)
        dep_parsed = parse_packet_markdown(dep_path, mode="strict")
        registry[dep_id] = {
            "packet_id": dep_id,
            "path": str(dep_path.relative_to(repo)),
            "registry_status": "accepted",
            "status": "ready",
            "source_hash": dep_parsed.source_hash,
            "depends_on": [],
        }
    (state / "packet_registry.yaml").write_text(yaml.safe_dump(registry), encoding="utf-8")
    fact = {
        "packet_id": packet_id,
        "source_hash": parsed.source_hash,
        "registry_status": "ready",
        "source_status": "ready",
        "depends_on": depends_on or [],
        "review_status": "accepted",
        "evidence_status": "valid",
        "cost_estimate": "unit",
    }
    plan = {
        "ok": True,
        "project_key": "test-project",
        "mode": "nightly_batch_selection",
        "selected_packets": [packet_id],
        "selected_packet_facts": [fact],
        "selected_total": 1,
        "batch_limits": {"max_packets": 10, "max_cost": "live_required"},
        "dry_run": True,
    }
    return project_path, plan


def _binding_ok(**_: object) -> SimpleNamespace:
    return SimpleNamespace(ok=True, errors=[], prefect_runs_created=0, live_agents_started=0)


def _write_plan(tmp_path: Path, plan: dict) -> Path:
    plan_path = tmp_path / "selection.json"
    plan_path.write_text(json.dumps({"ok": True, "result": plan, "data": plan}), encoding="utf-8")
    return plan_path


def _codes(result) -> set[str]:
    return {str(blocker.get("code")) for blocker in result.blockers}


class _ReadyPrefectClient:
    def api_healthcheck(self):
        return None

    def read_work_pool(self, name):
        return SimpleNamespace(type="process", is_paused=False)

    def read_work_queue_by_name(self, queue_name, work_pool_name):
        return SimpleNamespace(is_paused=False)

    def read_deployment_by_name(self, deployment_name):
        return SimpleNamespace(work_pool_name="astro-process", work_queue_name="grace-live")


def test_clean_saved_plan_rechecks_as_ready(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
    )
    assert result.ok is True
    assert result.preflight_status == "ready"
    assert result.selected_total == 1
    assert result.confirmed_total == 1
    assert result.blocked_total == 0
    assert result.lock_status["acquired"] is True
    assert result.lock_status["released"] is True


def test_default_prefect_client_factory_can_confirm_non_empty_plan(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        prefect_client_factory=lambda: _ReadyPrefectClient(),
    )
    assert result.ok is True
    assert result.preflight_status == "ready"
    assert result.confirmed_total == 1
    assert result.lock_status["binding_checked"] is True
    assert result.lock_status["prefect_client_available"] is True


def test_default_prefect_client_missing_fails_closed_for_non_empty_plan(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        prefect_client_factory=lambda: None,
    )
    assert result.preflight_status == "blocked"
    assert "PREFECT_BINDING_NOT_READY" in _codes(result)
    assert result.lock_status["binding_checked"] is True
    assert result.lock_status["prefect_client_available"] is False


def test_stale_source_hash_blocks(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    packet_path = tmp_path / "prefect_grace" / "packets" / "FEAT-TEST-ONE" / "EXECUTION_PACKET.md"
    packet_path.write_text(_packet_text("FEAT-TEST-ONE-W01-READY", extra="\nChanged source.\n"), encoding="utf-8")
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
    )
    assert result.preflight_status == "blocked"
    assert "SOURCE_HASH_CHANGED" in _codes(result)


def test_stale_registry_status_blocks(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    registry_path = tmp_path / "runtime" / "state" / "packet_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["FEAT-TEST-ONE-W01-READY"]["registry_status"] = "blocked"
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
    )
    assert "REGISTRY_STATUS_CHANGED" in _codes(result)
    assert "REGISTRY_STATUS_NOT_RUNNABLE" in _codes(result)


def test_dependency_change_blocks(tmp_path: Path) -> None:
    packet_id = "FEAT-TEST-ONE-W01-READY"
    dep_id = "FEAT-TEST-DEP-W01-READY"
    project_path, plan = _project(tmp_path, packet_id=packet_id, depends_on=[dep_id])
    registry_path = tmp_path / "runtime" / "state" / "packet_registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry[dep_id]["registry_status"] = "blocked"
    registry_path.write_text(yaml.safe_dump(registry), encoding="utf-8")
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
    )
    assert "DEPENDENCY_NOT_ACCEPTED" in _codes(result)


def test_review_blocker_blocks(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    review = tmp_path / "prefect_grace" / "packets" / "FEAT-TEST-ONE" / "REVIEWS" / "review-0002.md"
    review.write_text("verdict: blocked\n", encoding="utf-8")
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
    )
    assert "REVIEW_STATUS_CHANGED" in _codes(result)
    assert "REVIEW_BLOCKS_PACKET" in _codes(result)


def test_prefect_binding_blocker_blocks(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)

    def binding_blocked(**_: object) -> SimpleNamespace:
        return SimpleNamespace(ok=False, errors=[{"type": "DEPLOYMENT_NOT_FOUND", "message": "missing"}])

    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=binding_blocked,
    )
    assert "PREFECT_BINDING_NOT_READY" in _codes(result)
    assert "prefect_binding" in result.blocker_classes
    assert result.blocked_total == 1
    assert result.confirmed_total == 0


def test_saved_plan_selected_total_mismatch_blocks(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    plan["selected_total"] = 2
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
        max_packets=10,
    )
    assert result.preflight_status == "blocked"
    assert result.selected_total == 2
    assert "PLAN_SELECTED_TOTAL_MISMATCH" in _codes(result)


def test_saved_plan_missing_packet_fact_blocks(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    plan["selected_packet_facts"] = []
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
    )
    assert result.preflight_status == "blocked"
    assert "PLAN_PACKET_FACT_MISSING" in _codes(result)
    assert "PLAN_SOURCE_HASH_MISSING" in _codes(result)


def test_saved_plan_exceeding_current_max_packets_blocks(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
        max_packets=0,
    )
    assert result.preflight_status == "blocked"
    assert "CURRENT_MAX_PACKETS_EXCEEDED" in _codes(result)


def test_lock_unavailable_blocks_and_does_not_leak(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    release_calls = []

    class FakeLock:
        def __init__(self, *args, **kwargs):
            pass

        def acquire(self):
            return RuntimeLockResult(path="/tmp/fake.lock", acquired=False, already_running=True)

        def release(self, result=None):
            release_calls.append(True)
            return result

    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
        lock_factory=FakeLock,
    )
    assert result.preflight_status == "blocked"
    assert "LOCK_UNAVAILABLE" in _codes(result)
    assert release_calls == [True]


def test_no_execution_or_mutation_side_effects(tmp_path: Path) -> None:
    project_path, plan = _project(tmp_path)
    before_registry = (tmp_path / "runtime" / "state" / "packet_registry.yaml").read_text(encoding="utf-8")
    result = recheck_nightly_batch(
        project_config=project_path,
        selection_path=_write_plan(tmp_path, plan),
        binding_checker=_binding_ok,
    )
    after_registry = (tmp_path / "runtime" / "state" / "packet_registry.yaml").read_text(encoding="utf-8")
    assert result.side_effects == {
        "registry_updates": 0,
        "prefect_runs_created": 0,
        "live_agents_started": 0,
        "worktrees_created": 0,
        "git_mutations_count": 0,
    }
    assert before_registry == after_registry
    assert not (tmp_path / ".worktrees").exists()


def test_bounded_output_regression() -> None:
    from prefect_grace.platform.nightly_batch_recheck import NightlyBatchRecheckResult, PacketRecheckSummary

    result = NightlyBatchRecheckResult(
        ok=False,
        project_key="test",
        blocker_classes=[f"class-{idx}" for idx in range(30)],
        packet_samples=[PacketRecheckSummary(f"PKT-{idx}", "blocked") for idx in range(30)],
        packet_samples_total=30,
        warnings=[{"code": str(idx)} for idx in range(30)],
        errors=[{"code": str(idx)} for idx in range(30)],
        blockers=[{"code": str(idx)} for idx in range(30)],
    )
    data = result.to_dict()
    assert len(data["blocker_classes"]) == 25
    assert len(data["packet_samples"]) == 25
    assert len(data["warnings"]) == 25
    assert len(data["errors"]) == 25
    assert len(data["blockers"]) == 25
