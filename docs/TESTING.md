# TESTING

`docs/TESTING.md` is the agent-first home for how this repo verifies changes.

Use this document first. It keeps the durable rules short, points to the canonical command map, and leaves slice-specific execution packets near the slices they govern.

## Start here

1. Read `AGENTS.md` for the required test protocol.
2. Use `docs/REGRESSION_MAP.md` for the canonical regression profiles, verification commands, and durable coverage map.
3. Use packet-local docs for slice-specific checks, for example `docs/*packet/verification-matrix*.md`.
4. If the work falls into an active bounded slice, prefer that slice packet or plan before widening to general docs.

## Agent-first testing rules

- Verify to green for the smallest profile that honestly covers the changed surface.
- Backend changes must run `backend:quick` at minimum.
- Frontend changes must run `frontend:quick` at minimum.
- Green tests are necessary but not sufficient: after the chosen profile passes, review post-test `digest/replay/trace` evidence for the affected flow before calling verification complete.
- For `Today`, `Week`, `Admin`, `Catalog`, and `Billing` affected work, post-test observability review is mandatory even when tests and UI checks are green.
- Record an explicit observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.
- If a build, route, or page crashes, first add or update a reproducing test, then fix, then rerun until pass.
- Full regression is not required after every small change, but the chosen profile must match the task scope.
- Host-side observability helpers are expected to read canonical repo sinks under `logs/*.jsonl`; in dev Docker, keep backend UID/GID aligned with the host user so the container writes there instead of falling back to `/tmp/astro-project/logs`.

## Canonical profiles

The canonical profile definitions live in `docs/REGRESSION_MAP.md`.

- `backend:quick` — required for meaningful backend changes
- `frontend:quick` — required for meaningful frontend changes
- `frontend:targeted` — use for scoped Playwright verification
- `frontend:signed-auth` — prove authenticated consumer behavior in canonical Telegram lane
- `frontend:guest-lane` — prove public entry semantics without authenticated guarantees
- `frontend:mock-harness` — deterministic fallback/harness checks only, not canonical auth proof
- `smoke` — use before high-confidence handoff
- `full-regression` — use before release/deploy/large merge
- `llm-matrix` — expensive benchmark path, not routine task verification

## Auth lane profiles

### `frontend:signed-auth`

Use when a change touches authenticated consumer behavior, Telegram runtime detection, auth headers, or personalized Today/Week/Profile surfaces.

This is the only canonical authenticated proof lane for MVP consumer routes.
The suite must prove signed Telegram WebApp initData on `Today`, `Week`, `Profile`, and onboarding/profile flows without mock runtime.

```bash
./scripts/run_e2e.sh e2e/telegram-signed-auth.spec.ts
```

### `frontend:guest-lane`

Use when a change touches landing/start/public entry semantics.

`e2e/core-ux.spec.ts` is guest/public shell proof only. It is not an authenticated consumer proof file.

```bash
./scripts/run_e2e.sh e2e/core-ux.spec.ts
```

### `frontend:mock-harness`

Use only for deterministic fixture regressions and fallback harness checks.

This profile does not prove production-authenticated behavior.
Preferred examples: `e2e/week-page-fallback.spec.ts`, `e2e/week-fallback.regression.spec.ts`.

## Where details live

- `docs/REGRESSION_MAP.md` — single durable regression map
- `docs/TODAY_WEEK_DETAIL_LAYER_REFACTOR_PLAN.md` — active Day/Week detail-layer slice plan
- `docs/day_week_contract_audit_v2_2026-04-02.md` — precise Day score-disclosure contract and Week day-card detail-system audit for the current v2 wave
- `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md` — observability gate memo and verdict model
- `docs/frontend_functional_reliability_packet/verification-matrix.slice.frontend-functional-reliability.md` — frontend structural remediation functional packet
- `docs/frontend_test_hardening_packet/verification-matrix.slice.frontend-test-hardening.md` — frontend structural remediation hardening packet
- `verification-matrix.md` — legacy root matrix retained as a pointer and snapshot-specific companion
- `docs/GRACE_TEST_PLAYBOOK.md` — legacy playbook retained for historical context
- `docs/TESTING_GUIDE.md` — legacy narrow guide retained for specific DayBrief notes

## Non-goals for this page

This page does not duplicate every packet-level matrix, benchmark manifest, or one-off audit. Those remain close to the slice that owns them.
