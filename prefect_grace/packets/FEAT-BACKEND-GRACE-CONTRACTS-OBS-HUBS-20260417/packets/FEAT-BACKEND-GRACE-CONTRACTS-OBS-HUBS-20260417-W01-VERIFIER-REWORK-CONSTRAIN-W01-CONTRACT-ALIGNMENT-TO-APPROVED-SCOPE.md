# Packet: FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-VERIFIER-REWORK-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE

## Title
Verifier Rework Constrain W01 Contract Alignment To Approved Scope

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-VERIFIER-REWORK-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-VERDICT

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: backend:quick plus targeted hub pytest bundle
- frontend: not required
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh
- runner: codex
- backend_profile: backend_quick
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-VERIFIER-REWORK-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE",
  "feature_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Constrain W01 Contract Alignment To Approved Scope",
  "summary": "Validate the architect-bounded direct rework for `FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE",
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-VERDICT"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "backend:quick plus targeted hub pytest bundle",
    "frontend": "not required",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-CONSTRAIN-W01-CONTRACT-ALIGNMENT-TO-APPROVED-SCOPE"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417-W01-BACKEND-HUB-CONTRACT-ALIGNMENT",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
