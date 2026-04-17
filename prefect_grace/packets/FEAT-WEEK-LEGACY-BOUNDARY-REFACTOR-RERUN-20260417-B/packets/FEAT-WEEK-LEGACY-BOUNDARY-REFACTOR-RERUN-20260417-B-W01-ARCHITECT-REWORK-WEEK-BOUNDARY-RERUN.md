# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-ARCHITECT-REWORK-WEEK-BOUNDARY-RERUN

## Title
Architect Rework Week Boundary Rerun

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-ARCHITECT-REWORK-WEEK-BOUNDARY-RERUN`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Required Playwright verification failed for the raw-slug legacy fallback guard.; Legacy-only boundary evidence is incomplete until week-page-fallback.spec.ts passes.; Visual proof and packet-local observability are sufficient, so this is localized product/test rework rather than a pipeline block.

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`.
- Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT`.
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
- workdir: /opt/astro-project

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT

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
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-ARCHITECT-REWORK-WEEK-BOUNDARY-RERUN",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Week Boundary Rerun",
  "summary": "Review reviewer blockers for FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Required Playwright verification failed for the raw-slug legacy fallback guard.; Legacy-only boundary evidence is incomplete until week-page-fallback.spec.ts passes.; Visual proof and packet-local observability are sufficient, so this is localized product/test rework rather than a pipeline block.",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`.",
    "Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT`.",
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
  "execution_hints": {
    "workdir": "/opt/astro-project"
  },
  "reviewer_gate": [
    "Do not widen scope beyond the reviewer blockers.",
    "Prefer bounded coder rework over user escalation when the blocker is self-resolvable."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-VERDICT"
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
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
