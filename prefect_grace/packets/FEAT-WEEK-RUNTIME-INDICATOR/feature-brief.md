# Feature Brief: FEAT-WEEK-RUNTIME-INDICATOR

## Business Intent
Turn the existing compact dev/prod chip into a dev-only entry point for lightweight runtime diagnostics on the Week screen without changing product content, backend payloads, scoring, or prod behavior.

## Desired Outcome
Expandable dev indicator on Week screen

## In Scope
- Keep the existing Week-screen dev/prod chip visually compact.
- In dev mode only, tapping the chip expands a lightweight local diagnostics block.
- Show only render path, bootstrap result, and current mode from existing runtime/debug state.
- Keep the diagnostics block local to the chip area with minimal layout shift.
- Add targeted frontend verification and visual evidence for dev-expanded and prod-unchanged states on Week.

## Out of Scope
- No backend changes.
- No new payload fields.
- No new top-level debug banner or separate diagnostics screen.
- No correlation, trace, or payload diagnostics in user-facing UI.
- No changes to Day screen or other product surfaces.

## Impacted Surfaces
- frontend
- observability
- grace

## Impacted GRACE Artifacts
- verification-matrix.md
- knowledge-graph.xml
- development-plan.xml
- requirements.xml
- technology.xml

## Acceptance Criteria
- In dev mode on Week, tapping the current dev indicator expands a compact diagnostics block.
- The diagnostics block shows render path, bootstrap result, and current mode.
- Tapping the dev indicator again collapses the diagnostics block.
- In prod mode, the indicator remains inert and the visible UI stays unchanged.
- No backend payload, scoring, explainability, or business-logic changes are introduced.
- Visual evidence shows the Week top area remains clean and not banner-like.

## Visual Expectations
- Dev chip remains compact in collapsed state.
- Expanded diagnostics appear as a small local disclosure near the existing chip.
- Expanded diagnostics do not visually dominate or noticeably shift the Week hero/top-area.
- Prod mode remains visually unchanged.

## Wave Proposal
1. W00 architect + planner formalization for bounded Week-screen slice
2. W01 frontend implementation + verifier evidence + reviewer gate + architect wave gate

## Open Decisions
- Confirm exact existing runtime/debug source fields for render path and bootstrap result on Week.
- Confirm whether current week Playwright coverage already exposes a stable hook around the runtime badge.
