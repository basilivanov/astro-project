# Packet: FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-REVIEWER-VERDICT

## Title
Reviewer Verdict

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ`
- wave_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ:wave:W03:packet:FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-REVIEWER-VERDICT`

## Packet Type
gate_decision

## Summary
Judge the final canonical backend evidence and decide whether the feature is ready for architect acceptance.

## Wave
W03

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE
- FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-ARCHITECT-WAVE-GATE

## Acceptance Criteria
- Exactly one verdict is returned.
- Blockers are actionable.
- Reviewer explicitly calls out any frozen-scope drift or canonical evidence blocker.

## Verification Profile
- backend: not required
- frontend: not required
- observability: consume final verifier evidence and verdict

## Execution Hints
- workdir: /opt/astro-project

## Reviewer Gate
- Do not accept missing canonical evidence.
- Do not widen scope during closeout.

## Dependencies
- FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE

## Notes
- Escalate only when the blocker changes business boundaries or invalidates the wave graph.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-REVIEWER-VERDICT",
  "feature_id": "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ",
  "wave_id": "W03",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Verdict",
  "summary": "Judge the final canonical backend evidence and decide whether the feature is ready for architect acceptance.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE",
    "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W02-ARCHITECT-WAVE-GATE"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "Blockers are actionable.",
    "Reviewer explicitly calls out any frozen-scope drift or canonical evidence blocker."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "consume final verifier evidence and verdict"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "Do not accept missing canonical evidence.",
    "Do not widen scope during closeout."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE"
  ],
  "notes": [
    "Escalate only when the blocker changes business boundaries or invalidates the wave graph."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-GRACE-OBSERVABILITY-WAVE-TZ-W03-VERIFIER-EVIDENCE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
