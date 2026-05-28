# ############################################################################
# AI_HEADER: test_prefect_grace_cli_nightly_batch_recheck
# ROLE: CLI contract tests for nightly batch recheck command.
# ############################################################################

from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys

import yaml

from prefect_grace.platform.packet_parser import parse_packet_markdown


def _empty_project(tmp_path: Path) -> tuple[Path, Path]:
    project_dir = tmp_path / "prefect_grace"
    project_dir.mkdir()
    project_path = project_dir / "project.yaml"
    project_path.write_text(
        f"""version: 1
project_key: test-project
repo_root: {tmp_path}
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
    selection = tmp_path / "selection.json"
    plan = {
        "ok": True,
        "project_key": "test-project",
        "mode": "nightly_batch_selection",
        "selected_packets": [],
        "selected_packet_facts": [],
        "selected_total": 0,
        "batch_limits": {"max_packets": 10, "max_cost": "live_required"},
        "dry_run": True,
    }
    selection.write_text(json.dumps({"ok": True, "result": plan, "data": plan}), encoding="utf-8")
    return project_path, selection


def _packet_text(packet_id: str) -> str:
    feature_id = packet_id.split("-W", 1)[0]
    return f"""# Execution Packet: {packet_id}

## Objective

Implement CLI recheck coverage packet.

## Slice

- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-TEST`
- depends_on: ``

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


def _non_empty_project(tmp_path: Path) -> tuple[Path, Path]:
    project_path, _ = _empty_project(tmp_path)
    packet_id = "FEAT-CLI-RECHECK-W01-READY"
    packet_dir = tmp_path / "prefect_grace" / "packets" / "FEAT-CLI-RECHECK"
    packet_dir.mkdir(parents=True)
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(_packet_text(packet_id), encoding="utf-8")
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir()
    (reviews / "review-0001.md").write_text("verdict: accepted\n", encoding="utf-8")
    evidence = packet_dir / "EVIDENCE" / "attempt-0001"
    evidence.mkdir(parents=True)
    (evidence / "evidence_manifest.json").write_text("{}", encoding="utf-8")
    parsed = parse_packet_markdown(packet_path, mode="strict")
    state = tmp_path / "runtime" / "state"
    state.mkdir(parents=True)
    (state / "packet_registry.yaml").write_text(yaml.safe_dump({
        packet_id: {
            "packet_id": packet_id,
            "path": str(packet_path.relative_to(tmp_path)),
            "registry_status": "ready",
            "status": "ready",
            "source_hash": parsed.source_hash,
            "depends_on": [],
        }
    }), encoding="utf-8")
    fact = {
        "packet_id": packet_id,
        "source_hash": parsed.source_hash,
        "registry_status": "ready",
        "source_status": "ready",
        "depends_on": [],
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
    selection = tmp_path / "non_empty_selection.json"
    selection.write_text(json.dumps({"ok": True, "result": plan, "data": plan}), encoding="utf-8")
    return project_path, selection


def test_cli_nightly_recheck_batch_contract() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "nightly-recheck-batch", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--selection" in result.stdout
    assert "--max-packets" in result.stdout
    assert "--max-cost" in result.stdout
    assert "--allow-conflicts" in result.stdout
    assert "--allow-risky" in result.stdout
    assert "--json" in result.stdout


def test_cli_nightly_recheck_batch_json_envelope(tmp_path: Path) -> None:
    project_path, selection = _empty_project(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-recheck-batch",
            "--project",
            str(project_path),
            "--selection",
            str(selection),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["command"] == "nightly-recheck-batch"
    assert data["project_key"] == "test-project"
    assert data["result"] == data["data"]
    payload = data["result"]
    assert payload["mode"] == "nightly_batch_recheck"
    assert payload["dry_run"] is True
    assert payload["preflight_status"] == "ready"
    assert payload["selected_total"] == 0
    assert payload["confirmed_total"] == 0
    assert payload["blocked_total"] == 0
    assert payload["side_effects"]["prefect_runs_created"] == 0
    assert payload["side_effects"]["live_agents_started"] == 0
    assert payload["side_effects"]["registry_updates"] == 0
    assert payload["lock_status"]["acquired"] is True
    assert payload["lock_status"]["released"] is True


def test_cli_nightly_recheck_batch_bounded_output(tmp_path: Path) -> None:
    project_path, selection = _empty_project(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-recheck-batch",
            "--project",
            str(project_path),
            "--selection",
            str(selection),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)["result"]
    assert len(payload["packet_samples"]) <= 25
    assert len(payload["blocker_classes"]) <= 25
    assert len(payload["warnings"]) <= 25
    assert len(payload["errors"]) <= 25
    assert len(payload["blockers"]) <= 25


def test_cli_nightly_recheck_batch_non_empty_prefect_unavailable_blocks(tmp_path: Path) -> None:
    project_path, selection = _non_empty_project(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "nightly-recheck-batch",
            "--project",
            str(project_path),
            "--selection",
            str(selection),
            "--json",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PREFECT_API_URL": "http://127.0.0.1:9/api"},
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)["result"]
    assert payload["preflight_status"] == "blocked"
    assert "prefect_binding" in payload["blocker_classes"]
    assert payload["side_effects"]["prefect_runs_created"] == 0
    assert payload["side_effects"]["live_agents_started"] == 0
