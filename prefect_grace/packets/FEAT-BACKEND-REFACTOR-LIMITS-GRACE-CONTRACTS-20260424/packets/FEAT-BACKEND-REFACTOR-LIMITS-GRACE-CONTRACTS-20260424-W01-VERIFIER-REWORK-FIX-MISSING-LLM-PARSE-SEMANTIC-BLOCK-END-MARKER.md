# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER

## Title
Verifier Rework Fix Missing LLM Parse Semantic Block End Marker

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-REVIEW-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: W01 targeted commands
- frontend: not required
- observability: packet_local

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
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is only allowed for coder packets

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFIER-REWORK-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Fix Missing LLM Parse Semantic Block End Marker",
  "summary": "Validate the architect-bounded direct rework for `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-REVIEW-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "W01 targeted commands",
    "frontend": "not required",
    "observability": "packet_local"
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
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is only allowed for coder packets"
  },
  "reviewer_gate": [
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
