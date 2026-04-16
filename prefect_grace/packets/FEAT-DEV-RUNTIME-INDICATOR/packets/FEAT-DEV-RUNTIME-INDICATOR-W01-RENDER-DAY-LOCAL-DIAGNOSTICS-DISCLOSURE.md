# Packet: FEAT-DEV-RUNTIME-INDICATOR-W01-RENDER-DAY-LOCAL-DIAGNOSTICS-DISCLOSURE

## Summary
Implement the Day-local disclosure body and supporting unit coverage using only existing render path, bootstrap result, and mode state with stable fallbacks.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/frontend/app/page.tsx
- /opt/astro-project/frontend/components/today/*
- /opt/astro-project/frontend/hooks/useTelegram.ts
- /opt/astro-project/frontend/lib/telegram-runtime.ts
- /opt/astro-project/frontend/test/app/home-page.test.tsx

## Inputs
- FEAT-DEV-RUNTIME-INDICATOR-W01-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/architect_manifest.json
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/verification-matrix.slice.expandable-day-screen-dev-indicator.md
- /opt/astro-project/docs/expandable-day-screen-dev-indicator/knowledge-graph.slice.expandable-day-screen-dev-indicator.xml

## Acceptance Criteria
- On `/` in non-production, tapping the existing chip expands and collapses a local disclosure near the chip area.
- The visible disclosure body shows only render path, bootstrap result, and current mode.
- Missing diagnostics values render stable unknown or unavailable fallbacks instead of blocking or crashing the Day screen.
- DayBrief hero content, CTA, readiness, scoring, backend payloads, and production behavior remain unchanged.

## Verification Profile
- backend: {'required_commands': [], 'evidence': ['No backend diff is permitted.'], 'verdict_expectation': 'not_required'}
- frontend: {'required_commands': ['corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx'], 'visual_verification': {'status': 'deferred_to_FEAT-DEV-RUNTIME-INDICATOR-W01-DAY-PLAYWRIGHT-VISUAL-COVERAGE', 'artifacts': ['Dev-collapsed and dev-expanded disclosure screenshots must be captured later.', 'Prod-unchanged proof must be captured later or explicitly substituted per architect handoff.']}, 'evidence': ['Unit coverage must prove non-production `/` toggle and collapse behavior.', 'Unit coverage must prove production inertness and stable fallback values when runtime state is absent.'], 'verdict_expectation': 'pass'}
- observability: {'required_commands': [], 'evidence': ['Today observability review is deferred to FEAT-DEV-RUNTIME-INDICATOR-W01-VERIFIER-EVIDENCE after targeted frontend verification.'], 'verdict_expectation': 'deferred'}

## Execution Hints
- workdir: /tmp/prefect_grace_feature_workdir
- sandbox: danger-full-access

## Reviewer Gate
- Diff stays within the Day disclosure scope and supporting runtime helper reads; no Week or backend files are touched.
- The disclosure content is limited to the three approved fields and does not expose trace, payload, or correlation diagnostics.
- Jest evidence covers expand, collapse, fallback, and production-inert branches and leaves Playwright capture deterministic.

## Dependencies
- FEAT-DEV-RUNTIME-INDICATOR-W01-ROUTE-GATE-SHELL-BADGE-ON-DAY-ONLY

## Notes
- Prefer consuming existing runtime/debug state; any new contract or payload field is out of scope.
- Keep layout shift local and non-banner-like.
