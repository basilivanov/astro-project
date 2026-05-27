# Packet: FEAT-MULTI-WAVE-W01-VERIFY-BACKEND-SLICE

## Title
Verify Backend Slice

## GRACE IDs
- feature_ref: `feature:FEAT-MULTI-WAVE`
- wave_ref: `feature:FEAT-MULTI-WAVE:wave:W01`
- packet_ref: `feature:FEAT-MULTI-WAVE:wave:W01:packet:FEAT-MULTI-WAVE-W01-VERIFY-BACKEND-SLICE`

## Packet Type
execution

## Summary
Verify backend slice

## Wave
W01

## Role
verifier

## Reasoning
high

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
- observability_profile: read-only
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
-

## Dependencies
- FEAT-MULTI-WAVE-W01-BACKEND-SLICE

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-MULTI-WAVE-W01-VERIFY-BACKEND-SLICE",
  "feature_id": "FEAT-MULTI-WAVE",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Verify Backend Slice",
  "summary": "Verify backend slice",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {},
  "execution_hints": {
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_profile": "read-only",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-MULTI-WAVE-W01-BACKEND-SLICE"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
