import json
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
from prefect_grace.platform.packet_yaml_sidecar_migration_plan import (
    plan_packet_yaml_sidecar_migration,
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
Plan YAML sidecar migration impact.

## Impacted Modules
- M-SIDECAR-MIGRATION

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**

## Must Preserve
- Planner must not write source files.

## Verification
python3 -m pytest tests/test_prefect_grace_packet_yaml_sidecar_migration_plan.py

## Expected Evidence
- targeted_pytest.txt

## Escalation Triggers
- Source mutation.
"""


def _write_packet(root: Path, name: str, packet_id: str | None = None) -> Path:
    packet_id = packet_id or f"FEAT-MIGRATION-{name.upper()}-W01-PACKET"
    packet_dir = root / name
    packet_dir.mkdir()
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(_packet_markdown(packet_id), encoding="utf-8")
    return packet_path


def _canonical_payload(packet_path: Path) -> dict:
    parsed = parse_packet_markdown(packet_path.read_text(encoding="utf-8"), mode="strict")
    return packet_to_canonical_sidecar_payload(parsed)


def _write_canonical_sidecar(packet_path: Path) -> Path:
    sidecar_path = packet_path.with_name(PACKET_SIDECAR_NAME)
    sidecar_path.write_text(dump_packet_sidecar_payload(_canonical_payload(packet_path)), encoding="utf-8")
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


def test_missing_sidecar_accepted_registry_entry_plans_create_with_accepted_hash_risk(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "accepted", "FEAT-MIGRATION-ACCEPTED-W01-PACKET")
    project_path = _write_project(tmp_path)
    _registry(project_path).upsert_packet(
        {
            "packet_id": "FEAT-MIGRATION-ACCEPTED-W01-PACKET",
            "registry_status": "accepted",
            "source_hash": "sha256:old",
        }
    )

    result = plan_packet_yaml_sidecar_migration(packet_root, project=project_path)

    assert result.ok is True
    assert result.registry_loaded is True
    assert result.counts["no_sidecar"] == 1
    assert result.plan_count == 1
    item = result.items[0]
    assert item["packet_id"] == "FEAT-MIGRATION-ACCEPTED-W01-PACKET"
    assert item["packet_path"] == str(packet_path)
    assert item["planned_action"] == "create"
    assert item["registry_status"] == "accepted"
    assert item["source_hash_changes"] is True
    assert item["risk"] == "accepted_source_hash_change"
    assert result.risk_counts == {"accepted_source_hash_change": 1}
    assert result.writes == []
    assert result.source_mutations == []
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert not packet_path.with_name(PACKET_SIDECAR_NAME).exists()


def test_stale_sidecar_plans_update_with_hash_change(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "stale", "FEAT-MIGRATION-STALE-W01-PACKET")
    stale_payload = _canonical_payload(packet_path)
    stale_payload["depends_on"] = ["STALE-DEP"]
    packet_path.with_name(PACKET_SIDECAR_NAME).write_text(
        dump_packet_sidecar_payload(stale_payload),
        encoding="utf-8",
    )

    result = plan_packet_yaml_sidecar_migration(packet_root, project=_write_project(tmp_path))

    assert result.ok is True
    assert result.counts["stale_sidecar"] == 1
    assert result.plan_count == 1
    item = result.items[0]
    assert item["planned_action"] == "update"
    assert item["source_hash_changes"] is True
    assert item["risk"] == "no_registry_entry"
    assert item["current_source_hash"] != item["planned_source_hash"]


def test_canonical_packet_is_counted_but_not_included_in_plan_items(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "canonical", "FEAT-MIGRATION-CANONICAL-W01-PACKET")
    _write_canonical_sidecar(packet_path)

    result = plan_packet_yaml_sidecar_migration(packet_root, project=_write_project(tmp_path))

    assert result.ok is True
    assert result.counts["canonical"] == 1
    assert result.plan_count == 0
    assert result.items == []


def test_invalid_sidecar_is_bounded_finding_with_ok_true(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    packet_path = _write_packet(packet_root, "invalid", "FEAT-MIGRATION-INVALID-W01-PACKET")
    packet_path.with_name(PACKET_SIDECAR_NAME).write_text("- not\n- mapping\n", encoding="utf-8")

    result = plan_packet_yaml_sidecar_migration(packet_root, project=_write_project(tmp_path))

    assert result.ok is True
    assert result.counts["invalid_sidecar"] == 1
    assert result.plan_count == 0
    assert result.errors == []
    assert result.findings[0]["classification"] == "invalid_sidecar"
    assert result.findings[0]["packet_id"] == "FEAT-MIGRATION-INVALID-W01-PACKET"


def test_missing_project_config_warns_and_uses_null_registry_status(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    _write_packet(packet_root, "missing-project", "FEAT-MIGRATION-NOREG-W01-PACKET")

    result = plan_packet_yaml_sidecar_migration(packet_root, project=tmp_path / "missing-project.yaml")

    assert result.ok is True
    assert result.registry_loaded is False
    assert result.warnings[0]["code"] == "PROJECT_CONFIG_UNAVAILABLE"
    assert result.items[0]["registry_status"] is None
    assert result.items[0]["risk"] == "no_registry_entry"


def test_item_limit_caps_display_but_preserves_full_item_count(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    for index in range(3):
        _write_packet(packet_root, f"missing-{index}", f"FEAT-MIGRATION-LIMIT-{index}-W01-PACKET")

    result = plan_packet_yaml_sidecar_migration(packet_root, project=_write_project(tmp_path), limit=2)
    capped = plan_packet_yaml_sidecar_migration(packet_root, project=_write_project(tmp_path), limit=1000)

    assert result.ok is True
    assert result.plan_count == 3
    assert result.full_item_count == 3
    assert len(result.items) == 2
    assert result.items_truncated is True
    assert capped.limit == 100


def test_root_scan_error_fails_ok_false(tmp_path: Path) -> None:
    result = plan_packet_yaml_sidecar_migration(tmp_path / "missing-root", project=tmp_path / "missing.yaml")

    assert result.ok is False
    assert result.errors[0]["code"] == "PACKET_ROOT_NOT_FOUND"
    assert result.writes == []
    assert result.source_mutations == []


def test_cli_json_envelope_shape_and_read_only_fields(tmp_path: Path) -> None:
    packet_root = tmp_path / "packets"
    packet_root.mkdir()
    _write_packet(packet_root, "packet", "FEAT-MIGRATION-CLI-W01-PACKET")
    project_path = _write_project(tmp_path)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "plan-packet-yaml-sidecar-migration",
            "--packet-root",
            str(packet_root),
            "--project",
            str(project_path),
            "--json",
            "--limit",
            "5",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout)

    assert data["ok"] is True
    assert data["command"] == "plan-packet-yaml-sidecar-migration"
    assert data["result"] == data["data"]
    assert data["errors"] == []
    assert data["data"]["plan_count"] == 1
    assert data["data"]["items"][0]["planned_action"] == "create"
    assert data["data"]["writes"] == []
    assert data["data"]["source_mutations"] == []
    assert data["data"]["prefect_runs_created"] == 0
    assert data["data"]["live_agents_started"] == 0
