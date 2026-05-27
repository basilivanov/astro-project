# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-VERIFIER-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-VERIFIER-EVIDENCE`

## Summary
Validate the coder packet with the required test profile and observability gate.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- coder packet file

## Acceptance Criteria
- Commands run are recorded.
- Evidence paths are recorded.
- Observability verdict is explicit.
- Frontend visual verdict is explicit when UI is touched.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_profile: backend_quick
- observability_scope: packet_local
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - /opt/astro-project/frontend/docs/review_evidence/front/day-week/**/*
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Notes
- Fail the packet if evidence is missing.
