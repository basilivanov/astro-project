# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEWER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## Title
Reviewer Rework Refresh W02 Canonical Observability Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEWER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE`

## Packet Type
gate_decision

## Summary
Review whether the architect-bounded direct rework for `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT` addressed the reviewer blockers.

## Wave
W02

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## Acceptance Criteria
- Exactly one verdict is returned.
- The original blockers are either resolved or explicitly remain.
- No unrelated scope expansion is accepted.

## Verification Profile
- backend: consume verifier evidence
- frontend: consume verifier evidence
- observability: consume verifier evidence

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
- Assess only the original blocker scope.
- Escalate only if blockers imply decomposition or business changes.

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## Notes
- This reviewer packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REVIEWER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Refresh W02 Canonical Observability Evidence",
  "summary": "Review whether the architect-bounded direct rework for `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT` addressed the reviewer blockers.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "The original blockers are either resolved or explicitly remain.",
    "No unrelated scope expansion is accepted."
  ],
  "verification_profile": {
    "backend": "consume verifier evidence",
    "frontend": "consume verifier evidence",
    "observability": "consume verifier evidence"
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
    "Assess only the original blocker scope.",
    "Escalate only if blockers imply decomposition or business changes."
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFIER-REWORK-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE"
  ],
  "notes": [
    "This reviewer packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
