# Packet: FEAT-VERIFY-OVERRIDE-W01-SEED-IMPLEMENTATION

## Title
Seed implementation

## GRACE IDs
- feature_ref: `feature:FEAT-VERIFY-OVERRIDE`
- wave_ref: `feature:FEAT-VERIFY-OVERRIDE:wave:W01`
- packet_ref: `feature:FEAT-VERIFY-OVERRIDE:wave:W01:packet:FEAT-VERIFY-OVERRIDE-W01-SEED-IMPLEMENTATION`

## Packet Type
execution

## Summary
Seed implementation summary

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
- Only files required by the packet.
- Bounded implementation/refactor required by the feature brief.

## Inputs
- planner output
- FEAT-VERIFY-OVERRIDE-W00-ARCHITECT-FORMALIZATION
- feature brief

## Acceptance Criteria
- Requested code change is implemented within scope.
- Targeted tests are added or updated if needed.
- Implementation notes are left for verifier and reviewer.

## Verification Profile
- backend: backend:quick or targeted tests as required by the packet
- frontend: targeted Playwright run if the packet touches UI
- observability: post-test log, digest, and trace review

## Execution Hints
-

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
-

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-VERIFY-OVERRIDE-W01-SEED-IMPLEMENTATION",
  "feature_id": "FEAT-VERIFY-OVERRIDE",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Seed implementation",
  "summary": "Seed implementation summary",
  "write_scope": [
    "Only files required by the packet.",
    "Bounded implementation/refactor required by the feature brief."
  ],
  "inputs": [
    "planner output",
    "FEAT-VERIFY-OVERRIDE-W00-ARCHITECT-FORMALIZATION",
    "feature brief"
  ],
  "acceptance_criteria": [
    "Requested code change is implemented within scope.",
    "Targeted tests are added or updated if needed.",
    "Implementation notes are left for verifier and reviewer."
  ],
  "verification_profile": {
    "backend": "backend:quick or targeted tests as required by the packet",
    "frontend": "targeted Playwright run if the packet touches UI",
    "observability": "post-test log, digest, and trace review"
  },
  "execution_hints": {},
  "reviewer_gate": [
    "Packet scope respected.",
    "Verification handoff notes included."
  ],
  "dependencies": [],
  "notes": [
    "Prefer root-cause fixes.",
    "Strengthen logs if the packet touches runtime flow."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
