"""Tests for prefect_grace.platform.evidence_manifest module."""

import pytest
import json
import tempfile
from pathlib import Path
from prefect_grace.platform.evidence_manifest import (
    EvidenceItem,
    EvidenceManifest,
    parse_evidence_manifest,
    validate_evidence_manifest,
    ALLOWED_STATUSES,
)
from prefect_grace.platform.evidence_contract import (
    EvidenceRequirement,
    EvidenceContract,
)


def test_evidence_item_to_dict():
    """Test EvidenceItem serialization."""
    item = EvidenceItem(
        id="EV-TEST-001",
        status="collected",
        stage="packet_local",
        producer="pytest",
        artifact_paths=["test-output.txt"],
        summary="All tests passed",
    )

    data = item.to_dict()

    assert data["id"] == "EV-TEST-001"
    assert data["status"] == "collected"
    assert data["stage"] == "packet_local"
    assert data["producer"] == "pytest"
    assert data["artifact_paths"] == ["test-output.txt"]
    assert data["summary"] == "All tests passed"


def test_evidence_item_from_dict():
    """Test EvidenceItem deserialization."""
    data = {
        "id": "EV-TEST-001",
        "status": "collected",
        "stage": "packet_local",
        "producer": "pytest",
        "artifact_paths": ["test-output.txt"],
        "summary": "All tests passed",
    }

    item = EvidenceItem.from_dict(data)

    assert item.id == "EV-TEST-001"
    assert item.status == "collected"
    assert item.stage == "packet_local"
    assert item.producer == "pytest"
    assert item.artifact_paths == ["test-output.txt"]
    assert item.summary == "All tests passed"


def test_evidence_manifest_to_dict():
    """Test EvidenceManifest serialization."""
    item = EvidenceItem(
        id="EV-TEST-001",
        status="collected",
        stage="packet_local",
        producer="pytest",
        artifact_paths=["test-output.txt"],
        summary="All tests passed",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    data = manifest.to_dict()

    assert data["packet_id"] == "PKT-001"
    assert data["generated_by"] == "verifier"
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["id"] == "EV-TEST-001"
    assert data["blockers"] == []


def test_evidence_manifest_from_dict():
    """Test EvidenceManifest deserialization."""
    data = {
        "packet_id": "PKT-001",
        "generated_by": "verifier",
        "evidence": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["test-output.txt"],
                "summary": "All tests passed",
            }
        ],
        "blockers": [],
    }

    manifest = EvidenceManifest.from_dict(data)

    assert manifest.packet_id == "PKT-001"
    assert manifest.generated_by == "verifier"
    assert len(manifest.evidence) == 1
    assert manifest.evidence[0].id == "EV-TEST-001"
    assert manifest.blockers == []


