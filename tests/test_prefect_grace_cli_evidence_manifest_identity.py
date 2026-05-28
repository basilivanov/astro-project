import json
import subprocess
import sys
from pathlib import Path


PACKET_ID = "FEAT-IDENTITY-W01-STRICT-PACKET-ID"


def _write_packet(path: Path) -> None:
    path.write_text(
        f"""# Execution Packet: {PACKET_ID}

## Objective
Validate evidence manifest identity.

## Slice
- packet_id: `{PACKET_ID}`
- feature_id: `FEAT-IDENTITY`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- tests/example.py

## Frozen Scope
- backend/**

## Must Preserve
- Manifest identity validation fails closed.

## Verification
pytest

## Expected Evidence
- evidence manifest

## Escalation Triggers
- identity mismatch accepted
""",
        encoding="utf-8",
    )


def _write_manifest(path: Path, packet_id: str, *, legacy: bool = False) -> None:
    item = {
        "id": "EV-IDENTITY-001",
        "status": "collected",
        "stage": "packet_local",
        "producer": "pytest",
        "artifact_paths": ["identity_artifact.txt"],
        "summary": "Identity validation proof",
    }
    payload = {
        "packet_id": packet_id,
        "generated_by": "pytest",
        "blockers": [],
    }
    if legacy:
        payload["requirement_results"] = [item]
    else:
        payload["evidence"] = [item]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_validate(manifest: Path, packet: Path, artifact_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
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


def _error_codes(payload: dict) -> set[str]:
    errors = payload["data"]["contract_validation"]["errors"]
    return {error["code"] for error in errors}


def test_cli_validate_evidence_manifest_rejects_unknown_packet_id(tmp_path: Path) -> None:
    packet = tmp_path / "EXECUTION_PACKET.md"
    evidence_dir = tmp_path / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest = evidence_dir / "evidence_manifest.json"
    (evidence_dir / "identity_artifact.txt").write_text("proof", encoding="utf-8")
    _write_packet(packet)
    _write_manifest(manifest, "UNKNOWN")

    result = _run_validate(manifest, packet, tmp_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["result"] == payload["data"]
    assert "manifest_packet_id_unknown" in _error_codes(payload)


def test_cli_validate_evidence_manifest_rejects_packet_id_mismatch(tmp_path: Path) -> None:
    packet = tmp_path / "EXECUTION_PACKET.md"
    evidence_dir = tmp_path / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest = evidence_dir / "evidence_manifest.json"
    (evidence_dir / "identity_artifact.txt").write_text("proof", encoding="utf-8")
    _write_packet(packet)
    _write_manifest(manifest, "FEAT-IDENTITY-W01-OTHER")

    result = _run_validate(manifest, packet, tmp_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["result"] == payload["data"]
    assert "manifest_packet_id_mismatch" in _error_codes(payload)


def test_cli_validate_evidence_manifest_accepts_matching_legacy_requirement_results(
    tmp_path: Path,
) -> None:
    packet = tmp_path / "EXECUTION_PACKET.md"
    evidence_dir = tmp_path / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest = evidence_dir / "evidence_manifest.json"
    (evidence_dir / "identity_artifact.txt").write_text("proof", encoding="utf-8")
    _write_packet(packet)
    _write_manifest(manifest, PACKET_ID, legacy=True)

    result = _run_validate(manifest, packet, tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"] == payload["data"]
    assert payload["data"]["evidence_count"] == 1
    assert payload["data"]["artifact_validation"]["ok"] is True
