import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from prefect_grace.platform.packet_parser import (
    PACKET_SIDECAR_NAME,
    dump_packet_sidecar_payload,
    packet_to_canonical_sidecar_payload,
    parse_packet_markdown,
)
from prefect_grace.platform.packet_yaml_sidecar_migration_apply import (
    APPROVAL_ENV_NAME,
    APPROVAL_ENV_VALUE,
    apply_packet_yaml_sidecar_migration,
)
from prefect_grace.platform.state_store import PacketRegistryStore


def _packet_markdown(packet_id: str) -> str:
    feature_id = packet_id.split("-W01-", 1)[0]
    return f"""# Execution Packet: {packet_id}

## Slice
- packet_id: {packet_id}
- feature_id: {feature_id}
- wave_id: W01
- status: ready
- phase: PHASE-TEST
- depends_on: FEAT-DEP-W01-PACKET

## Objective
Apply YAML sidecar migration safely.

## Impacted Modules
- M-SIDECAR-MIGRATION

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**

## Must Preserve
- Apply must not mutate markdown.

## Verification
python3 -m pytest tests/test_prefect_grace_packet_yaml_sidecar_migration_apply.py

## Expected Evidence
- targeted_pytest.txt

## Escalation Triggers
- Unfiltered bulk apply.
"""


def _write_packet(root: Path, name: str, packet_id: str | None = None) -> Path:
    packet_id = packet_id or f"FEAT-MIGRATION-APPLY-{name.upper()}-W01-PACKET"
    packet_dir = root / name
    packet_dir.mkdir()
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(_packet_markdown(packet_id), encoding="utf-8")
    return packet_path


def _canonical_payload(packet_path: Path) -> dict:
    parsed = parse_packet_markdown(packet_path.read_text(encoding="utf-8"), mode="strict")
    return packet_to_canonical_sidecar_payload(parsed)


def _write_stale_sidecar(packet_path: Path) -> Path:
    stale_payload = _canonical_payload(packet_path)
    stale_payload["depends_on"] = ["STALE-DEP"]
    sidecar_path = packet_path.with_name(PACKET_SIDECAR_NAME)
    sidecar_path.write_text(dump_packet_sidecar_payload(stale_payload), encoding="utf-8")
    return sidecar_path


