"""Tests for prefect_grace.platform.evidence_contract module."""

import pytest
from prefect_grace.platform.evidence_contract import (
    EvidenceRequirement,
    EvidenceContract,
    EvidenceContractValidation,
    parse_evidence_contract,
    validate_evidence_contract,
    ALLOWED_KINDS,
    ALLOWED_STAGES,
    ALLOWED_OWNERS,
    ALLOWED_PRODUCERS,
)


class MockPacket:
    """Mock ParsedPacket for testing."""
    def __init__(self, packet_id: str):
        self.packet_id = packet_id


def test_evidence_requirement_to_dict():
    """Test EvidenceRequirement serialization."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile="backend_quick",
        instruction="Run backend unit tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=["test-output.txt"],
    )

    data = req.to_dict()

    assert data["id"] == "EV-TEST-001"
    assert data["kind"] == "test"
    assert data["stage"] == "packet_local"
    assert data["owner"] == "verifier"
    assert data["producer"] == "pytest"
    assert data["profile"] == "backend_quick"
    assert data["instruction"] == "Run backend unit tests"
    assert data["required"] is True
    assert data["coder_blocking"] is False
    assert data["artifact_patterns"] == ["test-output.txt"]


def test_evidence_contract_to_dict():
    """Test EvidenceContract serialization."""
    req1 = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req1],
    )

    data = contract.to_dict()

    assert data["packet_id"] == "PKT-001"
    assert len(data["requirements"]) == 1
    assert data["requirements"][0]["id"] == "EV-TEST-001"


def test_parse_evidence_contract_empty():
    """Test parsing empty evidence contract."""
    packet = MockPacket("PKT-001")

    contract = parse_evidence_contract(packet)

    assert contract.packet_id == "PKT-001"
    assert len(contract.requirements) == 0


def test_validate_evidence_contract_valid():
    """Test validation of valid evidence contract."""
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

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is True
    assert len(validation.errors) == 0


def test_validate_evidence_contract_missing_id():
    """Test validation catches missing id."""
    req = EvidenceRequirement(
        id="",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert len(validation.errors) == 1
    assert validation.errors[0]["code"] == "missing_id"
    assert validation.errors[0]["route_to"] == "architect"


def test_validate_evidence_contract_duplicate_id():
    """Test validation catches duplicate ids."""
    req1 = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    req2 = EvidenceRequirement(
        id="EV-TEST-001",
        kind="visual",
        stage="packet_local",
        owner="verifier",
        producer="playwright",
        profile=None,
        instruction="Take screenshot",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req1, req2],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "duplicate_id" for e in validation.errors)


def test_validate_evidence_contract_unknown_kind():
    """Test validation catches unknown kind."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="invalid_kind",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "unknown_kind" for e in validation.errors)


def test_validate_evidence_contract_unknown_stage():
    """Test validation catches unknown stage."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="invalid_stage",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "unknown_stage" for e in validation.errors)


def test_validate_evidence_contract_unknown_owner():
    """Test validation catches unknown owner."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="invalid_owner",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "unknown_owner" for e in validation.errors)


def test_validate_evidence_contract_unknown_producer():
    """Test validation catches unknown producer."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="invalid_producer",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "unknown_producer" for e in validation.errors)


def test_validate_evidence_contract_wave_final_coder_blocking():
    """Test validation catches wave_final evidence marked coder_blocking."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="wave_final",
        owner="verifier",
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=True,  # Invalid for wave_final
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "wave_final_coder_blocking" for e in validation.errors)
    assert any(e["route_to"] == "architect" for e in validation.errors)


def test_validate_evidence_contract_missing_profile():
    """Test validation catches missing profile reference."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="pytest",
        profile="nonexistent_profile",
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {"backend_quick": {}}  # Profile exists but not the one we reference
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "missing_verification_profile" for e in validation.errors)


def test_validate_evidence_contract_required_without_owner():
    """Test validation catches required evidence without owner."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="",  # Missing owner
        producer="pytest",
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "required_without_owner" for e in validation.errors)


def test_validate_evidence_contract_required_without_producer():
    """Test validation catches required evidence without producer."""
    req = EvidenceRequirement(
        id="EV-TEST-001",
        kind="test",
        stage="packet_local",
        owner="verifier",
        producer="",  # Missing producer
        profile=None,
        instruction="Run tests",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is False
    assert any(e["code"] == "required_without_producer" for e in validation.errors)


def test_validate_evidence_contract_missing_artifact_pattern_warning():
    """Test validation warns about missing artifact pattern for required non-human evidence."""
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
        artifact_patterns=[],  # Missing artifact patterns
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is True  # Warning, not error
    assert len(validation.warnings) > 0
    assert any(w["code"] == "missing_artifact_pattern" for w in validation.warnings)


def test_validate_evidence_contract_human_signoff_no_artifact_pattern():
    """Test validation allows human_signoff without artifact pattern."""
    req = EvidenceRequirement(
        id="EV-HUMAN-001",
        kind="human_signoff",
        stage="packet_local",
        owner="reviewer",
        producer="manual",
        profile=None,
        instruction="Manual review",
        required=True,
        coder_blocking=False,
        artifact_patterns=[],  # OK for human_signoff
    )

    contract = EvidenceContract(
        packet_id="PKT-001",
        requirements=[req],
    )

    profiles = {}
    validation = validate_evidence_contract(contract, profiles)

    assert validation.ok is True
    # Should not warn about missing artifact pattern for human_signoff
    assert not any(w["code"] == "missing_artifact_pattern" for w in validation.warnings)


def test_evidence_contract_validation_to_dict():
    """Test EvidenceContractValidation serialization."""
    validation = EvidenceContractValidation(
        ok=False,
        errors=[
            {
                "code": "missing_id",
                "evidence_id": None,
                "route_to": "architect",
                "message": "Missing id",
            }
        ],
        warnings=[
            {
                "code": "missing_artifact_pattern",
                "evidence_id": "EV-001",
                "message": "Missing pattern",
            }
        ],
    )

    data = validation.to_dict()

    assert data["ok"] is False
    assert len(data["errors"]) == 1
    assert len(data["warnings"]) == 1
    assert data["errors"][0]["code"] == "missing_id"
    assert data["warnings"][0]["code"] == "missing_artifact_pattern"
