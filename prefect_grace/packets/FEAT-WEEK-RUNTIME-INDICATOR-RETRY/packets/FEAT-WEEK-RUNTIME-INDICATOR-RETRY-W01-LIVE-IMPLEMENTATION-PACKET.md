# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-LIVE-IMPLEMENTATION-PACKET

## Summary
Scope: Keep the existing Week-screen dev/prod chip visually compact.; In dev mode only, tapping the chip expands a lightweight local diagnostics block.; Show only render path, bootstrap result, and current mode from existing runtime/debug state.; Keep the diagnostics block local to the chip area with minimal layout shift.; Add targeted frontend verification and visual evidence for dev-expanded and prod-unchanged states on Week.. Acceptance: In dev mode on Week, tapping the current dev indicator expands a compact diagnostics block.; The diagnostics block shows render path, bootstrap result, and current mode.; Tapping the dev indicator again collapses the diagnostics block.; In prod mode, the indicator remains inert and the visible UI stays unchanged.; No backend payload, scoring, explainability, or business-logic changes are introduced.; Visual evidence shows the Week top area remains clean and not banner-like.. Non-goals: No backend changes.; No new payload fields.; No new top-level debug banner or separate diagnostics screen.; No correlation, trace, or payload diagnostics in user-facing UI.; No changes to Day screen or other product surfaces.. Visual expectations: Dev chip remains compact in collapsed state.; Expanded diagnostics appear as a small local disclosure near the existing chip.; Expanded diagnostics do not visually dominate or noticeably shift the Week hero/top-area.; Prod mode remains visually unchanged..

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only files required by the packet.
- Bounded implementation/refactor required by the feature brief.

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W00-PLANNER-SLICING
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W00-ARCHITECT-FORMALIZATION
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
- workdir: /opt/astro-project

## Reviewer Gate
- Packet scope respected.
- Verification handoff notes included.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W00-PLANNER-SLICING

## Notes
- Prefer root-cause fixes.
- Strengthen logs if the packet touches runtime flow.
