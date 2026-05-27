# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REVIEWER-VERDICT

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REVIEWER-VERDICT`

## Summary
Review the coder diff and verifier evidence against the bounded Week slice and either accept the coder packet or route precise rework.

## Wave
W01

## Role
reviewer

## Reasoning
high

## Write Scope
- no_repo_writes

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE

## Acceptance Criteria
- Reviewer confirms the coder output stayed inside the approved Week write scope and respected all frozen modules.
- Reviewer confirms the disclosure exposes only render path, bootstrap result, and current mode and stays local to the chip area.
- Reviewer confirms verifier artifacts prove dev-collapsed, dev-expanded, and prod-unchanged states and that the Week top area remains non-banner-like.
- Reviewer confirms the FLOW-TODAY-WEEK-WEEK verdict is explicit and acceptable.
- Reviewer issues an accept or reject decision for the coder packet without widening the slice.

## Verification Profile
- backend: Read-only review; confirm no backend surface, payload contract, or business-logic lane changed.
- frontend: Inspect the coder diff plus visual artifacts to validate compact collapsed state, local disclosure containment, and production inertness.
- observability: Inspect the existing wave-final Week observability evidence and explicit verdict; do not run new observability commands in this packet.
- execution:
  - backend_commands:
  - frontend_commands:
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept only when the coder packet can be explicitly accepted or rejected with evidence-backed reasoning.
- Route rework if the diff, visual proof, or observability verdict leaves local containment, production inertness, or scope adherence ambiguous.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-VERIFIER-EVIDENCE

## Notes
- The review target is the single coder packet for W01; verifier output is supporting evidence, not the review target.
- If evidence and diff disagree, reject the coder packet and route specific rework inside the approved Week slice.
