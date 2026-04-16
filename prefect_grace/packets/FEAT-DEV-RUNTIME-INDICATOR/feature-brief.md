# Feature Brief: FEAT-DEV-RUNTIME-INDICATOR

## Business Intent
Rerun the existing compact dev/prod chip on the Day screen as a bounded dev-only runtime diagnostics helper and close the slice with packet-local frontend evidence only.

## Desired Outcome
Expandable dev indicator on Day screen packet-local rerun

## In Scope
- Formalize the feature into GRACE artifacts.
- Slice the feature into bounded execution packets.
- Prepare implementation, verification, and review flow.

## Out of Scope
- Full production rollout of the feature.
- Unbounded refactors outside the packet scopes.

## Impacted Surfaces
- frontend: the existing Day dev runtime indicator slice only.
- automation: Prefect packet orchestration only if the feature explicitly asks to validate pipeline behavior.
- observability: packet-local read-only evidence only; this frontend-only helper wave does not own canonical Today/Week runtime emission.

## Impacted GRACE Artifacts
- requirements.xml: only if the business scope/invariants change.
- technology.xml: only if the runtime/tooling contract changes.
- development-plan.xml: only if execution topology or packet model changes.
- knowledge-graph.xml: only if module/slice links change.
- verification-matrix.md: only if verification gates or evidence rules change.

## Acceptance Criteria
- Reuse the existing Day/home dev/prod chip on `/` as the only runtime-disclosure entry point.
- Keep the collapsed DEV chip visually compact and local to the Day hero area.
- In non-production only, expand and collapse a local disclosure that shows render path, bootstrap result, and current mode from existing client state.
- Re-run targeted unit, Playwright, visual, and packet-local read-only observability lanes.
- Publish Prefect artifacts for coder, verifier, reviewer, and architect packets.

## Visual Expectations
- The compact chip stays visually subordinate to the Day hero and does not become a banner.
- Expanded disclosure remains local to the chip area and shows only render path, bootstrap result, and current mode.
- Production and non-home routes stay visually unchanged and inert.

## Wave Proposal
1. W00 architect formalization updates the existing Day slice docs and packet graph.
2. W01 executes directly from the bounded coder packet; planner is not required for this rerun.
3. Verifier, reviewer, and architect consume packet-local evidence and published artifacts to close the wave.

## Open Decisions
- None.
