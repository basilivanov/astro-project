# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-REVIEW-FINAL-CANONICAL-CLOSEOUT

## Title
Review Final Canonical Closeout

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W03:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-REVIEW-FINAL-CANONICAL-CLOSEOUT`

## Packet Type
gate_decision

## Summary
Review final canonical evidence and decide whether architect acceptance is unblocked.

## Wave
W03

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT`

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/reviews/**

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT

## Acceptance Criteria
- Canonical today-week verdict is non-blocking.
- Hub review is explicit.
- Frozen scope remained frozen.

## Verification Profile
- backend: Consume final verifier evidence.
- frontend: not applicable
- observability: Consume today-week and read-only final verdicts.

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- Reject missing canonical evidence.
- Reject hidden hub ambiguity.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT

## Notes
- If blocked, route bounded rework to the local failing wave.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-REVIEW-FINAL-CANONICAL-CLOSEOUT",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W03",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Review Final Canonical Closeout",
  "summary": "Review final canonical evidence and decide whether architect acceptance is unblocked.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/reviews/**"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT"
  ],
  "acceptance_criteria": [
    "Canonical today-week verdict is non-blocking.",
    "Hub review is explicit.",
    "Frozen scope remained frozen."
  ],
  "verification_profile": {
    "backend": "Consume final verifier evidence.",
    "frontend": "not applicable",
    "observability": "Consume today-week and read-only final verdicts."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "Reject missing canonical evidence.",
    "Reject hidden hub ambiguity."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT"
  ],
  "notes": [
    "If blocked, route bounded rework to the local failing wave."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
