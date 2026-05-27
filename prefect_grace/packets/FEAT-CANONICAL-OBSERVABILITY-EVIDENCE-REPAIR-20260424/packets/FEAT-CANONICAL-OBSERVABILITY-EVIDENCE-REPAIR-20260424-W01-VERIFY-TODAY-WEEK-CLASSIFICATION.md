# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-VERIFY-TODAY-WEEK-CLASSIFICATION

## Title
Verify Today/Week Classification

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W01`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W01:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-VERIFY-TODAY-WEEK-CLASSIFICATION`

## Packet Type
execution

## Summary
Run targeted tests and packet-local post-test review output for W01 classification repair.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION`

## Write Scope
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**

## Inputs
- coder_w01_post_test_review output

## Acceptance Criteria
- Targeted pytest passes.
- Post-test review output contains explicit flow verdicts and identifiers where available.
- Verifier records clean, unexpected-degradation, degraded-but-expected, or no-evidence-blocker with rationale.

## Verification Profile
- backend: python3 -m pytest tests/test_post_test_review.py
- frontend: not required
- observability: packet_local post-test review evidence

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
  - prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence includes command output summary and verdict.
- No missing identifier analysis for degraded evidence.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION

## Notes
- Do not run frontend regression.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-VERIFY-TODAY-WEEK-CLASSIFICATION",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify Today/Week Classification",
  "summary": "Run targeted tests and packet-local post-test review output for W01 classification repair.",
  "write_scope": [
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**"
  ],
  "inputs": [
    "coder_w01_post_test_review output"
  ],
  "acceptance_criteria": [
    "Targeted pytest passes.",
    "Post-test review output contains explicit flow verdicts and identifiers where available.",
    "Verifier records clean, unexpected-degradation, degraded-but-expected, or no-evidence-blocker with rationale."
  ],
  "verification_profile": {
    "backend": "python3 -m pytest tests/test_post_test_review.py",
    "frontend": "not required",
    "observability": "packet_local post-test review evidence"
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
      "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/evidence/**"
    ],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence includes command output summary and verdict.",
    "No missing identifier analysis for degraded evidence."
  ],
  "dependencies": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION"
  ],
  "notes": [
    "Do not run frontend regression."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-REPAIR-TODAY-WEEK-POST-TEST-CLASSIFICATION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
