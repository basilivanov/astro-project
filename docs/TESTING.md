# TESTING

`docs/TESTING.md` is the agent-first home for how this repo verifies changes.

Use this document first. It keeps the durable rules short, points to the canonical command map, and leaves slice-specific execution packets near the slices they govern.

## Start here

1. Read `AGENTS.md` for the required test protocol.
2. Use `docs/REGRESSION_MAP.md` for the canonical regression profiles, verification commands, and durable coverage map.
3. Use packet-local docs for slice-specific checks, for example `docs/*packet/verification-matrix*.md`.

## Agent-first testing rules

- Verify to green for the smallest profile that honestly covers the changed surface.
- Backend changes must run `backend:quick` at minimum.
- Frontend changes must run `frontend:quick` at minimum.
- Green tests are necessary but not sufficient: after the chosen profile passes, review post-test `digest/replay/trace` evidence for the affected flow before calling verification complete.
- For `Today`, `Week`, `Admin`, `Catalog`, and `Billing` affected work, post-test observability review is mandatory even when tests and UI checks are green.
- Record an explicit observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.
- If a build, route, or page crashes, first add or update a reproducing test, then fix, then rerun until pass.
- Full regression is not required after every small change, but the chosen profile must match the task scope.

## Canonical profiles

The canonical profile definitions live in `docs/REGRESSION_MAP.md`.

- `backend:quick` — required for meaningful backend changes
- `frontend:quick` — required for meaningful frontend changes
- `frontend:targeted` — use for scoped Playwright verification
- `smoke` — use before high-confidence handoff
- `full-regression` — use before release/deploy/large merge
- `llm-matrix` — expensive benchmark path, not routine task verification

## Where details live

- `docs/REGRESSION_MAP.md` — single durable regression map
- `verification-matrix.md` — legacy root matrix retained as a pointer and snapshot-specific companion
- `docs/GRACE_TEST_PLAYBOOK.md` — legacy playbook retained for historical context
- `docs/TESTING_GUIDE.md` — legacy narrow guide retained for specific DayBrief notes

## Non-goals for this page

This page does not duplicate every packet-level matrix, benchmark manifest, or one-off audit. Those remain close to the slice that owns them.
