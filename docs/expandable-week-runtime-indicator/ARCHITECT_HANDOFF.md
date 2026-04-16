# Architect Handoff: FEAT-WEEK-RUNTIME-INDICATOR

- Slice ID: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR`
- Slice dir: `/opt/astro-project/docs/expandable-week-runtime-indicator`
- Goal: Reuse the existing compact Week DEV chip as a dev-only runtime diagnostics disclosure without changing Week content, backend payloads, scoring, or production behavior.
- Scope: Reuse the existing shell DEV/PROD chip on /week as the only runtime-disclosure entry point.; Keep the collapsed chip visually compact and local to the chip area.; In non-production on /week, expand and collapse a local disclosure that shows Week render path, bootstrap result, and current mode from existing page and runtime state.; Derive Week render-path labels from existing Week page states only: loading, auth_gate, empty, in_progress, error, canonical.; Add targeted unit, Playwright, visual, and packet-local read-only evidence for the dev-expanded and prod-unchanged Week states.
- Out of scope: Any backend change.; Any new payload field, scoring change, Week explainability change, or business-logic change.; Any Day or multi-surface redesign.; Any new top-level banner or separate diagnostics screen.; Any diagnostics field beyond render path, bootstrap result, and current mode.
- Impacted modules: M-FRONTEND-WEBAPP, M-FRONTEND-WEEK, M-USE-TELEGRAM
- Verification surfaces: Week-page unit coverage for route gating, render-path labels, fallback values, and production inertness.; Dedicated Playwright Week disclosure behavior in the active dev stack.; Dedicated visual evidence for dev-collapsed, dev-expanded, and prod-unchanged Week states.; Packet-local read-only post-test review plus the local observability artifact identifiers.
- Open decisions: -

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
