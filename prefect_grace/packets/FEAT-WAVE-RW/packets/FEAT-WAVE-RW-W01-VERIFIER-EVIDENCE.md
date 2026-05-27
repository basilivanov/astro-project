# Packet: FEAT-WAVE-RW-W01-VERIFIER-EVIDENCE

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
- FEAT-WAVE-RW-W01-WAVE-PACKET
- Coder packet file `/opt/astro-project/prefect_grace/packets/FEAT-WAVE-RW/packets/FEAT-WAVE-RW-W01-WAVE-PACKET.md`.

## Acceptance Criteria
- Commands run are recorded.
- Evidence paths are recorded.
- Observability verdict is explicit.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-WAVE-RW-W01-WAVE-PACKET

## Notes
- Fail the packet if evidence is missing.