def _write_project(tmp_path: Path) -> Path:
    state_root = tmp_path / "runtime"
    project_path = tmp_path / "project.yaml"
    project_path.write_text(
        "\n".join(
            [
                "version: 1",
                "project_key: test-project",
                f"repo_root: {tmp_path}",
                "default_branch: main",
                "grace_dir: grace",
                f"packets_dir: {tmp_path / 'packets'}",
                f"runtime_state_root: {state_root}",
                f"artifact_root: {state_root / 'artifacts'}",
                f"worktree_root: {state_root / 'worktrees'}",
                "workflow_runtime: prefect",
                "prefect:",
                "  work_pool: test-process",
                "  live_queue: test-live",
                "  monitoring_queue: test-monitoring",
                "agent_executor:",
                "  default: codex-cli",
                "  command: codex1",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return project_path


def _registry(project_path: Path) -> PacketRegistryStore:
    data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    return PacketRegistryStore(Path(data["runtime_state_root"]) / "state")


def test_requires_explicit_selection(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    _write_packet(packet_root, "missing", "FEAT-MIGRATION-APPLY-MISSING-W01-PACKET")

    result = apply_packet_yaml_sidecar_migration(packet_root, project=_write_project(tmp_path))

    assert result.ok is False
    assert result.errors[0]["code"] == "SELECTION_REQUIRED"
    assert result.writes == []
    assert result.source_mutations == []
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0


def test_dry_run_stale_only_selects_updates_without_writes(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    stale_packet = _write_packet(packet_root, "stale", "FEAT-MIGRATION-APPLY-STALE-W01-PACKET")
    missing_packet = _write_packet(packet_root, "missing", "FEAT-MIGRATION-APPLY-MISSING-W01-PACKET")
    _write_stale_sidecar(stale_packet)
    project_path = _write_project(tmp_path)

    result = apply_packet_yaml_sidecar_migration(
        packet_root,
        project=project_path,
        stale_only=True,
        apply=False,
    )

    assert result.ok is True
    assert result.dry_run is True
    assert result.apply is False
    assert result.plan_count == 2
    assert result.selected_count == 1
    assert result.selected_items[0]["packet_id"] == "FEAT-MIGRATION-APPLY-STALE-W01-PACKET"
    assert result.selected_items[0]["planned_action"] == "update"
    assert result.writes == []
    assert result.source_mutations == []
    assert not missing_packet.with_name(PACKET_SIDECAR_NAME).exists()


def test_apply_source_hash_change_requires_ack_and_env(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "stale", "FEAT-MIGRATION-APPLY-GATED-W01-PACKET")
    sidecar_path = _write_stale_sidecar(packet_path)
    before = sidecar_path.read_text(encoding="utf-8")

    result = apply_packet_yaml_sidecar_migration(
        packet_root,
        project=_write_project(tmp_path),
        stale_only=True,
        apply=True,
        limit=1,
    )

    assert result.ok is False
    assert {error["code"] for error in result.errors} == {
        "SOURCE_HASH_CHANGE_ACK_REQUIRED",
        "SOURCE_HASH_CHANGE_APPROVAL_REQUIRED",
    }
    assert sidecar_path.read_text(encoding="utf-8") == before
    assert result.writes == []
    assert result.source_mutations == []


def test_apply_writes_selected_stale_sidecar_with_all_gates(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "stale", "FEAT-MIGRATION-APPLY-WRITE-W01-PACKET")
    sidecar_path = _write_stale_sidecar(packet_path)
    project_path = _write_project(tmp_path)
    _registry(project_path).upsert_packet(
        {
            "packet_id": "FEAT-MIGRATION-APPLY-WRITE-W01-PACKET",
            "registry_status": "accepted",
            "source_hash": "sha256:old",
        }
    )

    result = apply_packet_yaml_sidecar_migration(
        packet_root,
        project=project_path,
        stale_only=True,
        apply=True,
        limit=1,
        understand_source_hash_change=True,
        approval_token=APPROVAL_ENV_VALUE,
    )

    assert result.ok is True
    assert result.writes == [str(sidecar_path)]
    assert result.source_mutations == [str(sidecar_path)]
    assert result.markdown_mutations == []
    assert result.registry_mutations == []
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert yaml.safe_load(sidecar_path.read_text(encoding="utf-8")) == _canonical_payload(packet_path)


def test_apply_fails_when_selected_items_exceed_limit(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    first = _write_packet(packet_root, "stale-a", "FEAT-MIGRATION-APPLY-LIMIT-A-W01-PACKET")
    second = _write_packet(packet_root, "stale-b", "FEAT-MIGRATION-APPLY-LIMIT-B-W01-PACKET")
    first_sidecar = _write_stale_sidecar(first)
    second_sidecar = _write_stale_sidecar(second)
    before = {
        first_sidecar: first_sidecar.read_text(encoding="utf-8"),
        second_sidecar: second_sidecar.read_text(encoding="utf-8"),
    }

    result = apply_packet_yaml_sidecar_migration(
        packet_root,
        project=_write_project(tmp_path),
        stale_only=True,
        apply=True,
        limit=1,
        understand_source_hash_change=True,
        approval_token=APPROVAL_ENV_VALUE,
    )

    assert result.ok is False
    assert any(error["code"] == "APPLY_LIMIT_EXCEEDED" for error in result.errors)
    assert result.selected_count == 2
    assert result.writes == []
    assert first_sidecar.read_text(encoding="utf-8") == before[first_sidecar]
    assert second_sidecar.read_text(encoding="utf-8") == before[second_sidecar]


def test_apply_rejects_limit_above_hard_max(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "stale", "FEAT-MIGRATION-APPLY-HARD-MAX-W01-PACKET")
    sidecar_path = _write_stale_sidecar(packet_path)
    before = sidecar_path.read_text(encoding="utf-8")

    result = apply_packet_yaml_sidecar_migration(
        packet_root,
        project=_write_project(tmp_path),
        stale_only=True,
        apply=True,
        limit=11,
        understand_source_hash_change=True,
        approval_token=APPROVAL_ENV_VALUE,
    )

    assert result.ok is False
    assert any(error["code"] == "APPLY_LIMIT_TOO_HIGH" for error in result.errors)
    assert result.writes == []
    assert sidecar_path.read_text(encoding="utf-8") == before


def test_explicit_packet_id_can_select_missing_sidecar_in_dry_run(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "missing", "FEAT-MIGRATION-APPLY-EXPLICIT-W01-PACKET")

    result = apply_packet_yaml_sidecar_migration(
        packet_root,
        project=_write_project(tmp_path),
        packet_ids=["FEAT-MIGRATION-APPLY-EXPLICIT-W01-PACKET"],
        apply=False,
    )

    assert result.ok is True
    assert result.selected_count == 1
    assert result.selected_items[0]["planned_action"] == "create"
    assert result.source_hash_change_count == 1
    assert result.writes == []
    assert not packet_path.with_name(PACKET_SIDECAR_NAME).exists()


def test_invalid_selected_sidecar_fails_closed_without_overwrite(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "invalid", "FEAT-MIGRATION-APPLY-INVALID-W01-PACKET")
    sidecar_path = packet_path.with_name(PACKET_SIDECAR_NAME)
    sidecar_path.write_text("- not\n- mapping\n", encoding="utf-8")

    result = apply_packet_yaml_sidecar_migration(
        packet_root,
        project=_write_project(tmp_path),
        packet_ids=["FEAT-MIGRATION-APPLY-INVALID-W01-PACKET"],
        apply=True,
        limit=1,
        understand_source_hash_change=True,
        approval_token=APPROVAL_ENV_VALUE,
    )

    assert result.ok is False
    assert any(error["code"] == "SELECTED_PACKET_INVALID_SIDECAR" for error in result.errors)
    assert result.writes == []
    assert sidecar_path.read_text(encoding="utf-8") == "- not\n- mapping\n"


def test_cli_json_envelope_stale_only_dry_run(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "stale", "FEAT-MIGRATION-APPLY-CLI-W01-PACKET")
    _write_stale_sidecar(packet_path)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "apply-packet-yaml-sidecar-migration",
            "--packet-root",
            str(packet_root),
            "--project",
            str(_write_project(tmp_path)),
            "--stale-only",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout)

    assert data["ok"] is True
    assert data["command"] == "apply-packet-yaml-sidecar-migration"
    assert data["result"] == data["data"]
    assert data["data"]["dry_run"] is True
    assert data["data"]["selected_count"] == 1
    assert data["data"]["writes"] == []
    assert data["data"]["source_mutations"] == []


def test_cli_unfiltered_apply_is_blocked(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    _write_packet(packet_root, "missing", "FEAT-MIGRATION-APPLY-CLI-BLOCKED-W01-PACKET")
    env = dict(os.environ)
    env[APPROVAL_ENV_NAME] = APPROVAL_ENV_VALUE

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "apply-packet-yaml-sidecar-migration",
            "--packet-root",
            str(packet_root),
            "--project",
            str(_write_project(tmp_path)),
            "--apply",
            "--i-understand-source-hash-change",
            "--json",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    data = json.loads(res.stdout)

    assert res.returncode == 1
    assert data["ok"] is False
    assert any(error["code"] == "SELECTION_REQUIRED" for error in data["errors"])
    assert data["data"]["selected_count"] == 0
    assert data["data"]["writes"] == []
    assert data["data"]["prefect_runs_created"] == 0
    assert data["data"]["live_agents_started"] == 0
