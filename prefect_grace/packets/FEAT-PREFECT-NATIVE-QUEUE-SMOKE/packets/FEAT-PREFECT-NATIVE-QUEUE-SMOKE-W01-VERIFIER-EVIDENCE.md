# Packet: FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-VERIFIER-EVIDENCE

## Title
Verifier Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-PREFECT-NATIVE-QUEUE-SMOKE`
- wave_ref: `feature:FEAT-PREFECT-NATIVE-QUEUE-SMOKE:wave:W01`
- packet_ref: `feature:FEAT-PREFECT-NATIVE-QUEUE-SMOKE:wave:W01:packet:FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-VERIFIER-EVIDENCE`

## Packet Type
execution

## Summary
Validate the coder packet with the required test profile and observability gate.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET
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
- runner: codex
- backend_profile: backend_quick
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- No green-only pass without evidence review.
- Blocking issues are explicit when evidence is missing.

## Dependencies
- FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET

## Notes
- Fail the packet if evidence is missing.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-VERIFIER-EVIDENCE",
  "feature_id": "FEAT-PREFECT-NATIVE-QUEUE-SMOKE",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Evidence",
  "summary": "Validate the coder packet with the required test profile and observability gate.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET",
    "coder packet file"
  ],
  "acceptance_criteria": [
    "Commands run are recorded.",
    "Evidence paths are recorded.",
    "Observability verdict is explicit.",
    "Frontend visual verdict is explicit when UI is touched."
  ],
  "verification_profile": {
    "backend": "execute minimally sufficient backend profile",
    "frontend": "execute minimally sufficient frontend profile if UI is touched",
    "observability": "mandatory log, replay, digest, and trace review"
  },
  "execution_hints": {
    "runner": "codex",
    "backend_profile": "backend_quick",
    "frontend_profile": null,
    "frontend_commands": [],
    "observability_profile": null,
    "observability_commands": [],
    "observability_scope": "packet_local",
    "canonical_flow_commands": [],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "artifact_globs": [],
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "No green-only pass without evidence review.",
    "Blocking issues are explicit when evidence is missing."
  ],
  "dependencies": [
    "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET"
  ],
  "notes": [
    "Fail the packet if evidence is missing."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
