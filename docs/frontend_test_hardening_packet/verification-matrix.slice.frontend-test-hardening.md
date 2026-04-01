# Verification Matrix — Frontend Test Hardening

## Slice Metadata
- **Slice ID:** `FRONTEND-TEST-HARDENING`
- **Packet Date:** `2026-03-31`
- **Objective:** Reach and enforce `>=95%` line coverage for `frontend/app` + `frontend/components` + `frontend/lib`, with E2E excluded from the coverage numerator and denominator.
- **Primary Risk:** The repo currently has Playwright E2E coverage but no committed `Jest`/`Next` frontend unit/integration coverage runner for scoped source measurement.

## Controller-Owned Local Adaptation
- **Playwright role:** Canonical frontend E2E/live-interaction verifier for this project.
- **Jest/Next role:** Canonical frontend unit/integration and coverage runner for `frontend/app/**`, `frontend/components/**`, and `frontend/lib/**`.
- **Control rule:** Worker execution must preserve these roles unless the controller updates the packet.

## Metric Contract
- **Metric:** scoped frontend line coverage
- **Included source:** `frontend/app/**`, `frontend/components/**`, `frontend/lib/**`
- **Excluded source:** `frontend/e2e/**`, `**/*.spec.*`, `**/*.test.*`, `**/__tests__/**`, `**/__mocks__/**`, `**/__snapshots__/**`, `**/*.snap`, generated artifacts, coverage outputs, and framework build outputs
- **Pass threshold:** `>=95.00%` lines on the scoped source set
- **Important rule:** Playwright E2E does not count toward the coverage numerator because E2E files are excluded from the instrumented scope; scoped source coverage is owned by the Jest/Next runner.

## Verification Units
| VM ID | Purpose | Commands | Pass Signal | Notes |
|---|---|---|---|---|
| `VM-FTH-BASELINE` | Establish initial scoped coverage baseline and confirm include/exclude policy is active | `cd frontend && npm run test:coverage` | Command exits `0` and emits a scoped line coverage report for `app/components/lib` only | This VM is red until the Jest/Next coverage runner exists |
| `VM-FTH-TOOLING` | Prove the Jest/Next unit/integration harness is stable for scoped frontend source tests | `cd frontend && npm run test:coverage`; rerun once more | Two consecutive runs complete without config drift or ad-hoc manual setup | Use for Wave 2 completion |
| `VM-FTH-HIGH-VALUE` | Verify high-value source tests cover behavior-rich modules | `cd frontend && npm run test:coverage` | Per-file report shows shrinking uncovered hotspots in priority files and total scoped line coverage rises materially | Worker should attach before/after hotspot list |
| `VM-FTH-THRESHOLD` | Enforce fail-closed threshold behavior | `cd frontend && npm run test:coverage:threshold` | Command exits `0` at `>=95%` and exits non-zero below threshold | Threshold must target scoped lines, not global unrelated files |
| `VM-FTH-BACKEND-QUICK` | Preserve required project quick backend verification while frontend slice evolves | `docker exec astro-project-backend-1 python3 scripts/pipeline.py` | Canonical backend quick profile passes | Required by project AGENTS guidance after significant changes |
| `VM-FTH-FRONTEND-E2E-QUICK` | Ensure existing frontend quick path still works after test tooling/refactor changes | `./scripts/run_e2e.sh --last-failed` | Playwright quick profile passes or returns canonical no-last-failed success behavior | E2E is a regression guard, not part of the coverage metric |

## Acceptance Bundle
- `VM-FTH-THRESHOLD` passes with scoped line coverage `>=95.00%`
- `VM-FTH-BACKEND-QUICK` passes
- `VM-FTH-FRONTEND-E2E-QUICK` passes
- The committed coverage config explicitly excludes generated files, test files, E2E files, and snapshots
- The packet docs and package scripts match the implemented command names

## Failure Triage
- If coverage includes `frontend/e2e`, fix config before adding more tests
- If coverage includes snapshots, test fixtures, or generated artifacts, fix exclusions before trusting the reported percentage
- If large `frontend/app/admin/**` pages block progress, extract pure helpers and cover those first
- If a refactor breaks user flows, restore green on `./scripts/run_e2e.sh --last-failed` before proceeding