def test_parse_evidence_manifest_from_json():
    """Test parsing evidence manifest from JSON file."""
    data = {
        "packet_id": "PKT-001",
        "generated_by": "verifier",
        "evidence": [
            {
                "id": "EV-TEST-001",
                "status": "collected",
                "stage": "packet_local",
                "producer": "pytest",
                "artifact_paths": ["test-output.txt"],
                "summary": "All tests passed",
            }
        ],
        "blockers": [],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = Path(f.name)

    try:
        manifest = parse_evidence_manifest(temp_path)

        assert manifest.packet_id == "PKT-001"
        assert manifest.generated_by == "verifier"
        assert len(manifest.evidence) == 1
        assert manifest.evidence[0].id == "EV-TEST-001"
    finally:
        temp_path.unlink()


def test_validate_evidence_manifest_complete():
    """Test validation of complete manifest with all required evidence collected."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=["test-output.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-TEST-001",
        status="collected",
        stage="packet_local",
        producer="pytest",
        artifact_paths=["test-output.txt"],
        summary="All tests passed",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is True
    assert len(validation.errors) == 0


def test_validate_evidence_manifest_missing_required():
    """Test validation catches missing required evidence."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=["test-output.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[],  # Missing required evidence
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is False
    assert any(e["code"] == "evidence_not_generated" for e in validation.errors)
    assert any(e["evidence_id"] == "EV-TEST-001" for e in validation.errors)


def test_validate_evidence_manifest_deferred_wave_final():
    """Test validation allows wave_final evidence to be deferred."""
    req = EvidenceRequirement(
        id="EV-OBS-001",
        kind="observability",
        stage="wave_final",
        owner="verifier",
        producer="log_watch",
        profile=None,
        instruction="Check logs",
        required=True,
        coder_blocking=False,
        artifact_patterns=["logs.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-OBS-001",
        status="deferred",
        stage="wave_final",
        producer="log_watch",
        artifact_paths=[],
        summary="Deferred to wave-final verifier",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is True
    assert len(validation.errors) == 0


def test_validate_evidence_manifest_packet_local_deferred():
    """Test validation catches packet_local evidence deferred."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=["test-output.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-TEST-001",
        status="deferred",  # Invalid for packet_local
        stage="packet_local",
        producer="pytest",
        artifact_paths=[],
        summary="Deferred",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is False
    assert any(e["code"] == "packet_local_deferred" for e in validation.errors)


def test_validate_evidence_manifest_packet_local_missing_coder_blocking():
    """Test validation routes packet_local missing evidence to coder if coder_blocking."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=True,  # Coder blocking
        artifact_patterns=["test-output.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-TEST-001",
        status="missing",
        stage="packet_local",
        producer="pytest",
        artifact_paths=[],
        summary="Tests failed",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is False
    assert any(e["code"] == "implementation_failed" for e in validation.errors)
    assert any(e["route_to"] == "coder" for e in validation.errors)


def test_validate_evidence_manifest_packet_local_missing_not_coder_blocking():
    """Test validation routes packet_local missing evidence to verifier if not coder_blocking."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,  # Not coder blocking
        artifact_patterns=["test-output.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-TEST-001",
        status="missing",
        stage="packet_local",
        producer="pytest",
        artifact_paths=[],
        summary="Tests not run",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is False
    assert any(e["code"] == "evidence_not_generated" for e in validation.errors)
    assert any(e["route_to"] == "verifier" for e in validation.errors)


def test_validate_evidence_manifest_wave_final_missing_warning():
    """Test validation warns about wave_final missing evidence (not packet-blocking)."""
    req = EvidenceRequirement(
        id="EV-OBS-001",
        kind="observability",
        stage="wave_final",
        owner="verifier",
        producer="log_watch",
        profile=None,
        instruction="Check logs",
        required=True,
        coder_blocking=False,
        artifact_patterns=["logs.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-OBS-001",
        status="missing",
        stage="wave_final",
        producer="log_watch",
        artifact_paths=[],
        summary="Logs not available",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is True  # Warning, not error
    assert len(validation.warnings) > 0
    assert any(w["code"] == "wave_final_evidence_pending" for w in validation.warnings)


def test_validate_evidence_manifest_unknown_id():
    """Test validation warns about evidence id not in contract."""
    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[],  # No requirements
    )

    item = EvidenceItem(
        id="EV-UNKNOWN-001",
        status="collected",
        stage="packet_local",
        producer="pytest",
        artifact_paths=["test-output.txt"],
        summary="Unknown evidence",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is True  # Warning, not error
    assert len(validation.warnings) > 0
    assert any(w["code"] == "unknown_evidence_id" for w in validation.warnings)


def test_validate_evidence_manifest_invalid_status():
    """Test validation catches invalid evidence status."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=["test-output.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-TEST-001",
        status="invalid_status",  # Invalid status
        stage="packet_local",
        producer="pytest",
        artifact_paths=[],
        summary="Invalid",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is False
    assert any(e["code"] == "invalid_status" for e in validation.errors)


def test_validate_evidence_manifest_not_applicable():
    """Test validation allows not_applicable status."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=["test-output.txt"],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    item = EvidenceItem(
        id="EV-TEST-001",
        status="not_applicable",
        stage="packet_local",
        producer="pytest",
        artifact_paths=[],
        summary="No tests in this packet",
    )

    manifest = EvidenceManifest(
        packet_id="PKT-001",
        generated_by="verifier",
        evidence=[item],
        blockers=[],
    )

    validation = validate_evidence_manifest(manifest, contract)

    assert validation.ok is True
    assert len(validation.errors) == 0
