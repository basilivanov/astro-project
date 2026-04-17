# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-REVIEWER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD

## Title
Reviewer Rework Fix Week Legacy Raw-Slug Fallback Guard

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-REVIEWER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD`

## Packet Type
gate_decision

## Summary
Review whether the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN` addressed the reviewer blockers.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-VERIFIER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD

## Acceptance Criteria
- Exactly one verdict is returned.
- The original blockers are either resolved or explicitly remain.
- No unrelated scope expansion is accepted.

## Verification Profile
- backend: consume verifier evidence
- frontend: consume verifier evidence
- observability: consume verifier evidence

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to at most two small blocker reasons

## Reviewer Gate
- Assess only the original blocker scope.
- Escalate only if blockers imply decomposition or business changes.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-VERIFIER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD

## Notes
- This reviewer packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-REVIEWER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Fix Week Legacy Raw-Slug Fallback Guard",
  "summary": "Review whether the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN` addressed the reviewer blockers.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-VERIFIER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "The original blockers are either resolved or explicitly remain.",
    "No unrelated scope expansion is accepted."
  ],
  "verification_profile": {
    "backend": "consume verifier evidence",
    "frontend": "consume verifier evidence",
    "observability": "consume verifier evidence"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to at most two small blocker reasons"
  },
  "reviewer_gate": [
    "Assess only the original blocker scope.",
    "Escalate only if blockers imply decomposition or business changes."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-VERIFIER-REWORK-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD"
  ],
  "notes": [
    "This reviewer packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-WEEK-BOUNDARY-RERUN",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-B-W01-FIX-WEEK-LEGACY-RAW-SLUG-FALLBACK-GUARD",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
