# Packet: FEAT-SMALL-FIX-ALIAS-W01-ARCHITECT-REWORK-MAIN-SLICE

## Title
Architect Rework Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-SMALL-FIX-ALIAS`
- wave_ref: `feature:FEAT-SMALL-FIX-ALIAS:wave:W01`
- packet_ref: `feature:FEAT-SMALL-FIX-ALIAS:wave:W01:packet:FEAT-SMALL-FIX-ALIAS-W01-ARCHITECT-REWORK-MAIN-SLICE`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Fix one narrow typo

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE`

## Review Target
`FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE`.
- Reviewer packet `FEAT-SMALL-FIX-ALIAS-W01-REVIEW-SLICE`.
- Reviewer blocker notes and latest verifier evidence.

## Acceptance Criteria
- Architect classifies the blocker as self-resolvable, requires_user_decision, or requires_planner.
- If self-resolvable, architect returns a bounded direct rework packet for coder.
- If escalation is required, architect states the narrowest blocking reason.

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review only

## Execution Hints
-

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE
- FEAT-SMALL-FIX-ALIAS-W01-REVIEW-SLICE

## Notes
- Return FINAL_DIRECT_REWORK_PACKET_JSON.
- Use route_classification=self_resolvable_rework when the next step is a bounded coder packet.
- Use rework_mode=light_resume only for small packet-local fixes that can safely reuse coder context.
- Use rework_mode=bounded_fresh for bounded fixes that still need a fresh coder packet.
- Use rework_mode=decision_required when the blocker should not resume coder work directly.
- Use requires_user_decision only for true business/product/user decisions.
- Use requires_planner only when packet graph or decomposition must change.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-SMALL-FIX-ALIAS-W01-ARCHITECT-REWORK-MAIN-SLICE",
  "feature_id": "FEAT-SMALL-FIX-ALIAS",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Main Slice",
  "summary": "Review reviewer blockers for FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Fix one narrow typo",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE`.",
    "Reviewer packet `FEAT-SMALL-FIX-ALIAS-W01-REVIEW-SLICE`.",
    "Reviewer blocker notes and latest verifier evidence."
  ],
  "acceptance_criteria": [
    "Architect classifies the blocker as self-resolvable, requires_user_decision, or requires_planner.",
    "If self-resolvable, architect returns a bounded direct rework packet for coder.",
    "If escalation is required, architect states the narrowest blocking reason."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "artifact review only"
  },
  "execution_hints": {},
  "reviewer_gate": [
    "Do not widen scope beyond the reviewer blockers.",
    "Prefer bounded coder rework over user escalation when the blocker is self-resolvable."
  ],
  "dependencies": [
    "FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE",
    "FEAT-SMALL-FIX-ALIAS-W01-REVIEW-SLICE"
  ],
  "notes": [
    "Return FINAL_DIRECT_REWORK_PACKET_JSON.",
    "Use route_classification=self_resolvable_rework when the next step is a bounded coder packet.",
    "Use rework_mode=light_resume only for small packet-local fixes that can safely reuse coder context.",
    "Use rework_mode=bounded_fresh for bounded fixes that still need a fresh coder packet.",
    "Use rework_mode=decision_required when the blocker should not resume coder work directly.",
    "Use requires_user_decision only for true business/product/user decisions.",
    "Use requires_planner only when packet graph or decomposition must change."
  ],
  "parent_packet_id": "FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE",
  "review_target_packet_id": "FEAT-SMALL-FIX-ALIAS-W01-MAIN-SLICE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
