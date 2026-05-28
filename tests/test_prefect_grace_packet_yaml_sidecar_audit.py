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
from prefect_grace.platform.packet_yaml_sidecar_audit import audit_packet_yaml_sidecars


STRICT_PACKET_MARKDOWN = """# Execution Packet: FEAT-AUDIT-W01-PACKET

## Slice
- packet_id: FEAT-AUDIT-W01-PACKET
- feature_id: FEAT-AUDIT
- wave_id: W01
- status: ready
- phase: PHASE-TEST
- depends_on: FEAT-DEP-W01-PACKET

## Objective
Audit YAML sidecars.

## Impacted Modules
- M-AUDIT

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**

## Must Preserve
- Audit must not write source files.

## Verification
python3 -m pytest tests/test_prefect_grace_packet_yaml_sidecar_audit.py

## Expected Evidence
- targeted_pytest.txt

## Escalation Triggers
- Source mutation.
"""


NON_STRICT_PACKET_MARKDOWN = """# Execution Packet: FEAT-AUDIT-W01-NON-STRICT

## Objective
This packet is intentionally missing strict metadata.
"""


def _write_packet(root: Path, name: str, body: str = STRICT_PACKET_MARKDOWN) -> Path:
    packet_dir = root / name
    packet_dir.mkdir()
    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(body, encoding="utf-8")
    return packet_path


def _canonical_payload(packet_path: Path) -> dict:
    parsed = parse_packet_markdown(packet_path.read_text(encoding="utf-8"), mode="strict")
    return packet_to_canonical_sidecar_payload(parsed)


def _write_canonical_sidecar(packet_path: Path) -> Path:
    sidecar_path = packet_path.with_name(PACKET_SIDECAR_NAME)
    sidecar_path.write_text(dump_packet_sidecar_payload(_canonical_payload(packet_path)), encoding="utf-8")
    return sidecar_path


def test_audit_classifies_canonical_no_sidecar_stale_invalid_and_skipped(tmp_path: Path) -> None:
    canonical_packet = _write_packet(tmp_path, "canonical")
    _write_canonical_sidecar(canonical_packet)

    no_sidecar_packet = _write_packet(tmp_path, "missing")

    stale_packet = _write_packet(tmp_path, "stale")
    stale_payload = _canonical_payload(stale_packet)
    stale_payload["depends_on"] = ["STALE-DEP"]
    stale_packet.with_name(PACKET_SIDECAR_NAME).write_text(
        dump_packet_sidecar_payload(stale_payload),
        encoding="utf-8",
    )

    invalid_packet = _write_packet(tmp_path, "invalid")
    invalid_packet.with_name(PACKET_SIDECAR_NAME).write_text(
        "schema_version: 1\nartifact_type: execution_packet\npacket_id: FEAT-OTHER-W01-PACKET\n",
        encoding="utf-8",
    )

    skipped_packet = _write_packet(tmp_path, "skipped", NON_STRICT_PACKET_MARKDOWN)

    result = audit_packet_yaml_sidecars(tmp_path)

    assert result.ok is True
    assert result.packets_total == 5
    assert result.counts == {
        "canonical": 1,
        "no_sidecar": 1,
        "stale_sidecar": 1,
        "invalid_sidecar": 1,
        "skipped": 1,
    }
    assert result.examples["canonical"][0]["packet"] == str(canonical_packet)
    assert result.examples["no_sidecar"][0]["packet"] == str(no_sidecar_packet)
    assert result.examples["stale_sidecar"][0]["packet"] == str(stale_packet)
    assert result.examples["invalid_sidecar"][0]["packet"] == str(invalid_packet)
    assert result.examples["skipped"][0]["packet"] == str(skipped_packet)
    assert result.errors[0]["code"] == "INVALID_PACKET_YAML_SIDECAR"


def test_root_missing_fails_closed(tmp_path: Path) -> None:
    result = audit_packet_yaml_sidecars(tmp_path / "missing-root")

    assert result.ok is False
    assert result.packets_total == 0
    assert result.counts["canonical"] == 0
    assert result.errors[0]["code"] == "PACKET_ROOT_NOT_FOUND"
    assert result.writes == []
    assert result.source_mutations == []
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0


def test_examples_and_errors_are_capped_by_limit(tmp_path: Path) -> None:
    for index in range(3):
        packet_path = _write_packet(tmp_path, f"invalid-{index}")
        packet_path.with_name(PACKET_SIDECAR_NAME).write_text(
            "schema_version: 1\nartifact_type: execution_packet\npacket_id: FEAT-OTHER-W01-PACKET\n",
            encoding="utf-8",
        )

    result = audit_packet_yaml_sidecars(tmp_path, limit=2)

    assert result.ok is True
    assert result.counts["invalid_sidecar"] == 3
    assert len(result.examples["invalid_sidecar"]) == 2
    assert len(result.errors) == 2


def test_limit_is_capped_at_100(tmp_path: Path) -> None:
    result = audit_packet_yaml_sidecars(tmp_path, limit=1000)

    assert result.limit == 100


def test_audit_is_read_only_and_discovers_only_execution_packet_markdown(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path, "packet")
    fragment = tmp_path / "packet" / "OTHER_PACKET.md"
    fragment.write_text(STRICT_PACKET_MARKDOWN, encoding="utf-8")
    before_files = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    before_markdown = packet_path.read_bytes()

    result = audit_packet_yaml_sidecars(tmp_path)

    after_files = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    assert result.ok is True
    assert result.packets_total == 1
    assert result.counts["no_sidecar"] == 1
    assert result.writes == []
    assert result.source_mutations == []
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert after_files == before_files
    assert packet_path.read_bytes() == before_markdown


def test_cli_json_envelope_shape(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path, "packet")
    _write_canonical_sidecar(packet_path)

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "audit-packet-yaml-sidecars",
            "--packet-root",
            str(tmp_path),
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
    assert data["command"] == "audit-packet-yaml-sidecars"
    assert data["result"] == data["data"]
    assert data["errors"] == []
    assert data["data"]["packets_total"] == 1
    assert data["data"]["counts"]["canonical"] == 1
    assert data["data"]["writes"] == []
    assert data["data"]["source_mutations"] == []
    assert data["data"]["prefect_runs_created"] == 0
    assert data["data"]["live_agents_started"] == 0


def test_invalid_yaml_sidecar_is_a_finding_not_cli_failure(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path, "packet")
    packet_path.with_name(PACKET_SIDECAR_NAME).write_text("- not\n- mapping\n", encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "audit-packet-yaml-sidecars",
            "--packet-root",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout)

    assert data["ok"] is True
    assert data["data"]["counts"]["invalid_sidecar"] == 1
    assert data["errors"][0]["code"] == "INVALID_PACKET_YAML_SIDECAR"


def test_stale_sidecar_is_not_rewritten(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path, "packet")
    sidecar_path = packet_path.with_name(PACKET_SIDECAR_NAME)
    sidecar_payload = _canonical_payload(packet_path)
    sidecar_payload["depends_on"] = ["STALE-DEP"]
    sidecar_path.write_text(yaml.safe_dump(sidecar_payload, sort_keys=False), encoding="utf-8")
    before = sidecar_path.read_bytes()

    result = audit_packet_yaml_sidecars(tmp_path)

    assert result.ok is True
    assert result.counts["stale_sidecar"] == 1
    assert sidecar_path.read_bytes() == before
