# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## Title
Verifier Rework Refresh W02 Canonical Observability Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT` and capture fresh evidence.

## Wave
W02

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEW-W02-API-GATEWAY-SPLIT

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

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
- rework_mode: bounded_fresh

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Refresh W02 Canonical Observability Evidence",
  "summary": "Validate the architect-bounded direct rework for `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEW-W02-API-GATEWAY-SPLIT"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
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
    "include_day_live_canary": false,
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
