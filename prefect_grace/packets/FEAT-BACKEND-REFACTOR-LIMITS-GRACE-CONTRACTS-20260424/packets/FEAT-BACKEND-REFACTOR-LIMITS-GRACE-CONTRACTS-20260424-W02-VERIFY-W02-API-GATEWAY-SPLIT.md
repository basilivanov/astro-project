# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT

## Title
Verify W02 API Gateway Split

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`

## Packet Type
execution

## Summary
Verify W02 route behavior, main.py line limit, targeted API tests, and canonical evidence.

## Wave
W02

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION`

## Write Scope
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION

## Acceptance Criteria
- W02 commands pass
- main.py is <=1000 lines
- Today/Week/Admin/Catalog evidence verdict is clean

## Verification Profile
- backend: W02 targeted API commands
- frontend: not required
- observability: wave_final clean required

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- artifact_globs:
  - logs/*.jsonl
  - test-results/**/*.json
  - test-results/**/*.md
  - prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/**
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence includes route/size/test/log verdicts

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION

## Notes
- W02 touches canonical API emitters, so no-evidence closeout is blocking.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Verify W02 API Gateway Split",
  "summary": "Verify W02 route behavior, main.py line limit, targeted API tests, and canonical evidence.",
  "write_scope": [
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION"
  ],
  "acceptance_criteria": [
    "W02 commands pass",
    "main.py is <=1000 lines",
    "Today/Week/Admin/Catalog evidence verdict is clean"
  ],
  "verification_profile": {
    "backend": "W02 targeted API commands",
    "frontend": "not required",
    "observability": "wave_final clean required"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_profile": "read-only",
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
    ],
    "artifact_globs": [
      "logs/*.jsonl",
      "test-results/**/*.json",
      "test-results/**/*.md",
      "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/**"
    ],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence includes route/size/test/log verdicts"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION"
  ],
  "notes": [
    "W02 touches canonical API emitters, so no-evidence closeout is blocking."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
