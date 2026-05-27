# Architect Handoff: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2

- Slice ID: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`
- Slice dir: `/opt/astro-project/docs/expandable-week-runtime-indicator-rerun-2`
- Goal: Rerun the already-canonical Week runtime indicator slice through the live GRACE pipeline after pipeline and reviewer-routing fixes, without widening product scope.
- Scope: Reuse the existing shell DEV/PROD chip on /week as the only runtime-disclosure entry point.; Keep the collapsed Week chip visually compact and local to the chip area.; In non-production on /week, tapping the chip expands and collapses a small local disclosure showing Week render path, Telegram bootstrap result, and current runtime mode from existing frontend state.; Collect targeted unit, Playwright, visual, reviewer, and observability evidence for the rerun.
- Out of scope: Backend changes.; New payload fields, WeekBrief contract changes, scoring changes, explainability changes, or business-logic changes.; Day screen changes or multi-surface redesign.; New top-level debug banners, separate diagnostics screens, or user-visible correlation, trace, or payload diagnostics.
- Impacted modules: M-FRONTEND-WEBAPP, M-FRONTEND-WEEK, M-USE-TELEGRAM
- Verification surfaces: Week unit coverage for route gating, render-path labels, fallback values, and production inertness.; Dedicated Playwright Week disclosure behavior in the active dev stack.; Dedicated visual captures for dev-collapsed, dev-expanded, and prod-unchanged Week states.; Post-test observability review for FLOW-TODAY-WEEK-WEEK with an explicit verdict.
- Open decisions: -

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
