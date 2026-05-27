# Packet: FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-REVIEWER-VERDICT

## Title
Reviewer Verdict

## GRACE IDs
- feature_ref: `feature:FEAT-PREFECT-NATIVE-QUEUE-SMOKE`
- wave_ref: `feature:FEAT-PREFECT-NATIVE-QUEUE-SMOKE:wave:W01`
- packet_ref: `feature:FEAT-PREFECT-NATIVE-QUEUE-SMOKE:wave:W01:packet:FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-REVIEWER-VERDICT`

## Packet Type
gate_decision

## Summary
Judge the packet outcome and decide accepted, rework_required, blocked, or escalate_to_architect.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
-

## Review Target
`FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET
- FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-VERIFIER-EVIDENCE

## Acceptance Criteria
- Exactly one verdict is returned.
- Blockers are actionable.
- Follow-up action is explicit.

## Verification Profile
- backend: not required
- frontend: not required
- observability: consume verifier evidence and notes

## Execution Hints
-

## Reviewer Gate
- Do not invent new scope.
- Do not accept missing evidence.

## Dependencies
- FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET
- FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-VERIFIER-EVIDENCE

## Notes
- Escalate to architect when the blocker changes decomposition or business semantics.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-REVIEWER-VERDICT",
  "feature_id": "FEAT-PREFECT-NATIVE-QUEUE-SMOKE",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Verdict",
  "summary": "Judge the packet outcome and decide accepted, rework_required, blocked, or escalate_to_architect.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET",
    "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-VERIFIER-EVIDENCE"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "Blockers are actionable.",
    "Follow-up action is explicit."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "consume verifier evidence and notes"
  },
  "execution_hints": {},
  "reviewer_gate": [
    "Do not invent new scope.",
    "Do not accept missing evidence."
  ],
  "dependencies": [
    "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET",
    "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-VERIFIER-EVIDENCE"
  ],
  "notes": [
    "Escalate to architect when the blocker changes decomposition or business semantics."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-PREFECT-NATIVE-QUEUE-SMOKE-W01-LIVE-IMPLEMENTATION-PACKET",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
