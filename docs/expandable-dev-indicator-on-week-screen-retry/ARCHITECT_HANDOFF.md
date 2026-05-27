# Architect Handoff: FEAT-WEEK-RUNTIME-INDICATOR-RETRY

- Slice ID: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-RETRY`
- Slice dir: `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-retry`
- Goal: Retry the Week runtime indicator live pipeline with rework-loop guard and pipeline-resume safety.
- Scope: Keep the existing Week-screen dev/prod chip visually compact.; In dev mode only, tapping the chip expands a lightweight local diagnostics block.; Show only render path, bootstrap result, and current mode from existing runtime/debug state.; Keep the diagnostics block local to the chip area with minimal layout shift.; Add targeted frontend verification and visual evidence for dev-expanded and prod-unchanged states on Week.
- Out of scope: No backend changes.; No new payload fields.; No new top-level debug banner or separate diagnostics screen.; No correlation, trace, or payload diagnostics in user-facing UI.; No changes to Day screen or other product surfaces.
- Impacted modules: -
- Verification surfaces: See verification matrix slice.
- Open decisions: Confirm exact existing runtime/debug source fields for render path and bootstrap result on Week.; Confirm whether current week Playwright coverage already exposes a stable hook around the runtime badge.

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
