# Packet: FEAT-ARTIFACT-PUBLISH-W01-VERIFY-SLICE

## Title
Verify Slice

## GRACE IDs
- feature_ref: `feature:FEAT-ARTIFACT-PUBLISH`
- wave_ref: `feature:FEAT-ARTIFACT-PUBLISH:wave:W01`
- packet_ref: `feature:FEAT-ARTIFACT-PUBLISH:wave:W01:packet:FEAT-ARTIFACT-PUBLISH-W01-VERIFY-SLICE`

## Packet Type
execution

## Summary
Verify slice

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
-

## Inputs
-

## Acceptance Criteria
-

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review only

## Execution Hints
- runner: codex
- backend_profile: backend_quick
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
-

## Dependencies
- FEAT-ARTIFACT-PUBLISH-W01-MAIN-SLICE

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-ARTIFACT-PUBLISH-W01-VERIFY-SLICE",
  "feature_id": "FEAT-ARTIFACT-PUBLISH",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify Slice",
  "summary": "Verify slice",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {},
  "execution_hints": {
    "runner": "codex",
    "backend_profile": "backend_quick",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-ARTIFACT-PUBLISH-W01-MAIN-SLICE"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
