# Packet: FEAT-OBS-REWORK-STOP-W01-VERIFIER-REWORK-REWORK-MAIN-SLICE

## Title
Verifier Rework Rework Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-OBS-REWORK-STOP`
- wave_ref: `feature:FEAT-OBS-REWORK-STOP:wave:W01`
- packet_ref: `feature:FEAT-OBS-REWORK-STOP:wave:W01:packet:FEAT-OBS-REWORK-STOP-W01-VERIFIER-REWORK-REWORK-MAIN-SLICE`

## Packet Type
rework

## Summary
Validate the localized rework for `FEAT-OBS-REWORK-STOP-W01-MAIN-SLICE` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-OBS-REWORK-STOP-W01-MAIN-SLICE`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-OBS-REWORK-STOP-W01-REWORK-MAIN-SLICE
- FEAT-OBS-REWORK-STOP-W01-REVIEW-SLICE

## Acceptance Criteria
- Commands run are recorded for the rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the rework.

## Verification Profile
- backend: rerun minimally sufficient backend checks for the reworked scope
- frontend: rerun targeted frontend checks if UI changed
- observability: repeat post-test digest, trace, and replay review

## Execution Hints
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-OBS-REWORK-STOP-W01-REWORK-MAIN-SLICE

## Notes
- This verifier packet was auto-created from reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-OBS-REWORK-STOP-W01-VERIFIER-REWORK-REWORK-MAIN-SLICE",
  "feature_id": "FEAT-OBS-REWORK-STOP",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Rework Main Slice",
  "summary": "Validate the localized rework for `FEAT-OBS-REWORK-STOP-W01-MAIN-SLICE` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-OBS-REWORK-STOP-W01-REWORK-MAIN-SLICE",
    "FEAT-OBS-REWORK-STOP-W01-REVIEW-SLICE"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the rework."
  ],
  "verification_profile": {
    "backend": "rerun minimally sufficient backend checks for the reworked scope",
    "frontend": "rerun targeted frontend checks if UI changed",
    "observability": "repeat post-test digest, trace, and replay review"
  },
  "execution_hints": {
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_profile": "read-only",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence must correspond to the rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-OBS-REWORK-STOP-W01-REWORK-MAIN-SLICE"
  ],
  "notes": [
    "This verifier packet was auto-created from reviewer blockers."
  ],
  "parent_packet_id": "FEAT-OBS-REWORK-STOP-W01-MAIN-SLICE",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
