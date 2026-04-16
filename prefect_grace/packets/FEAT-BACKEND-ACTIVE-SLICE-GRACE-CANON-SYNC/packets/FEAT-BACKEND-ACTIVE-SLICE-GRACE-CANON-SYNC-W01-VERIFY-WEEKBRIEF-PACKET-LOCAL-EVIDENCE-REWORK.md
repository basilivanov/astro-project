# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFY-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFY-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK`

## Summary
Validate the architect-issued direct rework `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK` for packet-local WeekBrief evidence and record exact backend/observability results.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only. Do not edit implementation files.

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS

## Acceptance Criteria
- Record exact targeted WeekBrief pytest result.
- Record backend:quick result.
- Run packet-local read-only post-test review and state observability verdict clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker.
- Do not claim canonical today-week/W02 evidence from this W01 verifier packet.

## Verification Profile
- backend: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py; docker exec astro-project-backend-1 python3 scripts/pipeline.py
- frontend: not applicable; frontend frozen and untouched
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; packet-local evidence only

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False
- artifact_globs:
  - /opt/astro-project/logs/**/*
  - /opt/astro-project/artifacts/**/*
  - /opt/astro-project/prefect_grace/state/runs/**/*

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original W01 attempt.
- WeekBrief packet-local evidence must be attributable by module/function/block/lane.
- Missing or failed backend/read-only evidence remains a blocker for the rework reviewer.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK

## Notes
- This verifier packet was created as canonical-line continuation after architect direct rework.
- W02 canonical today-week evidence remains owned by the existing W02 verifier packet.
