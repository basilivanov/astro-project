# Architect Handoff: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN

- Slice ID: `SLICE-FEAT-WEEK-RUNTIME-INDICATOR-CLEAN`
- Slice dir: `/opt/astro-project/docs/expandable-dev-indicator-on-week-screen-clean`
- Goal: Keep the existing Week runtime disclosure bounded to the current frontend helper surface and verify it through packet-local evidence without claiming canonical Today/Week ownership.
- Scope: Reuse the existing Week dev/prod chip as the only Week runtime-disclosure entry point.; Keep the collapsed chip visually compact and local to the chip area.; In non-production on /week, expand and collapse a lightweight disclosure that shows render path, bootstrap result, and current mode from existing page/runtime state.; Reuse the current Week render-path helper values already exposed by frontend/app/week/page.tsx.; Close the helper slice with targeted frontend verification, visual proof, and packet-local read-only observability only.
- Out of scope: Backend changes.; New payload fields, scoring changes, explainability changes, or business-logic changes.; New top-level banners, separate diagnostics screens, or user-facing correlation/trace/payload diagnostics.; Day screen changes or broader multi-surface badge redesign.; Canonical Today/Week closeout for this wave.
- Impacted modules: M-FRONTEND-WEBAPP, M-FRONTEND-WEEK, M-USE-TELEGRAM
- Verification surfaces: Week unit coverage for route gating, render-path labels, fallback values, and production inertness.; Dedicated Playwright Week disclosure behavior in the active dev stack.; Dedicated visual captures for dev-collapsed, dev-expanded, and prod-unchanged Week states.; Packet-local read-only post-test review plus `week-runtime-indicator-observability.json` identifiers.
- Evidence ownership: W01 is `packet_local` only. It may use `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`, but it must not claim canonical Today/Week ownership or add canonical flow commands.
- Open decisions: None. Existing code resolves render path in frontend/app/week/page.tsx and bootstrap/mode through useTelegram.

Planner must treat the slice docs in this directory as the source of truth for packet decomposition.
