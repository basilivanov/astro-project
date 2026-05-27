# Packet: FEAT-LIGHT-RESUME-LOOP-STOP-W01-ARCHITECT-REWORK-MAIN-SLICE

## Title
Architect Rework Main Slice

## GRACE IDs
- feature_ref: `feature:FEAT-LIGHT-RESUME-LOOP-STOP`
- wave_ref: `feature:FEAT-LIGHT-RESUME-LOOP-STOP:wave:W01`
- packet_ref: `feature:FEAT-LIGHT-RESUME-LOOP-STOP:wave:W01:packet:FEAT-LIGHT-RESUME-LOOP-STOP-W01-ARCHITECT-REWORK-MAIN-SLICE`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Fix another small typo

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`

## Review Target
`FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`.
- Reviewer packet `FEAT-LIGHT-RESUME-LOOP-STOP-W01-REVIEWER-REWORK-MAIN-SLICE`.
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
- resume_strategy: packet_parent
- resume_parent_packet_id: FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE
- rework_mode: light_resume
- light_resume_stage: True
- light_resume_scope: packet_local
- light_resume_source_packet_id: FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE
- light_resume_attempt: 1
- light_resume_max_attempts: 1
- light_resume_title: Light Resume Main Slice
- light_resume_summary: Resume the existing coder packet for FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE: Fix one small typo
- light_resume_write_scope:
  - Only the files required to address architect-bounded blockers from `FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`.
- light_resume_inputs:
  - Parent packet `FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`.
  - Reviewer blocker notes.
  - Architect direct rework packet.
- light_resume_acceptance_criteria:
  - Architect-bounded blockers are addressed directly.
  - No unrelated scope expansion.
  - Updated verification evidence is ready for re-review.
- light_resume_reviewer_gate:
  - All architect-bounded blocker reasons are addressed.
  - No new regressions are introduced in the scoped flow.
- light_resume_notes:
  - This packet was resumed in-place as an architect-bounded light rework stage.
- light_resume_reasons:
  - Fix one small typo
- light_resume_verification_profile: {'backend': 'rerun the minimally sufficient backend profile if backend code changed', 'frontend': 'rerun targeted Playwright if UI changed', 'observability': 'repeat post-test evidence review for the affected flow'}
- light_resume_reviewer_packet_id: FEAT-LIGHT-RESUME-LOOP-STOP-W01-REVIEW-SLICE

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE
- FEAT-LIGHT-RESUME-LOOP-STOP-W01-REVIEWER-REWORK-MAIN-SLICE

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
  "packet_id": "FEAT-LIGHT-RESUME-LOOP-STOP-W01-ARCHITECT-REWORK-MAIN-SLICE",
  "feature_id": "FEAT-LIGHT-RESUME-LOOP-STOP",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Main Slice",
  "summary": "Review reviewer blockers for FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Fix another small typo",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`.",
    "Reviewer packet `FEAT-LIGHT-RESUME-LOOP-STOP-W01-REVIEWER-REWORK-MAIN-SLICE`.",
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
    "resume_strategy": "packet_parent",
    "resume_parent_packet_id": "FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE",
    "rework_mode": "light_resume",
    "light_resume_stage": true,
    "light_resume_scope": "packet_local",
    "light_resume_source_packet_id": "FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE",
    "light_resume_attempt": 1,
    "light_resume_max_attempts": 1,
    "light_resume_title": "Light Resume Main Slice",
    "light_resume_summary": "Resume the existing coder packet for FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE: Fix one small typo",
    "light_resume_write_scope": [
      "Only the files required to address architect-bounded blockers from `FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`."
    ],
    "light_resume_inputs": [
      "Parent packet `FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE`.",
      "Reviewer blocker notes.",
      "Architect direct rework packet."
    ],
    "light_resume_acceptance_criteria": [
      "Architect-bounded blockers are addressed directly.",
      "No unrelated scope expansion.",
      "Updated verification evidence is ready for re-review."
    ],
    "light_resume_reviewer_gate": [
      "All architect-bounded blocker reasons are addressed.",
      "No new regressions are introduced in the scoped flow."
    ],
    "light_resume_notes": [
      "This packet was resumed in-place as an architect-bounded light rework stage."
    ],
    "light_resume_reasons": [
      "Fix one small typo"
    ],
    "light_resume_verification_profile": {
      "backend": "rerun the minimally sufficient backend profile if backend code changed",
      "frontend": "rerun targeted Playwright if UI changed",
      "observability": "repeat post-test evidence review for the affected flow"
    },
    "light_resume_reviewer_packet_id": "FEAT-LIGHT-RESUME-LOOP-STOP-W01-REVIEW-SLICE"
  },
  "reviewer_gate": [
    "Do not widen scope beyond the reviewer blockers.",
    "Prefer bounded coder rework over user escalation when the blocker is self-resolvable."
  ],
  "dependencies": [
    "FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE",
    "FEAT-LIGHT-RESUME-LOOP-STOP-W01-REVIEWER-REWORK-MAIN-SLICE"
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
  "parent_packet_id": "FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE",
  "review_target_packet_id": "FEAT-LIGHT-RESUME-LOOP-STOP-W01-MAIN-SLICE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
