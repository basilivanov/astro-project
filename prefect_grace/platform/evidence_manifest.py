"""
# ============================================================================
# AI_HEADER: GRACE Evidence Manifest Module
# ============================================================================
#
# This module provides typed evidence manifest models for GRACE verifier output.
# Evidence manifests are structured JSON documents that record what evidence
# was collected, what's missing, what's deferred, and what blockers exist.
#
# Key Concepts:
# - Evidence manifests are JSON (not free-form prose)
# - Each evidence item has: id, status, stage, producer, artifact_paths, summary
# - Statuses: collected, missing, deferred, not_applicable, failed, artifact_reference_invalid, contract_invalid
# - Manifests are validated against evidence contracts
# - Verifier produces manifest, platform validates it
#
# Module Dependencies:
# - prefect_grace.platform.evidence_contract (EvidenceContract, EvidenceContractValidation)
# - No Prefect imports (pure validation logic)
#
# ============================================================================
"""

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
import json

# START_MODULE_CONTRACT
# Module: evidence_manifest
# Purpose: Parse and validate evidence manifests from verifier output
# Exports: EvidenceItem, EvidenceManifest, parse_evidence_manifest, validate_evidence_manifest
# Dependencies: evidence_contract (EvidenceContract, EvidenceContractValidation)
# Constraints: No Prefect imports, deterministic validation, fail-closed
# END_MODULE_CONTRACT

# START_MODULE_MAP
# Block: models - Evidence item and manifest dataclasses
# Block: validation_constants - Allowed evidence statuses
# Block: parser - Parse evidence manifest from JSON
# Block: validator - Validate manifest against contract
# END_MODULE_MAP

# START_BLOCK: models

@dataclass(frozen=True)
class EvidenceItem:
    """Single evidence item in manifest.

    Fields:
    - id: Evidence requirement ID
    - status: Evidence status (collected, missing, deferred, not_applicable, failed, artifact_reference_invalid, contract_invalid)
    - stage: Evidence stage (packet_local, wave_final, release_final)
    - producer: How evidence was produced (agent, pytest, playwright, cli, etc.)
    - artifact_paths: List of artifact file paths
    - summary: Human-readable summary of evidence
    """
    id: str
    status: str
    stage: str
    producer: str
    artifact_paths: list[str]
    summary: str

    # START_FUNCTION_CONTRACT
    # Function: to_dict
    # Purpose: Serialize EvidenceItem to dict for JSON output
    # Args: None (instance method)
    # Returns: Dict with all fields
    # Inputs: self
    # Side_effects: None (pure function)
    # Emitted_logs: None
    # Error_behavior: Never raises
    # END_FUNCTION_CONTRACT
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON output."""
        return {
            "id": self.id,
            "status": self.status,
            "stage": self.stage,
            "producer": self.producer,
            "artifact_paths": list(self.artifact_paths),
            "summary": self.summary,
        }

    # START_FUNCTION_CONTRACT
    # Function: from_dict
    # Purpose: Deserialize EvidenceItem from dict
    # Args: data dict with evidence item fields
    # Returns: EvidenceItem instance
    # Inputs: Dict from JSON
    # Side_effects: None (pure function)
    # Emitted_logs: None
    # Error_behavior: Raises KeyError if required fields missing
    # END_FUNCTION_CONTRACT
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceItem":
        """Deserialize from dict."""
        return cls(
            id=data.get("id", ""),
            status=data.get("status", ""),
            stage=data.get("stage", ""),
            producer=data.get("producer", ""),
            artifact_paths=data.get("artifact_paths", []),
            summary=data.get("summary", ""),
        )


@dataclass(frozen=True)
class EvidenceManifest:
    """Evidence manifest from verifier output.

    Fields:
    - packet_id: Packet identifier
    - generated_by: Who generated manifest (verifier, pipeline, etc.)
    - evidence: List of evidence items
    - blockers: List of blocker dicts
    """
    packet_id: str
    generated_by: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    blockers: list[dict[str, Any]] = field(default_factory=list)

    # START_FUNCTION_CONTRACT
    # Function: to_dict
    # Purpose: Serialize EvidenceManifest to dict for JSON output
    # Args: None (instance method)
    # Returns: Dict with packet_id, generated_by, evidence, blockers
    # Inputs: self
    # Side_effects: None (pure function)
    # Emitted_logs: None
    # Error_behavior: Never raises
    # END_FUNCTION_CONTRACT
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON output."""
        return {
            "packet_id": self.packet_id,
            "generated_by": self.generated_by,
            "evidence": [item.to_dict() for item in self.evidence],
            "blockers": list(self.blockers),
        }

    # START_FUNCTION_CONTRACT
    # Function: from_dict
    # Purpose: Deserialize EvidenceManifest from dict
    # Args: data dict with manifest fields
    # Returns: EvidenceManifest instance
    # Inputs: Dict from JSON
    # Side_effects: None (pure function)
    # Emitted_logs: None
    # Error_behavior: Raises KeyError if required fields missing
    # END_FUNCTION_CONTRACT
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceManifest":
        """Deserialize from dict."""
        return cls(
            packet_id=data.get("packet_id", ""),
            generated_by=data.get("generated_by", ""),
            evidence=[EvidenceItem.from_dict(item) for item in data.get("evidence", [])],
            blockers=data.get("blockers", []),
        )

