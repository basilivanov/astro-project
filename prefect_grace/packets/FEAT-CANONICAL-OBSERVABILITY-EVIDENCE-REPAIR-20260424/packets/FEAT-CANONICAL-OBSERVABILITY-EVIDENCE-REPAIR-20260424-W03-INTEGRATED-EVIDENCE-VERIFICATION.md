# Packet: FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION

## Title
Integrated Evidence Verification

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- wave_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03`
- packet_ref: `feature:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424:wave:W03:packet:FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`

## Packet Type
execution

## Summary
Run integrated targeted tests, backend quick pipeline, and canonical post-test evidence commands for final closeout.

## Wave
W03

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION`

## Write Scope
- prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**

## Inputs
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-ARCHITECT-GATE-W01
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-ARCHITECT-GATE-W02

## Acceptance Criteria
- Targeted tests pass.
- Backend quick pipeline passes or unrelated failure is clearly isolated.
- Post-test evidence verdict is explicit and not misleading.
- Any degradation is classified as unexpected unless architect-approved expected reason codes are present.

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

## Reviewer Gate
- Evidence includes final verdict and relevant identifiers.
- No no-evidence-blocker when concrete degraded evidence exists.

## Dependencies
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-ARCHITECT-GATE-W01
- FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-ARCHITECT-GATE-W02

## Notes
- This wave owns canonical runtime evidence closeout.
- Do not add frontend visual requirements.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
  "feature_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Integrated Evidence Verification",
  "summary": "Run integrated targeted tests, backend quick pipeline, and canonical post-test evidence commands for final closeout.",
  "write_scope": [
    "prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**"
  ],
  "inputs": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-ARCHITECT-GATE-W01",
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-ARCHITECT-GATE-W02"
  ],
  "acceptance_criteria": [
    "Targeted tests pass.",
    "Backend quick pipeline passes or unrelated failure is clearly isolated.",
    "Post-test evidence verdict is explicit and not misleading.",
    "Any degradation is classified as unexpected unless architect-approved expected reason codes are present."
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
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence includes final verdict and relevant identifiers.",
    "No no-evidence-blocker when concrete degraded evidence exists."
  ],
  "dependencies": [
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W01-ARCHITECT-GATE-W01",
    "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W02-ARCHITECT-GATE-W02"
  ],
  "notes": [
    "This wave owns canonical runtime evidence closeout.",
    "Do not add frontend visual requirements."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424-W03-INTEGRATED-EVIDENCE-VERIFICATION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
