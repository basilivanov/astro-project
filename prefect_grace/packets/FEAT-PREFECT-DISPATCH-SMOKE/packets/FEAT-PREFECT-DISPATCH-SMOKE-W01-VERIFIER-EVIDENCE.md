# Packet: FEAT-PREFECT-DISPATCH-SMOKE-W01-VERIFIER-EVIDENCE

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
- FEAT-PREFECT-DISPATCH-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET
- Coder packet file `/opt/astro-project/prefect_grace/packets/FEAT-PREFECT-DISPATCH-SMOKE/packets/FEAT-PREFECT-DISPATCH-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET.md`.

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
- backend_profile: backend_quick
- observability_profile: read-only
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-PREFECT-DISPATCH-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET

## Notes
- Fail the packet if evidence is missing.
