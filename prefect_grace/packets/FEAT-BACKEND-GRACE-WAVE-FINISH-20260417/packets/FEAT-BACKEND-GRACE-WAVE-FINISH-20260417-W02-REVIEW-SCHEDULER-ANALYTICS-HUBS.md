# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-REVIEW-SCHEDULER-ANALYTICS-HUBS

## Title
Review Scheduler Analytics Hubs

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W02:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-REVIEW-SCHEDULER-ANALYTICS-HUBS`

## Packet Type
gate_decision

## Summary
Review W02 scope containment and packet-local hub evidence completeness.

## Wave
W02

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/reviews/**

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-VERIFY-SCHEDULER-ANALYTICS-HUBS

## Acceptance Criteria
- Diff stays inside W02 scope.
- Scheduler and analytics hub evidence is explicit.
- W02 does not claim final canonical closeout.

## Verification Profile
- backend: Consume verifier evidence.
- frontend: not applicable
- observability: Consume read-only packet-local verdict.

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- Reject silent hub ambiguity.
- Reject scope expansion.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-VERIFY-SCHEDULER-ANALYTICS-HUBS

## Notes
- If the blocker is local, route bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-REVIEW-SCHEDULER-ANALYTICS-HUBS",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W02",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Review Scheduler Analytics Hubs",
  "summary": "Review W02 scope containment and packet-local hub evidence completeness.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/reviews/**"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE",
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-VERIFY-SCHEDULER-ANALYTICS-HUBS"
  ],
  "acceptance_criteria": [
    "Diff stays inside W02 scope.",
    "Scheduler and analytics hub evidence is explicit.",
    "W02 does not claim final canonical closeout."
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
    "Reject silent hub ambiguity.",
    "Reject scope expansion."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE",
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-VERIFY-SCHEDULER-ANALYTICS-HUBS"
  ],
  "notes": [
    "If the blocker is local, route bounded direct rework."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
