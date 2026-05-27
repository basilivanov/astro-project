# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-REPAIR-ARCHITECT-SLICE-BOUNDARIES

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-REPAIR-ARCHITECT-SLICE-BOUNDARIES`

## Summary
Resolve the blocker created by incomplete slice artifacts: impacted modules are empty, W01 wave fields are placeholders, write scope is not executable, and observability ownership conflicts with the formalization note.

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Write Scope
- /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/architect_manifest.json
- /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/development-plan.slice.expandable-dev-indicator-on-week-screen-clean.xml
- /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/verification-matrix.slice.expandable-dev-indicator-on-week-screen-clean.md
- /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/knowledge-graph.slice.expandable-dev-indicator-on-week-screen-clean.xml
- /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/ARCHITECT_HANDOFF.md

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W00-ARCHITECT-FORMALIZATION

## Acceptance Criteria
- architect_manifest.impacted_modules is no longer empty and names the authorized Week helper/module boundary, or the architect formally changes the feature to no-code with rationale.
- architect_manifest.waves contains W01 metadata aligned with the development-plan slice.
- development-plan W01 goal is concrete and no longer `None` or `-`.
- development-plan W01 allowed_write_scope lists exact authorized frontend and test artifact paths or module paths; backend, Day, payload, scoring, explainability, and business-logic paths remain excluded.
- development-plan W01 frozen_scope explicitly excludes backend payload fields, Day screen, top-level debug banners, separate diagnostics screens, correlation diagnostics, trace diagnostics, and user-facing payload diagnostics.
- development-plan W01 observability_scope is resolved consistently across slice docs as `none` or `packet_local`; `wave_final` is not introduced unless canonical emitter commands are explicitly authorized by architect artifacts.
- verification matrix names targeted Week dev expand/collapse, Week prod inert/unchanged, and visual evidence requirements for the compact top-area.
- No `today-week` post-test command is introduced unless the architect explicitly changes the wave to `wave_final` and supplies canonical_flow_commands.

## Verification Profile
- backend: No backend runtime verification is expected for this blocker repair; backend changes remain out of scope.
- frontend: No frontend runtime verification is expected in this packet because no UI source files are authorized for implementation yet.
- observability: Artifact-level observability ownership must be made internally consistent; canonical Today/Week evidence is not authorized by the current architect wave.
- execution:
  - backend_commands:
  - frontend_commands:
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: False
  - requires_frontend_visual: False
  - artifact_globs:
    - /opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Reject if any required execution boundary remains `-`, empty, or `None`.
- Reject if the repaired scope authorizes backend, Day, payload, scoring, explainability, or broad product-surface changes.
- Reject if UI verification is not explicit for dev-expanded and prod-unchanged Week states.
- Reject if canonical Today/Week observability is added without architect-authorized canonical emitter commands.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W00-ARCHITECT-FORMALIZATION

## Notes
- This is a blocker packet graph because the architect manifest and slice docs do not currently provide executable impacted modules or write scope.
- The architect formalization says evidence ownership was shifted to packet_local, but the development-plan slice currently says observability_scope none; this must be resolved before implementation slicing.
- No coder implementation packet is emitted in this planner output because doing so would require guessing Week frontend file boundaries.
