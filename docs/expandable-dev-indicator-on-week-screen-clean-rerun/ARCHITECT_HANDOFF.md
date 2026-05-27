# Architect Handoff: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN

- Slice ID: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-RERUN`
- Slice dir: `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean-rerun`
- Goal: Rerun the already-approved Week dev indicator helper slice as a local dev-only runtime diagnostics disclosure without widening scope and without forcing invalid canonical observability ownership.
- Scope: Keep the existing Week dev/prod chip visually compact.; In dev mode only, tapping the chip expands a lightweight local diagnostics block.; Show only render path, bootstrap result, and current mode from existing runtime/debug state.; Keep the diagnostics block local to the chip area with minimal layout shift.; Use packet-local frontend verification and visual evidence for dev-expanded and prod-unchanged Week states.
- Out of scope: No backend changes.; No new payload fields.; No new top-level debug banner or separate diagnostics screen.; No correlation, trace, or payload diagnostics in user-facing UI.; No changes to Day screen or other product surfaces.; No canonical today-week closeout ownership in this rerun wave.
- Impacted modules: M-FRONTEND-WEBAPP, M-FRONTEND-WEEK, M-USE-TELEGRAM
- Verification surfaces: Week unit coverage for route gating, render-path labels, fallback values, and production inertness.; Dedicated Playwright Week disclosure behavior in the active dev stack.; Dedicated visual captures for dev-collapsed, dev-expanded, and prod-unchanged Week states.; Packet-local read-only post-test review plus week-runtime-indicator-observability.json identifiers.
- Open decisions: -

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
