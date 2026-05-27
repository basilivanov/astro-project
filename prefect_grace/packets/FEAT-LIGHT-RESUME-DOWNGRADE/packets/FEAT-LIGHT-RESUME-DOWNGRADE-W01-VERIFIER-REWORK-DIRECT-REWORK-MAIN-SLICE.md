# Packet: FEAT-LIGHT-RESUME-DOWNGRADE-W01-VERIFIER-REWORK-DIRECT-REWORK-MAIN-SLICE

## Title
Verifier Rework Direct Rework Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE`
- wave_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE:wave:W01`
- packet_ref: `feature:FEAT-LIGHT-RESUME-DOWNGRADE:wave:W01:packet:FEAT-LIGHT-RESUME-DOWNGRADE-W01-VERIFIER-REWORK-DIRECT-REWORK-MAIN-SLICE`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-LIGHT-RESUME-DOWNGRADE-W01-DIRECT-REWORK-MAIN-SLICE
- FEAT-LIGHT-RESUME-DOWNGRADE-W01-REVIEW-SLICE

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: rerun minimally sufficient backend checks for the reworked scope
- frontend: rerun targeted frontend checks if UI changed
- observability: repeat post-test digest, trace, and replay review

## Execution Hints
- rework_mode: bounded_fresh
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-LIGHT-RESUME-DOWNGRADE-W01-DIRECT-REWORK-MAIN-SLICE

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-LIGHT-RESUME-DOWNGRADE-W01-VERIFIER-REWORK-DIRECT-REWORK-MAIN-SLICE",
  "feature_id": "FEAT-LIGHT-RESUME-DOWNGRADE",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Direct Rework Main Slice",
  "summary": "Validate the architect-bounded direct rework for `FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-LIGHT-RESUME-DOWNGRADE-W01-DIRECT-REWORK-MAIN-SLICE",
    "FEAT-LIGHT-RESUME-DOWNGRADE-W01-REVIEW-SLICE"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "rerun minimally sufficient backend checks for the reworked scope",
    "frontend": "rerun targeted frontend checks if UI changed",
    "observability": "repeat post-test digest, trace, and replay review"
  },
  "execution_hints": {
    "rework_mode": "bounded_fresh",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_profile": "read-only",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-LIGHT-RESUME-DOWNGRADE-W01-DIRECT-REWORK-MAIN-SLICE"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-LIGHT-RESUME-DOWNGRADE-W01-MAIN-SLICE",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
