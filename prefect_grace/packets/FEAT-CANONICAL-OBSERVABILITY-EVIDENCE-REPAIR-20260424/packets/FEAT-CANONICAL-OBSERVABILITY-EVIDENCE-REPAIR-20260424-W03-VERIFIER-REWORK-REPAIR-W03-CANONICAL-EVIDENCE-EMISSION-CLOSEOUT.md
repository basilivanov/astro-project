# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-VERIFIER-REWORK-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT

## Title
Verifier Rework Repair W03 Canonical Evidence Emission Closeout

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-VERIFIER-REWORK-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION` and capture fresh evidence.

## Wave
W03

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REVIEW-INTEGRATED-EVIDENCE-CLOSEOUT

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: python3 -m pytest tests/test_post_test_review.py tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py && docker exec astro-project-backend-1 python3 scripts/pipeline.py
- frontend: not required
- observability: wave_final canonical post-test review commands

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
- rework_mode: bounded_fresh

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-VERIFIER-REWORK-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W03",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Repair W03 Canonical Evidence Emission Closeout",
  "summary": "Validate the architect-bounded direct rework for `FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT",
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REVIEW-INTEGRATED-EVIDENCE-CLOSEOUT"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "python3 -m pytest tests/test_post_test_review.py tests/test_log_watch_feed_admin.py tests/test_forecast_catalog_watch.py && docker exec astro-project-backend-1 python3 scripts/pipeline.py",
    "frontend": "not required",
    "observability": "wave_final canonical post-test review commands"
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
    "include_day_live_canary": false,
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-REPAIR-W03-CANONICAL-EVIDENCE-EMISSION-CLOSEOUT"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
