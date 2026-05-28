"""Tests for GRACE structured logger envelope."""

from __future__ import annotations

import json
import re
import subprocess
import sys

from prefect_grace.platform.log_collector import LogCollector
from prefect_grace.platform.evidence_manifest import validate_execution_trace_jsonl
from prefect_grace.platform.structured_logger import REQUIRED_ENVELOPE_FIELDS, StructuredLogger


def test_structured_logger_writes_canonical_envelope(tmp_path):
    """Structured logger emits required GRACE Canon envelope fields."""
    collector = LogCollector(artifact_root=tmp_path, packet_id="PACKET-1")
    logger = StructuredLogger(
        trace_id="TRACE-PACKET-1-ATTEMPT-001",
        scenario_id="SCN-UNIT",
        packet_id="PACKET-1",
        attempt=1,
        collector=collector,
    )

    envelope = logger.log_event(
        module="M-GRACE-TEST",
        fn="test_fn",
        block="UNIT",
        event="started",
        result="ok",
        detail="value",
    )

    assert envelope is not None
    assert REQUIRED_ENVELOPE_FIELDS.issubset(envelope)
    assert envelope["packet_id"] == "PACKET-1"
    assert envelope["attempt"] == 1
    assert envelope["timestamp"].endswith("Z")
    assert re.match(r"^\d{4}-\d{2}-\d{2}T.*Z$", envelope["timestamp"])

    rows = [json.loads(line) for line in collector.path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["event"] == "started"
    assert rows[0]["detail"] == "value"
    assert validate_execution_trace_jsonl(collector.path) == []


def test_structured_logger_bounds_extra_fields(tmp_path):
    """Extra fields are bounded and core envelope fields cannot be overridden."""
    collector = LogCollector(artifact_root=tmp_path, packet_id="PACKET-2")
    logger = StructuredLogger(
        trace_id="TRACE-PACKET-2-ATTEMPT-001",
        scenario_id="SCN-UNIT",
        packet_id="PACKET-2",
        attempt=1,
        collector=collector,
    )

    extra = {f"k{i:02d}": i for i in range(40)}
    extra["trace_id"] = "bad"
    envelope = logger.log_event(
        module="M-GRACE-TEST",
        fn="test_fn",
        block="UNIT",
        event="bounded",
        result="ok",
        **extra,
    )

    assert envelope is not None
    assert envelope["trace_id"] == "TRACE-PACKET-2-ATTEMPT-001"
    assert envelope["extra_fields_truncated"] is True
    assert len([key for key in envelope if key.startswith("k")]) <= 32


def test_structured_logger_is_fail_safe_when_collector_fails():
    """Collector failures do not escape packet execution."""
    class FailingCollector:
        def collect(self, entry):
            raise RuntimeError("collector failed")

    logger = StructuredLogger(
        trace_id="TRACE-PACKET-3-ATTEMPT-001",
        scenario_id="SCN-UNIT",
        packet_id="PACKET-3",
        attempt=1,
        collector=FailingCollector(),
    )

    assert logger.log_event(
        module="M-GRACE-TEST",
        fn="test_fn",
        block="UNIT",
        event="fail_safe",
        result="ok",
    ) is None
    assert logger.failures


def test_cli_rejects_invalid_manifest_local_execution_trace(tmp_path):
    """CLI manifest validation rejects invalid manifest-local execution traces."""
    packet = tmp_path / "EXECUTION_PACKET.md"
    packet.write_text(
        """# Execution Packet: FEAT-TRACE-W01-PACKET

## Objective
Validate trace artifact format.

## Slice
- packet_id: `FEAT-TRACE-W01-PACKET`
- feature_id: `FEAT-TRACE`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- tests/example.py

## Frozen Scope
- backend/**

## Must Preserve
- Trace artifacts are format validated.

## Verification
pytest

## Expected Evidence
- execution_trace.jsonl

## Escalation Triggers
- Invalid trace accepted
""",
        encoding="utf-8",
    )
    manifest = tmp_path / "evidence_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "packet_id": "FEAT-TRACE-W01-PACKET",
                "generated_by": "pytest",
                "evidence": [
                    {
                        "id": "EV-TRACE-001",
                        "status": "collected",
                        "stage": "packet_local",
                        "producer": "pytest",
                        "artifact_paths": ["execution_trace.jsonl"],
                        "summary": "Invalid trace proof",
                    }
                ],
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "execution_trace.jsonl").write_text("{bad-json}\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "validate-evidence-manifest",
            str(manifest),
            "--packet",
            str(packet),
            "--artifact-root",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    errors = payload["data"]["contract_validation"]["errors"]
    assert any(error["code"] == "execution_trace_invalid_json" for error in errors)
    assert payload["data"]["artifact_validation"]["ok"] is True


def test_cli_rejects_invalid_repo_relative_execution_trace(tmp_path):
    """CLI rejects invalid traces resolved only through --artifact-root."""
    artifact_root = tmp_path / "root"
    manifest_dir = tmp_path / "manifestdir"
    trace_rel = "prefect_grace/packets/PKT/EVIDENCE/attempt-0001/PKT/execution_trace.jsonl"
    trace_path = artifact_root / trace_rel
    trace_path.parent.mkdir(parents=True)
    manifest_dir.mkdir()
    trace_path.write_text("{bad-json}\n", encoding="utf-8")

    packet = tmp_path / "EXECUTION_PACKET.md"
    packet.write_text(
        """# Execution Packet: FEAT-TRACE-W01-PACKET

## Objective
Validate repo-relative trace artifact format.

## Slice
- packet_id: `FEAT-TRACE-W01-PACKET`
- feature_id: `FEAT-TRACE`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- tests/example.py

## Frozen Scope
- backend/**

## Must Preserve
- Trace artifacts are format validated.

## Verification
pytest

## Expected Evidence
- execution_trace.jsonl

## Escalation Triggers
- Invalid trace accepted
""",
        encoding="utf-8",
    )
    manifest = manifest_dir / "evidence_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "packet_id": "FEAT-TRACE-W01-PACKET",
                "generated_by": "pytest",
                "evidence": [
                    {
                        "id": "EV-TRACE-001",
                        "status": "collected",
                        "stage": "packet_local",
                        "producer": "pytest",
                        "artifact_paths": [trace_rel],
                        "summary": "Invalid repo-relative trace proof",
                    }
                ],
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "validate-evidence-manifest",
            str(manifest),
            "--packet",
            str(packet),
            "--artifact-root",
            str(artifact_root),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    errors = payload["data"]["contract_validation"]["errors"]
    assert any(error["code"] == "execution_trace_invalid_json" for error in errors)
    assert payload["data"]["artifact_validation"]["ok"] is True
