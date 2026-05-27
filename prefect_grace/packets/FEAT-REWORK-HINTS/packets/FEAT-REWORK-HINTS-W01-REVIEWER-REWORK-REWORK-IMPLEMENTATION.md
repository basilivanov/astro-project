# Packet: FEAT-REWORK-HINTS-W01-REVIEWER-REWORK-REWORK-IMPLEMENTATION

## Title
Reviewer Rework Rework Implementation

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS`
- wave_ref: `feature:FEAT-REWORK-HINTS:wave:W01`
- packet_ref: `feature:FEAT-REWORK-HINTS:wave:W01:packet:FEAT-REWORK-HINTS-W01-REVIEWER-REWORK-REWORK-IMPLEMENTATION`

## Packet Type
gate_decision

## Summary
Review whether the localized rework for `FEAT-REWORK-HINTS-W01-IMPLEMENTATION` addressed the reviewer blockers.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Review Target
`FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION
- FEAT-REWORK-HINTS-W01-VERIFIER-REWORK-REWORK-IMPLEMENTATION

## Acceptance Criteria
- Exactly one verdict is returned.
- The original blockers are either resolved or explicitly remain.
- No unrelated scope expansion is accepted.

## Verification Profile
- backend: consume verifier evidence
- frontend: consume verifier evidence
- observability: consume verifier evidence

## Execution Hints
- sandbox: danger-full-access

## Reviewer Gate
- Assess only the original blocker scope.
- Escalate only if blockers imply decomposition or business changes.

## Dependencies
- FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION
- FEAT-REWORK-HINTS-W01-VERIFIER-REWORK-REWORK-IMPLEMENTATION

## Notes
- This reviewer packet was auto-created from reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-W01-REVIEWER-REWORK-REWORK-IMPLEMENTATION",
  "feature_id": "FEAT-REWORK-HINTS",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Rework Implementation",
  "summary": "Review whether the localized rework for `FEAT-REWORK-HINTS-W01-IMPLEMENTATION` addressed the reviewer blockers.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION",
    "FEAT-REWORK-HINTS-W01-VERIFIER-REWORK-REWORK-IMPLEMENTATION"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "The original blockers are either resolved or explicitly remain.",
    "No unrelated scope expansion is accepted."
  ],
  "verification_profile": {
    "backend": "consume verifier evidence",
    "frontend": "consume verifier evidence",
    "observability": "consume verifier evidence"
  },
  "execution_hints": {
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "Assess only the original blocker scope.",
    "Escalate only if blockers imply decomposition or business changes."
  ],
  "dependencies": [
    "FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION",
    "FEAT-REWORK-HINTS-W01-VERIFIER-REWORK-REWORK-IMPLEMENTATION"
  ],
  "notes": [
    "This reviewer packet was auto-created from reviewer blockers."
  ],
  "parent_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "review_target_packet_id": "FEAT-REWORK-HINTS-W01-REWORK-IMPLEMENTATION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
