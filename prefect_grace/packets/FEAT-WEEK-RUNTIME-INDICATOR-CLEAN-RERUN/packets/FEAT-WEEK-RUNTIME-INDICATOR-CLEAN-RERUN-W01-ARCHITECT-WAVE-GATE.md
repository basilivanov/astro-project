# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-ARCHITECT-WAVE-GATE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-ARCHITECT-WAVE-GATE`

## Summary
Accept or block W01 against the feature-local architect manifest, frozen scope, verification evidence, and reviewer verdict.

## Wave
W01

## Role
architect

## Reasoning
high

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN/**

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-REVIEWER-VERDICT

## Acceptance Criteria
- Reviewer verdict accepts coder_week_runtime_indicator_disclosure.
- The implemented slice remains a Week-only frontend helper rerun.
- No frozen scope or deferred work was pulled into W01.
- Verification evidence covers unit, behavior, visual, and packet-local read-only observability lanes.
- The final observability verdict is clean or degraded-but-expected, not unexpected-degradation or no-evidence-blocker.
- Architect accepts that no canonical Today/Week closeout is owned by this rerun wave.

## Verification Profile
- backend: No backend execution is expected at the architect gate; scope review must confirm backend remains frozen.
- frontend: Architect reviews the verifier and reviewer evidence for the Week-only UI outcome and visual expectations.
- observability: Architect reviews packet-local evidence ownership only and must not require canonical Today/Week flow evidence for this wave.
- execution:
  - backend_commands:
  - frontend_commands:
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - /opt/astro-project/frontend/docs/review_evidence/front/day-week/2026-04-15-week-runtime-indicator/**

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept the wave only if the reviewer verdict is accepted and evidence satisfies architect manifest criteria.
- Block the wave if any acceptance criterion is unmet.
- Block the wave if canonical Today/Week ownership was added contrary to the architect manifest.
- Block the wave if implementation widened into backend, Day, WeekBrief, useTelegram internals, or unrelated Week panels.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN-W01-REVIEWER-VERDICT

## Notes
- This is a gate packet, not an implementation packet.
- If blocked, route rework to coder_week_runtime_indicator_disclosure with the failed acceptance condition.
