# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## Title
Verifier Rework Packet-Local Evidence Freshness Rework

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: execute minimally sufficient backend profile
- frontend: execute minimally sufficient frontend profile if UI is touched
- observability: mandatory log, replay, digest, and trace review

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh
- runner: codex
- backend_profile: backend_quick
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK",
  "feature_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Packet-Local Evidence Freshness Rework",
  "summary": "Validate the architect-bounded direct rework for `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK",
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "execute minimally sufficient backend profile",
    "frontend": "execute minimally sufficient frontend profile if UI is touched",
    "observability": "mandatory log, replay, digest, and trace review"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh",
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
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
