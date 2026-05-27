# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-VERIFIER-EVIDENCE

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
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-LIVE-IMPLEMENTATION-PACKET
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
- runner: codex
- backend_profile: backend_quick
- touches_frontend: True
- requires_frontend_visual: True
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-LIVE-IMPLEMENTATION-PACKET

## Notes
- Fail the packet if evidence is missing.
