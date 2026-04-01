# Frontend Test Hardening Execution Packet

## Mission
- **Metric:** `>=95.00%` line coverage
- **Scope:** `frontend/app/**` + `frontend/components/**` + `frontend/lib/**`
- **Exclusion rule:** generated files, test files, E2E files, and snapshots are excluded from both numerator and denominator
- **Non-goal:** E2E coverage does not count toward this metric; Playwright remains a separate regression verifier

## Controller-Owned Local Adaptation
- **Local adaptation:** For this project, `Playwright` is the canonical frontend E2E/live-interaction verifier.
- **Local adaptation:** For this project, `Jest` with `Next`-compatible frontend setup is the canonical frontend unit/integration and coverage runner for `frontend/app/**`, `frontend/components/**`, and `frontend/lib/**`.
- **Controller rule:** Worker proposals that replace either canonical role require explicit controller approval; this packet does not authorize switching the unit/integration runner to `Vitest`.

## Current Repo Baseline
- Frontend E2E is already established through `frontend/playwright.config.cjs` and `./scripts/run_e2e.sh`
- `frontend/package.json` currently exposes Playwright test scripts; this packet records `Jest`/`Next` as the canonical unit/integration and coverage target to add or align
- No committed unit/integration coverage runner is currently defined for the scoped frontend source

## Exact Metric Definition
```text
scoped_line_coverage =
  covered executable lines in included files under frontend/app + frontend/components + frontend/lib
  divided by
  all executable lines in included files under frontend/app + frontend/components + frontend/lib
  multiplied by 100
```
Pass condition: `scoped_line_coverage >= 95.00`

## Scope Rules
### Included
- `frontend/app/**`
- `frontend/components/**`
- `frontend/lib/**`

### Excluded
- generated files
- `frontend/e2e/**`
- `**/*.spec.*`
- `**/*.test.*`
- `**/__tests__/**`
- `**/__mocks__/**`
- `**/__snapshots__/**`
- `**/*.snap`
- build/output artifacts such as `.next`, coverage outputs, Playwright reports, and `node_modules`

## Waves
### Wave 1 — Audit / Baseline
- inventory scoped files
- add/select coverage runner
- produce first scoped coverage report
- rank hotspots by uncovered lines

### Wave 2 — Tool Stabilization
- add test dependencies and scripts in `frontend/package.json`
- add committed `Jest`/`Next` coverage config with explicit include/exclude rules
- add stable DOM/render/mock setup as needed
- prove repeatable local execution

### Wave 3 — High-Value Tests
- prioritize `frontend/lib/**` pure helpers
- cover shared components and renderers with deterministic props/state
- cover analytics and catalog helpers
- extract pure page helpers only when needed for deterministic tests

### Wave 4 — Threshold Enforcement
- set scoped line threshold to `95%`
- ensure threshold command exits non-zero below target
- ensure excluded file classes do not leak into denominator

### Wave 5 — Docs / Handoff
- record final scoped percentage
- record accepted exclusions discovered during setup
- keep packet docs aligned with final scripts/config

## Write Scope
- `frontend/package.json`
- `frontend/package-lock.json`
- coverage/test config files in `frontend/`
- `frontend/test/**`, `frontend/tests/**`, `frontend/__tests__/**`
- scoped source files under `frontend/app/**`, `frontend/components/**`, `frontend/lib/**` when required for testability or defects exposed by tests
- `docs/frontend_test_hardening_packet/**`

## Frozen Scope
- `backend/**`
- `frontend/e2e/**` except minimal compatibility adjustments if harmless refactors force them
- `scripts/run_e2e.sh`
- unrelated redesign or runtime/backend work

## Verification Commands
```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
cd frontend && npm run test:coverage
cd frontend && npm run test:coverage:threshold
./scripts/run_e2e.sh --last-failed
```

Command roles for this slice:
- `./scripts/run_e2e.sh*` = canonical Playwright frontend E2E/live-interaction verification
- `cd frontend && npm run test:coverage*` = canonical Jest/Next frontend unit/integration and coverage verification

## Acceptance Criteria
- A committed `Jest`/`Next` frontend unit/integration coverage runner exists
- It measures scoped line coverage for `frontend/app + frontend/components + frontend/lib`
- Generated files are excluded
- Test files are excluded
- E2E files are excluded
- Snapshots are excluded
- Scoped line coverage is `>=95.00%`
- Threshold enforcement is committed and exits non-zero below target
- Backend quick remains green
- Frontend E2E quick remains green

## Worker Handoff Checklist
- [ ] Coverage config includes only `frontend/app`, `frontend/components`, `frontend/lib`
- [ ] Coverage config excludes generated files, tests, E2E, and snapshots
- [ ] `npm run test:coverage` works from `frontend/`
- [ ] `npm run test:coverage:threshold` enforces `>=95%` lines
- [ ] Final scoped percentage is recorded
- [ ] `docker exec astro-project-backend-1 python3 scripts/pipeline.py` passes
- [ ] `./scripts/run_e2e.sh --last-failed` passes
