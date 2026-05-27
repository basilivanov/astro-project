# Feature Brief: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2

## Business Intent
Rerun the Week-screen dev runtime indicator feature through the live GRACE pipeline after pipeline and reviewer-routing fixes.

## Desired Outcome
Expandable dev indicator on Week screen rerun 2

## In Scope
- Keep the existing Week dev/prod chip visually compact.
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
1. W00 architect + planner formalization for a bounded Week-screen slice
2. W01 frontend implementation + verifier evidence + reviewer gate + architect wave gate

## Open Decisions
- Confirm exact existing runtime/debug source fields for render path and bootstrap result on Week.
- Confirm whether existing week Playwright coverage already has a stable selector around the runtime badge.
