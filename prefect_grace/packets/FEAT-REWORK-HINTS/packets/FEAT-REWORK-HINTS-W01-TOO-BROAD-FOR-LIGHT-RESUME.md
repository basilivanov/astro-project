# Packet: FEAT-REWORK-HINTS-W01-TOO-BROAD-FOR-LIGHT-RESUME

## Title
Too Broad For Light Resume

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS`
- wave_ref: `feature:FEAT-REWORK-HINTS:wave:W01`
- packet_ref: `feature:FEAT-REWORK-HINTS:wave:W01:packet:FEAT-REWORK-HINTS-W01-TOO-BROAD-FOR-LIGHT-RESUME`

## Packet Type
rework

## Summary
Address architect-bounded rework for FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Needs planner because packet graph changes; Also requires business decision

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Review Target
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Write Scope
- Only the files required to address architect-bounded blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.

## Inputs
- Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.
- Reviewer blocker notes.
- Architect direct rework packet.

## Acceptance Criteria
- Architect-bounded blockers are addressed directly.
- No unrelated scope expansion.
- Updated verification evidence is ready for re-review.

## Verification Profile
- backend: rerun the minimally sufficient backend profile if backend code changed
- frontend: rerun targeted Playwright if UI changed
- observability: repeat post-test evidence review for the affected flow

## Execution Hints
- sandbox: danger-full-access
- resume_strategy: packet_parent
- resume_parent_packet_id: FEAT-REWORK-HINTS-W01-IMPLEMENTATION
- rework_mode: bounded_fresh
- light_resume_stage: True
- light_resume_scope: packet_local
- light_resume_source_packet_id: FEAT-REWORK-HINTS-W01-IMPLEMENTATION
- light_resume_attempt: 1
- light_resume_max_attempts: 1
- light_resume_title: Light Rework Main Slice
- light_resume_summary: Resume the existing coder packet for FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Small packet-local fix
- light_resume_write_scope:
  - Only the files required to address architect-bounded blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.
- light_resume_inputs:
  - Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.
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
  - Small packet-local fix
- light_resume_verification_profile: {'backend': 'rerun the minimally sufficient backend profile if backend code changed', 'frontend': 'rerun targeted Playwright if UI changed', 'observability': 'repeat post-test evidence review for the affected flow'}
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is not allowed for decomposition, business, or broad-scope blockers

## Reviewer Gate
- All architect-bounded blocker reasons are addressed.
- No new regressions are introduced in the scoped flow.

## Dependencies
- FEAT-REWORK-HINTS-W01-IMPLEMENTATION

## Notes
- This is an architect-bounded direct rework packet created after reviewer blockers.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-W01-TOO-BROAD-FOR-LIGHT-RESUME",
  "feature_id": "FEAT-REWORK-HINTS",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Too Broad For Light Resume",
  "summary": "Address architect-bounded rework for FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Needs planner because packet graph changes; Also requires business decision",
  "write_scope": [
    "Only the files required to address architect-bounded blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`."
  ],
  "inputs": [
    "Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.",
    "Reviewer blocker notes.",
    "Architect direct rework packet."
  ],
  "acceptance_criteria": [
    "Architect-bounded blockers are addressed directly.",
    "No unrelated scope expansion.",
    "Updated verification evidence is ready for re-review."
  ],
  "verification_profile": {
    "backend": "rerun the minimally sufficient backend profile if backend code changed",
    "frontend": "rerun targeted Playwright if UI changed",
    "observability": "repeat post-test evidence review for the affected flow"
  },
  "execution_hints": {
    "sandbox": "danger-full-access",
    "resume_strategy": "packet_parent",
    "resume_parent_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
    "rework_mode": "bounded_fresh",
    "light_resume_stage": true,
    "light_resume_scope": "packet_local",
    "light_resume_source_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
    "light_resume_attempt": 1,
    "light_resume_max_attempts": 1,
    "light_resume_title": "Light Rework Main Slice",
    "light_resume_summary": "Resume the existing coder packet for FEAT-REWORK-HINTS-W01-IMPLEMENTATION: Small packet-local fix",
    "light_resume_write_scope": [
      "Only the files required to address architect-bounded blockers from `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`."
    ],
    "light_resume_inputs": [
      "Parent packet `FEAT-REWORK-HINTS-W01-IMPLEMENTATION`.",
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
      "Small packet-local fix"
    ],
    "light_resume_verification_profile": {
      "backend": "rerun the minimally sufficient backend profile if backend code changed",
      "frontend": "rerun targeted Playwright if UI changed",
      "observability": "repeat post-test evidence review for the affected flow"
    },
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is not allowed for decomposition, business, or broad-scope blockers"
  },
  "reviewer_gate": [
    "All architect-bounded blocker reasons are addressed.",
    "No new regressions are introduced in the scoped flow."
  ],
  "dependencies": [
    "FEAT-REWORK-HINTS-W01-IMPLEMENTATION"
  ],
  "notes": [
    "This is an architect-bounded direct rework packet created after reviewer blockers."
  ],
  "parent_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "review_target_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "light_resume",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
