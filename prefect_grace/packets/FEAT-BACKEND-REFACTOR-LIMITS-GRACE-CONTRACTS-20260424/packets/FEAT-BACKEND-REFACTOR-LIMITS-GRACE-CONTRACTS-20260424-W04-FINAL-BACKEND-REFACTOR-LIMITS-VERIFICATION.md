# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W04-FINAL-BACKEND-REFACTOR-LIMITS-VERIFICATION

## Title
Final Backend Refactor Limits Verification

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W04`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W04:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W04-FINAL-BACKEND-REFACTOR-LIMITS-VERIFICATION`

## Packet Type
execution

## Summary
Run strict size/function checks, targeted behavior suites, backend quick pipeline, and final post-test observability review.

## Wave
W04

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-ARCHITECT-GATE-W03`

## Write Scope
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**
- docs/backend-refactor-limits-grace-contracts/**

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-ARCHITECT-GATE-W03

## Acceptance Criteria
- All final verification commands pass
- Observability verdict is clean
- Evidence includes size scan, function-size scan, test commands, and trace/log review

## Verification Profile
- backend: strict size scan, targeted pytest, docker backend quick pipeline
- frontend: not required
- observability: wave_final post_test_review with clean verdict

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
- Evidence paths and verdicts are concrete
- No degraded/no-evidence closeout accepted for W04

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-ARCHITECT-GATE-W03

## Notes
- Do not run frontend E2E; frontend is out of scope.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W04-FINAL-BACKEND-REFACTOR-LIMITS-VERIFICATION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W04",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Final Backend Refactor Limits Verification",
  "summary": "Run strict size/function checks, targeted behavior suites, backend quick pipeline, and final post-test observability review.",
  "write_scope": [
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**",
    "docs/backend-refactor-limits-grace-contracts/**"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-ARCHITECT-GATE-W03"
  ],
  "acceptance_criteria": [
    "All final verification commands pass",
    "Observability verdict is clean",
    "Evidence includes size scan, function-size scan, test commands, and trace/log review"
  ],
  "verification_profile": {
    "backend": "strict size scan, targeted pytest, docker backend quick pipeline",
    "frontend": "not required",
    "observability": "wave_final post_test_review with clean verdict"
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
    "Evidence paths and verdicts are concrete",
    "No degraded/no-evidence closeout accepted for W04"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-ARCHITECT-GATE-W03"
  ],
  "notes": [
    "Do not run frontend E2E; frontend is out of scope."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-ARCHITECT-GATE-W03",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
