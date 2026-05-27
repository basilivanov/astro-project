# Packet: FEAT-DEMO-VERIFY2-W01-VERIFIER-EVIDENCE

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
- FEAT-DEMO-VERIFY2-W01-TEST-IMPLEMENTATION-PACKET
- Coder packet file `/opt/astro-project/prefect_grace/packets/FEAT-DEMO-VERIFY2/packets/FEAT-DEMO-VERIFY2-W01-TEST-IMPLEMENTATION-PACKET.md`.

## Acceptance Criteria
- Commands run are recorded.
- Evidence paths are recorded.
- Observability verdict is explicit.
- Frontend visual verdict is explicit when UI is touched.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-DEMO-VERIFY2-W01-TEST-IMPLEMENTATION-PACKET

## Notes
- Fail the packet if evidence is missing.