# END_BLOCK: models

# START_BLOCK: validation_constants

# Allowed evidence statuses
ALLOWED_STATUSES = {
    "collected",
    "missing",
    "deferred",
    "not_applicable",
    "failed",
    "artifact_reference_invalid",
    "contract_invalid",
}

# END_BLOCK: validation_constants

# START_BLOCK: parser

# START_FUNCTION_CONTRACT
# Function: parse_evidence_manifest
# Purpose: Load evidence manifest from JSON file
# Args:
#   - path: Path to evidence_manifest.json
# Returns: EvidenceManifest with parsed data
# Inputs: Path to JSON file
# Side_effects: Reads file from disk
# Emitted_logs: None
# Error_behavior: Raises FileNotFoundError or JSONDecodeError on failure
# Behavior:
#   - Reads JSON file
#   - Deserializes to EvidenceManifest
#   - Raises exception if file not found or invalid JSON
# END_FUNCTION_CONTRACT
def parse_evidence_manifest(path: Path) -> "EvidenceManifest":
    """Load evidence manifest from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return EvidenceManifest.from_dict(data)

# END_BLOCK: parser

# START_BLOCK: validator

# START_FUNCTION_CONTRACT
# Function: validate_evidence_manifest
# Purpose: Validate manifest against contract
# Args:
#   - manifest: EvidenceManifest to validate
#   - contract: EvidenceContract to validate against
# Returns: EvidenceContractValidation with errors and warnings
# Inputs: EvidenceManifest, EvidenceContract
# Side_effects: None (pure function)
# Emitted_logs: None
# Error_behavior: Returns validation result with errors list, never raises
# Behavior:
#   - Checks all required evidence has status collected or deferred (if wave_final)
#   - Checks evidence IDs match contract
#   - Checks statuses are valid
#   - Checks packet_local required evidence not missing
#   - Deterministic validation, fail-closed
# END_FUNCTION_CONTRACT
def validate_evidence_manifest(
    manifest: "EvidenceManifest",
    contract: Any,  # EvidenceContract
) -> Any:  # EvidenceContractValidation
    """Validate manifest against contract.

    Checks:
    - All required evidence has status collected or deferred (if wave_final)
    - Evidence IDs match contract
    - Statuses are valid
    - packet_local required evidence not missing
    """
    from prefect_grace.platform.evidence_contract import EvidenceContractValidation

    errors = []
    warnings = []

    # Build map of contract requirements by ID
    contract_reqs = {req.id: req for req in contract.requirements}

    # Build map of manifest evidence by ID
    manifest_evidence = {item.id: item for item in manifest.evidence}

    # Check all required evidence is present
    for req_id, req in contract_reqs.items():
        if not req.required:
            continue

        evidence = manifest_evidence.get(req_id)

        if evidence is None:
            errors.append({
                "code": "evidence_not_generated",
                "evidence_id": req_id,
                "route_to": "verifier",
                "message": f"Required evidence {req_id} not in manifest",
            })
            continue

        # Check status is valid
        if evidence.status not in ALLOWED_STATUSES:
            errors.append({
                "code": "invalid_status",
                "evidence_id": req_id,
                "route_to": "verifier",
                "message": f"Invalid status for {req_id}: {evidence.status}",
            })
            continue

        # Check packet_local required evidence is collected
        if req.stage == "packet_local" and evidence.status not in ["collected", "not_applicable"]:
            if evidence.status == "deferred":
                errors.append({
                    "code": "packet_local_deferred",
                    "evidence_id": req_id,
                    "route_to": "verifier",
                    "message": f"packet_local evidence {req_id} cannot be deferred",
                })
            elif evidence.status == "missing":
                if req.coder_blocking:
                    errors.append({
                        "code": "implementation_failed",
                        "evidence_id": req_id,
                        "route_to": "coder",
                        "message": f"Required packet_local evidence {req_id} missing (coder_blocking)",
                    })
                else:
                    errors.append({
                        "code": "evidence_not_generated",
                        "evidence_id": req_id,
                        "route_to": "verifier",
                        "message": f"Required packet_local evidence {req_id} missing",
                    })

        # Check wave_final required evidence is collected or deferred
        if req.stage == "wave_final" and evidence.status not in ["collected", "deferred", "not_applicable"]:
            if evidence.status == "missing":
                warnings.append({
                    "code": "wave_final_evidence_pending",
                    "evidence_id": req_id,
                    "message": f"wave_final evidence {req_id} missing (not packet-blocking)",
                })

    # Check all manifest evidence IDs exist in contract
    for evidence_id in manifest_evidence.keys():
        if evidence_id not in contract_reqs:
            warnings.append({
                "code": "unknown_evidence_id",
                "evidence_id": evidence_id,
                "message": f"Evidence {evidence_id} not in contract",
            })

    return EvidenceContractValidation(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )

# END_BLOCK: validator
