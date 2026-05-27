# Packet: FEAT-PACKET-CONTRACT-W01-MAIN-SLICE

## Title
Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-PACKET-CONTRACT`
- wave_ref: `feature:FEAT-PACKET-CONTRACT:wave:W01`
- packet_ref: `feature:FEAT-PACKET-CONTRACT:wave:W01:packet:FEAT-PACKET-CONTRACT-W01-MAIN-SLICE`

## Packet Type
execution

## Summary
Implement a bounded slice.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
-

## Write Scope
- frontend/app/page.tsx

## Inputs
- architect formalization

## Acceptance Criteria
- Packet contract stays compact.

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review only

## Execution Hints
-

## Reviewer Gate
- No unrelated scope expansion.

## Dependencies
-

## Notes
- packet.md is the primary contract.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-PACKET-CONTRACT-W01-MAIN-SLICE",
  "feature_id": "FEAT-PACKET-CONTRACT",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Main Slice",
  "summary": "Implement a bounded slice.",
  "write_scope": [
    "frontend/app/page.tsx"
  ],
  "inputs": [
    "architect formalization"
  ],
  "acceptance_criteria": [
    "Packet contract stays compact."
  ],
  "verification_profile": {},
  "execution_hints": {},
  "reviewer_gate": [
    "No unrelated scope expansion."
  ],
  "dependencies": [],
  "notes": [
    "packet.md is the primary contract."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
