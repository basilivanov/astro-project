from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

import yaml

from prefect_grace.platform.packet_parser import parse_packet_markdown


def _packet_text(packet_id: str) -> str:
    feature_id = packet_id.split("-W", 1)[0]
    return f"""# Execution Packet: {packet_id}

## Objective

Implement a bounded CLI audit test packet.

## Slice

- packet_id: `{packet_id}`
- feature_id: `{feature_id}`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-TEST`

## Allowed Write Scope

- prefect_grace/platform/example.py

## Frozen Scope

- backend/**

## Must Preserve

- Runtime registry is read-only.

## Verification

pytest -q tests/test_prefect_grace_cli_registry_source_integrity_audit.py

## Expected Evidence

- pytest output

## Escalation Triggers

- missing source
"""


def _write_project(repo: Path) -> Path:
    project = repo / "prefect_grace" / "project.yaml"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        f"""version: 1
project_key: test-project
repo_root: {repo}
default_branch: test
grace_dir: grace
packets_dir: prefect_grace/packets
runtime_state_root: {repo / "runtime"}
artifact_root: {repo / "runtime" / "artifacts"}
worktree_root: {repo / "runtime" / "worktrees"}
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
    return project


def _write_clean_packet(repo: Path, packet_id: str) -> tuple[Path, str]:
    feature_id = packet_id.split("-W", 1)[0]
    packet_dir = repo / "prefect_grace" / "packets" / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    source = packet_dir / "EXECUTION_PACKET.md"
    source.write_text(_packet_text(packet_id), encoding="utf-8")
    parsed = parse_packet_markdown(source, mode="strict")
    reviews = packet_dir / "REVIEWS"
    reviews.mkdir()
    (reviews / "review-0001.md").write_text("verdict: accepted\n", encoding="utf-8")
    evidence = packet_dir / "EVIDENCE" / "attempt-0001"
    evidence.mkdir(parents=True)
    (evidence / "evidence_manifest.json").write_text(
        json.dumps({"packet_id": packet_id, "generated_by": "pytest", "evidence": [], "blockers": []}),
        encoding="utf-8",
    )
    return source, parsed.source_hash


def _write_registry(repo: Path, record: dict) -> None:
    state = repo / "runtime" / "state"
    state.mkdir(parents=True)
    (state / "packet_registry.yaml").write_text(yaml.safe_dump({record["packet_id"]: record}), encoding="utf-8")


def test_cli_json_envelope_and_exit_zero_when_clean(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-CLI-CLEAN-W01-PACKET"
    source, source_hash = _write_clean_packet(tmp_path, packet_id)
    _write_registry(
        tmp_path,
        {
            "packet_id": packet_id,
            "path": str(source.relative_to(tmp_path)),
            "registry_status": "accepted",
            "source_hash": source_hash,
        },
    )
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, text=True, check=True)
    subprocess.run(["git", "add", str(source.relative_to(tmp_path))], cwd=tmp_path, capture_output=True, text=True, check=True)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "registry-source-integrity-audit",
            "--project",
            str(project),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "registry-source-integrity-audit"
    assert payload["result"] == payload["data"]
    assert payload["data"]["ok"] is True


def test_cli_exits_one_when_blocking_issues_exist(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    packet_id = "FEAT-CLI-MISSING-W01-PACKET"
    _write_registry(
        tmp_path,
        {
            "packet_id": packet_id,
            "path": "prefect_grace/packets/FEAT-CLI-MISSING/EXECUTION_PACKET.md",
            "registry_status": "accepted",
            "source_hash": "sha256:missing",
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "registry-source-integrity-audit",
            "--project",
            str(project),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["result"] == payload["data"]
    assert payload["data"]["issue_counts"]["source_missing"] == 1
