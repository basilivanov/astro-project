# Packet: FEAT-REWORK-HINTS-W01-IMPLEMENTATION

## Title
Implementation

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS`
- wave_ref: `feature:FEAT-REWORK-HINTS:wave:W01`
- packet_ref: `feature:FEAT-REWORK-HINTS:wave:W01:packet:FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Packet Type
execution

## Summary
Implementation summary

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-REWORK-HINTS-W01-IMPLEMENTATION`

## Write Scope
- Only files required by the packet.
- Bounded implementation/refactor required by the feature brief.

## Inputs
- planner output
- FEAT-REWORK-HINTS-W00-ARCHITECT-FORMALIZATION
- feature brief

## Acceptance Criteria
- Requested code change is implemented within scope.
- Targeted tests are added or updated if needed.
- Implementation notes are left for verifier and reviewer.

## Verification Profile
- backend: backend:quick or targeted tests as required by the packet
- frontend: targeted Playwright run if the packet touches UI
- observability: post-test log, digest, and trace review

## Execution Hints
- sandbox: danger-full-access
- resume_strategy: packet_parent
- resume_parent_packet_id: FEAT-REWORK-HINTS-W01-IMPLEMENTATION
- rework_mode: light_resume
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

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
-

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "feature_id": "FEAT-REWORK-HINTS",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "coder",
  "reasoning": "high",
  "title": "Implementation",
  "summary": "Implementation summary",
  "write_scope": [
    "Only files required by the packet.",
    "Bounded implementation/refactor required by the feature brief."
  ],
  "inputs": [
    "planner output",
    "FEAT-REWORK-HINTS-W00-ARCHITECT-FORMALIZATION",
    "feature brief"
  ],
  "acceptance_criteria": [
    "Requested code change is implemented within scope.",
    "Targeted tests are added or updated if needed.",
    "Implementation notes are left for verifier and reviewer."
  ],
  "verification_profile": {
    "backend": "backend:quick or targeted tests as required by the packet",
    "frontend": "targeted Playwright run if the packet touches UI",
    "observability": "post-test log, digest, and trace review"
  },
  "execution_hints": {
    "sandbox": "danger-full-access",
    "resume_strategy": "packet_parent",
    "resume_parent_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
    "rework_mode": "light_resume",
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
    }
  },
  "reviewer_gate": [
    "Packet scope respected.",
    "Verification handoff notes included."
  ],
  "dependencies": [],
  "notes": [
    "Prefer root-cause fixes.",
    "Strengthen logs if the packet touches runtime flow."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-REWORK-HINTS-W01-IMPLEMENTATION",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "light_resume",
  "rework_mode": "light_resume"
}
END_FINAL_PACKET_CONTRACT_JSON
