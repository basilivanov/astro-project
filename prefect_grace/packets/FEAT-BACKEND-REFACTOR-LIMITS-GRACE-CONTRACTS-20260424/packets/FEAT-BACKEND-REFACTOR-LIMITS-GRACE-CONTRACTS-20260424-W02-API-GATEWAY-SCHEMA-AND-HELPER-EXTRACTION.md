# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION

## Title
API Gateway Schema And Helper Extraction

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION`

## Packet Type
execution

## Summary
Extract Pydantic DTOs and pure serialization/report helper functions from backend/app/main.py into API-local modules without moving route ownership yet.

## Wave
W02

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION`

## Write Scope
- backend/app/main.py
- backend/app/api*.py
- tests/test_api_contract_wave1.py
- tests/test_report_contract.py

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-ARCHITECT-GATE-W01
- current main.py module map
- existing API contract tests

## Acceptance Criteria
- Schemas serialize identically
- main.py compatibility imports remain stable
- No route behavior changes

## Verification Profile
- backend: targeted API/report contract pytest
- frontend: not required
- observability: packet_local structured log capture where tests already exercise it

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No endpoint movement in this packet
- No DTO field/default changes

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-ARCHITECT-GATE-W01

## Notes
- Preparatory split to reduce router extraction risk.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "API Gateway Schema And Helper Extraction",
  "summary": "Extract Pydantic DTOs and pure serialization/report helper functions from backend/app/main.py into API-local modules without moving route ownership yet.",
  "write_scope": [
    "backend/app/main.py",
    "backend/app/api*.py",
    "tests/test_api_contract_wave1.py",
    "tests/test_report_contract.py"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-ARCHITECT-GATE-W01",
    "current main.py module map",
    "existing API contract tests"
  ],
  "acceptance_criteria": [
    "Schemas serialize identically",
    "main.py compatibility imports remain stable",
    "No route behavior changes"
  ],
  "verification_profile": {
    "backend": "targeted API/report contract pytest",
    "frontend": "not required",
    "observability": "packet_local structured log capture where tests already exercise it"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No endpoint movement in this packet",
    "No DTO field/default changes"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-ARCHITECT-GATE-W01"
  ],
  "notes": [
    "Preparatory split to reduce router extraction risk."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-SCHEMA-AND-HELPER-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
