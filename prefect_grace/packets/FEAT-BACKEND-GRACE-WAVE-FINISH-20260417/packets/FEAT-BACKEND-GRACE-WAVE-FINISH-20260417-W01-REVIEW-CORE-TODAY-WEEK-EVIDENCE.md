# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-REVIEW-CORE-TODAY-WEEK-EVIDENCE

## Title
Review Core Today Week Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-REVIEW-CORE-TODAY-WEEK-EVIDENCE`

## Packet Type
gate_decision

## Summary
Review W01 scope containment and packet-local evidence completeness.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/reviews/**

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE

## Acceptance Criteria
- Diff stays inside W01 scope.
- Core evidence is current-run and attributable.
- W01 does not claim final canonical closeout.

## Verification Profile
- backend: Consume verifier evidence.
- frontend: not applicable
- observability: Consume read-only packet-local verdict.

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- Reject silent scope expansion.
- Reject missing evidence attribution.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE

## Notes
- If the blocker is local, route bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-REVIEW-CORE-TODAY-WEEK-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Review Core Today Week Evidence",
  "summary": "Review W01 scope containment and packet-local evidence completeness.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/reviews/**"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE"
  ],
  "acceptance_criteria": [
    "Diff stays inside W01 scope.",
    "Core evidence is current-run and attributable.",
    "W01 does not claim final canonical closeout."
  ],
  "verification_profile": {
    "backend": "Consume verifier evidence.",
    "frontend": "not applicable",
    "observability": "Consume read-only packet-local verdict."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "Reject silent scope expansion.",
    "Reject missing evidence attribution."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE"
  ],
  "notes": [
    "If the blocker is local, route bounded direct rework."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
