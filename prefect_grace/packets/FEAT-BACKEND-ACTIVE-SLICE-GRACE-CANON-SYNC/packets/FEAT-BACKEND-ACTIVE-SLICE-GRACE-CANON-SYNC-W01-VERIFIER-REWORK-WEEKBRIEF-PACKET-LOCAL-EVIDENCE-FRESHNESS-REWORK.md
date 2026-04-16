# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK`

## Summary
Validate the architect-bounded direct rework for `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False
- artifact_globs:
  - logs/**
  - artifacts/**
  - prefect_grace/packets/FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC/**
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## Notes
- This verifier packet was created for architect-bounded direct rework.
