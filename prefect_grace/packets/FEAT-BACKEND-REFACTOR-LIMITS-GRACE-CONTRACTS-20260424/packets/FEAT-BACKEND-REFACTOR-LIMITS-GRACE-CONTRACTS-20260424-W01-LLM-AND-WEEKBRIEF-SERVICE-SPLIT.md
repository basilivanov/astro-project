# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-LLM-AND-WEEKBRIEF-SERVICE-SPLIT

## Title
LLM And WeekBrief Service Split

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-LLM-AND-WEEKBRIEF-SERVICE-SPLIT`

## Packet Type
execution

## Summary
Split backend/app/llm/orchestrator.py and backend/app/services/week_brief_service.py into cohesive modules with stable facade imports and GRACE contracts.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-LLM-AND-WEEKBRIEF-SERVICE-SPLIT`

## Write Scope
- backend/app/llm/*.py
- backend/app/services/week_brief*.py
- tests/test_*llm*.py
- tests/test_*week_brief*.py

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD
- existing LLM and WeekBrief tests

## Acceptance Criteria
- Both original oversized files are <=1000 lines
- Existing public symbols remain importable
- WeekBrief logs keep packet_local evidence fields
- New modules include GRACE module contracts/maps and paired semantic blocks

## Verification Profile
- backend: targeted LLM and WeekBrief pytest
- frontend: not required
- observability: packet_local WeekBrief telemetry review; degraded-but-expected acceptable only if no canonical emitter ran

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No schema or fallback behavior change
- GRACE module contracts/maps present in new modules

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD

## Notes
- Keep backend.app.llm.orchestrator and backend.app.services.week_brief_service as compatibility facades.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-LLM-AND-WEEKBRIEF-SERVICE-SPLIT",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "LLM And WeekBrief Service Split",
  "summary": "Split backend/app/llm/orchestrator.py and backend/app/services/week_brief_service.py into cohesive modules with stable facade imports and GRACE contracts.",
  "write_scope": [
    "backend/app/llm/*.py",
    "backend/app/services/week_brief*.py",
    "tests/test_*llm*.py",
    "tests/test_*week_brief*.py"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD",
    "existing LLM and WeekBrief tests"
  ],
  "acceptance_criteria": [
    "Both original oversized files are <=1000 lines",
    "Existing public symbols remain importable",
    "WeekBrief logs keep packet_local evidence fields",
    "New modules include GRACE module contracts/maps and paired semantic blocks"
  ],
  "verification_profile": {
    "backend": "targeted LLM and WeekBrief pytest",
    "frontend": "not required",
    "observability": "packet_local WeekBrief telemetry review; degraded-but-expected acceptable only if no canonical emitter ran"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No schema or fallback behavior change",
    "GRACE module contracts/maps present in new modules"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-STRICT-BACKEND-SIZE-GUARD"
  ],
  "notes": [
    "Keep backend.app.llm.orchestrator and backend.app.services.week_brief_service as compatibility facades."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-LLM-AND-WEEKBRIEF-SERVICE-SPLIT",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
