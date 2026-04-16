# Architect Handoff: FEAT-DEV-RUNTIME-INDICATOR

- Slice ID: `SLICE-FEAT-DAY-DEV-INDICATOR`
- Slice dir: `/opt/astro-project/docs/expandable-day-screen-dev-indicator`
- Goal: Rerun the existing compact Day/home DEV chip diagnostics disclosure through bounded frontend verification and packet-local evidence without changing DayBrief contracts, backend traffic, or production behavior
- Scope: Reuse the existing Day/home dev/prod chip on `/` as the only runtime-disclosure entry point.; Keep the collapsed DEV chip visually compact and local to the Day hero area.; In non-production only, expand and collapse a local disclosure that shows render path, bootstrap result, and current mode from existing client state.; Re-run the targeted unit, Playwright, visual, and packet-local read-only observability lanes through the live pipeline.; Publish Prefect artifacts for the rerun wave so verifier, reviewer, and architect evidence is inspectable.
- Out of scope: Any backend change.; Any new payload field, scoring change, explainability change, or business-logic change.; Any new top-level banner, separate diagnostics screen, or Week or other-surface expansion.; Any diagnostics field beyond render path, bootstrap result, and current mode.; Any new slice definition separate from the existing Day dev-indicator slice.; Any canonical Today/Week closeout claim or runtime emitter ownership from this frontend-only helper wave.
- Impacted modules: M-FRONTEND-WEBAPP, M-FRONTEND-TODAY, M-USE-TELEGRAM
- Verification surfaces: Home-page unit coverage for toggle, collapse, fallback values, route gating, and production inertness.; Dedicated Playwright Day disclosure behavior on the active dev stack.; Dedicated visual evidence for dev-collapsed, dev-expanded, and prod-inert states.; Packet-local read-only post-test review for the touched flow.; Published Prefect packet artifacts for W01.
- Open decisions: -

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
