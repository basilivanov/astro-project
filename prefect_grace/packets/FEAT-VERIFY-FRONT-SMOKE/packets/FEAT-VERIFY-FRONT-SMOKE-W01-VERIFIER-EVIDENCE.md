# Packet: FEAT-VERIFY-FRONT-SMOKE-W01-VERIFIER-EVIDENCE

## Summary
Validate the coder packet with the required test profile and observability gate.

## Wave
W01

## Role
verifier

## Reasoning
high

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-VERIFY-FRONT-SMOKE-W01-VERIFIER-FRONTEND-SMOKE-IMPLEMENTATION
- Coder packet file `/opt/astro-project/prefect_grace/packets/FEAT-VERIFY-FRONT-SMOKE/packets/FEAT-VERIFY-FRONT-SMOKE-W01-VERIFIER-FRONTEND-SMOKE-IMPLEMENTATION.md`.

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
- runner: verifier
- frontend_profile: frontend_quick
- observability_profile: today-week
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - frontend/test-results/**/*
  - frontend/artifacts/**/*
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-VERIFY-FRONT-SMOKE-W01-VERIFIER-FRONTEND-SMOKE-IMPLEMENTATION

## Notes
- Fail the packet if evidence is missing.
