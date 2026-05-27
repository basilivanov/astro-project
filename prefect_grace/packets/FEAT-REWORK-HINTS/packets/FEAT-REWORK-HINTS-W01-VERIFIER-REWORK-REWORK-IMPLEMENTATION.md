# Packet: FEAT-REWORK-HINTS-W01-VERIFIER-REWORK-REWORK-IMPLEMENTATION

## Title
Verifier Rework Rework Implementation

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS`
- wave_ref: `feature:FEAT-REWORK-HINTS:wave:W01`
- packet_ref: `feature:FEAT-REWORK-HINTS:wave:W01:packet:FEAT-REWORK-HINTS-W01-VERIFIER-REWORK-REWORK-IMPLEMENTATION`

## Packet Type
rework

## Summary
Validate the localized rework for `FEAT-REWORK-HINTS-W01-IMPLEMENTATION` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION
- FEAT-REWORK-HINTS-W01-REVIEWER-VERDICT

## Acceptance Criteria
- Commands run are recorded for the rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the rework.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- sandbox: danger-full-access
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION

## Notes
- This verifier packet was auto-created from reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-W01-VERIFIER-REWORK-REWORK-IMPLEMENTATION",
  "feature_id": "FEAT-REWORK-HINTS",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Rework Implementation",
  "summary": "Validate the localized rework for `FEAT-REWORK-HINTS-W01-IMPLEMENTATION` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION",
    "FEAT-REWORK-HINTS-W01-REVIEWER-VERDICT"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the rework."
  ],
  "verification_profile": {
    "backend": "execute minimally sufficient backend profile",
    "frontend": "execute minimally sufficient frontend profile if UI is touched",
    "observability": "mandatory log, replay, digest, and trace review"
  },
  "execution_hints": {
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "frontend_profile": null,
    "frontend_commands": [],
    "observability_profile": "read-only",
    "observability_commands": [],
    "observability_scope": "packet_local",
    "canonical_flow_commands": [],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "artifact_globs": [],
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence must correspond to the rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION"
  ],
  "notes": [
    "This verifier packet was auto-created from reviewer blockers."
  ],
  "parent_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
