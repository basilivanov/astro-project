# Architect Handoff: FEAT-DEV-RUNTIME-INDICATOR

- Slice ID: `SLICE-FEAT-DAY-DEV-INDICATOR`
- Slice dir: `/opt/astro-project/docs/expandable-day-screen-dev-indicator`
- Goal: Reuse the existing compact Day/home DEV chip as a dev-only runtime diagnostics disclosure without changing DayBrief contracts, backend traffic, or production behavior.
- Scope: Keep the existing Day/home dev/prod chip visually compact.; In dev mode only on `/`, tapping the chip expands a lightweight local diagnostics block.; Show only render path, bootstrap result, and current mode from existing runtime/debug state.; Keep the diagnostics block local to the chip area with minimal layout shift.; Add targeted frontend verification and visual evidence for dev-expanded and prod-unchanged states.
- Out of scope: No backend changes.; No new payload fields.; No new top-level debug banner or separate diagnostics screen.; No correlation, trace, or payload diagnostics in user-facing UI.; No changes to Week screen or other product surfaces.
- Impacted modules: M-FRONTEND-WEBAPP, M-FRONTEND-TODAY, M-USE-TELEGRAM
- Verification surfaces: Home-page unit coverage for non-production toggle, collapse, fallback values, and production-inert behavior; Dedicated Playwright Day disclosure coverage on the active dev stack; Collapsed, expanded, and prod-inert visual evidence; Today post-test observability review with explicit verdict
- Open decisions: Escalate if the shell-owned badge cannot stay route-gated to `/` without leaking interactive behavior into other routes.; If no dedicated production host is available to Playwright, production-unchanged proof remains deterministic unit coverage plus any optional `E2E_PROD_BASE_URL` run.

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
