# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD

## Title
Strict Backend Size Guard

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD`

## Packet Type
execution

## Summary
Update scripts/check_size_limits.py to provide strict backend/app scoped file/function checks with generated/cache exclusions and transitional allow-known-oversized support for W01 only.

## Wave
W01

## Role
coder

## Reasoning
medium

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD`

## Write Scope
- scripts/check_size_limits.py
- tests/test_backend_size_contracts.py

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-ARCHITECT-FORMALIZATION
- feature brief
- canon digest advisory memory

## Acceptance Criteria
- Strict checker can fail on >1000-line backend files
- Checker excludes venv/cache/generated artifacts
- Checker reports AST function spans or exact token counts as available

## Verification Profile
- backend: targeted checker tests plus checker dry run
- frontend: not required
- observability: none

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No broad repository scan beyond configured exclusions
- No unrelated behavior checks embedded in size script

## Dependencies
-

## Notes
- Use allow-known-oversized only until W04 final scan.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "medium",
  "title": "Strict Backend Size Guard",
  "summary": "Update scripts/check_size_limits.py to provide strict backend/app scoped file/function checks with generated/cache exclusions and transitional allow-known-oversized support for W01 only.",
  "write_scope": [
    "scripts/check_size_limits.py",
    "tests/test_backend_size_contracts.py"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-ARCHITECT-FORMALIZATION",
    "feature brief",
    "canon digest advisory memory"
  ],
  "acceptance_criteria": [
    "Strict checker can fail on >1000-line backend files",
    "Checker excludes venv/cache/generated artifacts",
    "Checker reports AST function spans or exact token counts as available"
  ],
  "verification_profile": {
    "backend": "targeted checker tests plus checker dry run",
    "frontend": "not required",
    "observability": "none"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No broad repository scan beyond configured exclusions",
    "No unrelated behavior checks embedded in size script"
  ],
  "dependencies": [],
  "notes": [
    "Use allow-known-oversized only until W04 final scan."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
