import json
import subprocess
import sys
from pathlib import Path


def _write_packet(path: Path) -> None:
    path.write_text(
        """# Execution Packet: FEAT-PATH-W01-PACKET

## Objective
Validate evidence manifest path resolution.

## Slice
- packet_id: `FEAT-PATH-W01-PACKET`
- feature_id: `FEAT-PATH`
- wave_id: `W01`
- status: `ready`

## Allowed Write Scope
- tests/example.py

## Frozen Scope
- backend/**

## Must Preserve
- Path containment remains enforced.

## Verification
pytest

## Expected Evidence
- evidence manifest

## Escalation Triggers
- traversal accepted
""",
        encoding="utf-8",
    )


def _write_manifest(path: Path, artifact_paths: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "packet_id": "FEAT-PATH-W01-PACKET",
                "generated_by": "pytest",
                "evidence": [
                    {
                        "id": "EV-PATH-001",
                        "status": "collected",
                        "stage": "packet_local",
                        "producer": "pytest",
                        "artifact_paths": artifact_paths,
                        "summary": "Path resolution proof",
                    }
                ],
                "blockers": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


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


def test_cli_validate_evidence_manifest_accepts_manifest_local_artifact(tmp_path: Path) -> None:
    packet = tmp_path / "EXECUTION_PACKET.md"
    evidence_dir = tmp_path / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest = evidence_dir / "evidence_manifest.json"
    artifact = evidence_dir / "targeted_pytest.txt"
    artifact.write_text("1 passed", encoding="utf-8")
    _write_packet(packet)
    _write_manifest(manifest, ["targeted_pytest.txt"])

    result = _run_validate(manifest, packet, tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"] == payload["data"]
    assert payload["data"]["artifact_validation"]["ok"] is True
    assert payload["data"]["artifact_validation"]["missing_artifacts"] == []


def test_cli_validate_evidence_manifest_accepts_repo_relative_artifact(tmp_path: Path) -> None:
    packet = tmp_path / "EXECUTION_PACKET.md"
    evidence_dir = tmp_path / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest = evidence_dir / "evidence_manifest.json"
    artifact = evidence_dir / "targeted_pytest.txt"
    artifact.write_text("1 passed", encoding="utf-8")
    _write_packet(packet)
    _write_manifest(manifest, ["EVIDENCE/attempt-0001/targeted_pytest.txt"])

    result = _run_validate(manifest, packet, tmp_path)

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["result"] == payload["data"]
    assert payload["data"]["artifact_validation"]["ok"] is True


def test_cli_validate_evidence_manifest_rejects_manifest_relative_traversal(tmp_path: Path) -> None:
    packet = tmp_path / "EXECUTION_PACKET.md"
    evidence_dir = tmp_path / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest = evidence_dir / "evidence_manifest.json"
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("outside", encoding="utf-8")
    _write_packet(packet)
    _write_manifest(manifest, ["../../../../etc/passwd"])

    try:
        result = _run_validate(manifest, packet, tmp_path)
    finally:
        outside.unlink(missing_ok=True)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["result"] == payload["data"]
    assert payload["data"]["artifact_validation"]["ok"] is False
    assert "../../../../etc/passwd" in payload["data"]["artifact_validation"]["missing_artifacts"]


def test_cli_validate_evidence_manifest_rejects_absolute_path_outside_root(tmp_path: Path) -> None:
    packet = tmp_path / "EXECUTION_PACKET.md"
    evidence_dir = tmp_path / "EVIDENCE" / "attempt-0001"
    evidence_dir.mkdir(parents=True)
    manifest = evidence_dir / "evidence_manifest.json"
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("outside", encoding="utf-8")
    _write_packet(packet)
    _write_manifest(manifest, [str(outside)])

    try:
        result = _run_validate(manifest, packet, tmp_path)
    finally:
        outside.unlink(missing_ok=True)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["result"] == payload["data"]
    assert payload["data"]["artifact_validation"]["ok"] is False
    assert str(outside) in payload["data"]["artifact_validation"]["missing_artifacts"]
