import json
import subprocess
import sys
from pathlib import Path

import yaml

from prefect_grace.platform.packet_parser import parse_packet_markdown
from prefect_grace.platform.packet_yaml_sidecar_sync import sync_packet_yaml_sidecars


STRICT_PACKET_MARKDOWN = """# Execution Packet: FEAT-SIDECAR-W01-PACKET

## Slice
- packet_id: FEAT-SIDECAR-W01-PACKET
- feature_id: FEAT-SIDECAR
- wave_id: W01
- status: ready
- phase: PHASE-TEST
- depends_on: FEAT-DEP-W01-PACKET

## Objective
Synchronize YAML sidecars.

## Impacted Modules
- M-SIDECAR

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**

## Must Preserve
- Markdown must not change.

## Verification
python3 -m pytest tests/test_prefect_grace_packet_yaml_sidecar_sync.py

## Expected Evidence
- targeted_pytest.txt

## Escalation Triggers
- Markdown mutation.
"""


def _write_packet(root: Path, name: str = "packet") -> Path:
    packet_dir = root / name
    packet_dir.mkdir()
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(STRICT_PACKET_MARKDOWN, encoding="utf-8")
    return packet_path


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_dry_run_create_writes_no_file(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)

    result = sync_packet_yaml_sidecars([packet_path])

    assert result.ok is True
    assert result.dry_run is True
    assert result.results[0]["planned_action"] == "create"
    assert result.writes == []
    assert result.markdown_mutations == []
    assert not packet_path.with_name("EXECUTION_PACKET.yaml").exists()


def test_apply_create_writes_yaml_and_leaves_markdown_byte_identical(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    before = packet_path.read_bytes()

    result = sync_packet_yaml_sidecars([packet_path], apply=True)

    assert result.ok is True
    assert result.results[0]["planned_action"] == "create"
    assert result.writes == [str(packet_path.with_name("EXECUTION_PACKET.yaml"))]
    assert result.markdown_mutations == []
    assert packet_path.read_bytes() == before

    sidecar = _load_yaml(packet_path.with_name("EXECUTION_PACKET.yaml"))
    assert list(sidecar) == [
        "schema_version",
        "artifact_type",
        "packet_id",
        "feature_id",
        "wave_id",
        "title",
        "objective",
        "status",
        "phase",
        "depends_on",
        "modules",
        "allowed_write_scope",
        "frozen_scope",
        "must_preserve",
        "verification",
        "expected_evidence",
        "escalation_triggers",
    ]
    assert sidecar["packet_id"] == "FEAT-SIDECAR-W01-PACKET"
    assert parse_packet_markdown(packet_path, mode="strict").packet_id == "FEAT-SIDECAR-W01-PACKET"


def test_second_dry_run_after_apply_returns_noop(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)

    apply_result = sync_packet_yaml_sidecars([packet_path], apply=True)
    dry_run_result = sync_packet_yaml_sidecars([packet_path])

    assert apply_result.ok is True
    assert dry_run_result.ok is True
    assert dry_run_result.results[0]["planned_action"] == "noop"
    assert dry_run_result.writes == []


def test_valid_stale_sidecar_returns_update_and_apply_updates(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    sidecar_path = packet_path.with_name("EXECUTION_PACKET.yaml")
    sidecar_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1",
                "artifact_type": "execution_packet",
                "packet_id": "FEAT-SIDECAR-W01-PACKET",
                "depends_on": ["STALE-DEP"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    dry_run_result = sync_packet_yaml_sidecars([packet_path])
    assert dry_run_result.ok is True
    assert dry_run_result.results[0]["planned_action"] == "update"
    assert _load_yaml(sidecar_path)["depends_on"] == ["STALE-DEP"]

    apply_result = sync_packet_yaml_sidecars([packet_path], apply=True)
    assert apply_result.ok is True
    assert apply_result.results[0]["planned_action"] == "update"
    assert _load_yaml(sidecar_path)["depends_on"] == ["FEAT-DEP-W01-PACKET"]


def test_invalid_sidecars_return_error_and_are_not_overwritten(tmp_path: Path) -> None:
    cases = {
        "malformed": "schema_version: 1\nartifact_type: [execution_packet\n",
        "unknown": "schema_version: 1\nartifact_type: execution_packet\npacket_id: FEAT-SIDECAR-W01-PACKET\ntypo: true\n",
        "mismatch": "schema_version: 1\nartifact_type: execution_packet\npacket_id: FEAT-OTHER-W01-PACKET\n",
        "non_mapping": "- not\n- mapping\n",
    }

    for case_name, sidecar_text in cases.items():
        packet_path = _write_packet(tmp_path, case_name)
        sidecar_path = packet_path.with_name("EXECUTION_PACKET.yaml")
        sidecar_path.write_text(sidecar_text, encoding="utf-8")
        before = sidecar_path.read_bytes()

        result = sync_packet_yaml_sidecars([packet_path], apply=True)

        assert result.ok is False
        assert result.results[0]["planned_action"] == "error"
        assert result.writes == []
        assert sidecar_path.read_bytes() == before


def test_multiple_packets_produce_bounded_result_list(tmp_path: Path) -> None:
    first = _write_packet(tmp_path, "first")
    second = _write_packet(tmp_path, "second")

    result = sync_packet_yaml_sidecars([first, second])

    assert result.ok is True
    assert result.packets_total == 2
    assert len(result.results) == 2
    assert [item["planned_action"] for item in result.results] == ["create", "create"]


def test_invalid_packet_path_fails_closed(tmp_path: Path) -> None:
    wrong_name = tmp_path / "PACKET.md"
    wrong_name.write_text(STRICT_PACKET_MARKDOWN, encoding="utf-8")

    result = sync_packet_yaml_sidecars(["", wrong_name])

    assert result.ok is False
    assert len(result.results) == 2
    assert [item["planned_action"] for item in result.results] == ["error", "error"]
    assert result.writes == []


def test_cli_json_envelope_result_shape(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "sync-packet-yaml-sidecar",
            "--packet",
            str(packet_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout)

    assert data["ok"] is True
    assert data["command"] == "sync-packet-yaml-sidecar"
    assert data["result"] == data["data"]
    assert data["errors"] == []
    assert data["data"]["dry_run"] is True
    assert data["data"]["apply"] is False
    assert data["data"]["writes"] == []
    assert data["data"]["markdown_mutations"] == []
    assert data["data"]["results"][0]["planned_action"] == "create"
    assert not packet_path.with_name("EXECUTION_PACKET.yaml").exists()


def test_source_hash_changes_after_sidecar_creation(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    markdown_only = parse_packet_markdown(packet_path, mode="strict")

    result = sync_packet_yaml_sidecars([packet_path], apply=True)
    with_sidecar = parse_packet_markdown(packet_path, mode="strict")

    assert result.ok is True
    assert with_sidecar.source_hash != markdown_only.source_hash
