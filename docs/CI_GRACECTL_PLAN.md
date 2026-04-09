# GRACECTL CI Integration Plan

Plan compiled from `docs/gracectl.md`, `docs/GRACE_ARTIFACTS.md`,
`docs/GRACE_SLICE_AUTOMATION_MAP.md`, and the current `gracectl.yaml`. It
describes how to call `gracectl env/slice/watch/demo` inside CI for both pull
requests and scheduled jobs, where to store artifacts, and how to reason about
PASS/FAIL.

## Common Execution Contracts

### Command templates
- **Environment gate**: `gracectl env check --profile ci --json` must be the
  first CI step. It validates docker containers, repo paths, and config before
  any slice-specific checks. Non-zero exit status or a summary status other
  than PASS stops the workflow.
- **Slice verification**: `gracectl slice verify <SLICE> --backend --frontend --json`
  runs the backend + frontend bundles declared in `gracectl.yaml`. Use
  `--lint` when a slice introduces static checks and `--plan-only` for dry runs
  in presubmit experiments.
- **Replay sweeps**: `gracectl slice replay <SLICE> [--flow <name>] --json`
  executes the log/benchmark scripts listed under `commands.replay`. Needed for
  slices whose gates demand log evidence (e.g., Natal benchmark reruns).
- **Watchers**: `gracectl watch run <SLICE> --json` shells into the watcher
  commands defined in YAML (`feed_admin_watch`, `forecast_catalog_watch`, ...)
  and returns FAIL if any watcher exits non-zero.
- **Demos**: `gracectl demo run <SLICE> --backend --frontend --replay --json`
  chains `env check → slice verify → slice replay` for nightly smoke coverage.

### Reporting & failure packets
- Every invocation appends to `test-results/grace-report.json` (JSONL). Use
  `artifacts: upload` or an equivalent CI step to persist this file per job.
- Streaming logs land in `logs/gracectl/<SLICE>/<command>*.log`. Preserve the
  whole directory on failure for debugging.
- When a check fails, `gracectl` archives a failure packet under
  `test-results/failures/<slice>-<timestamp>/`. CI must always collect these
  packets and expose them as downloadable artifacts. They include
  `failure.json`, `stdout.log`, `stderr.log`, and any replay attachments.

### PASS/FAIL rules
- **PASS**: CLI exit status `0` *and* `summary.status == "passed"` inside the
  corresponding grace-report entry.
- **FAIL**: non-zero exit and/or `summary.status == "failed"` / `"errored"`.
  Jobs must propagate this status to block merges. Warnings (e.g., missing
  optional docs) may mark `summary.status == "passed"` with warnings and do
  not fail unless explicitly configured via `--strict` later.

## Pull Request Profile

### Shared order of operations
1. `gracectl env check --profile ci --json` (required for every PR pipeline).
2. Run `gracectl slice verify ...` for each affected slice (see below). Slices
   can be selected via path filters, but each run is isolated so artifacts and
   failure packets stay scoped.
3. Upload `test-results/grace-report.json`, the `logs/gracectl/` subtree, and
   any `test-results/failures/` folders.

### Slice-specific playbooks

#### `FEED-PERSONALIZED-DAILY`
- Command: `gracectl slice verify FEED-PERSONALIZED-DAILY --backend --frontend --json`.
- Backend coverage: `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
  plus the targeted pytest trio (`tests/test_daily_feed_robustness.py`,
  `tests/test_personalized_daily_service.py`, `tests/verify_daily_feed.py`).
- Frontend coverage: `./scripts/run_e2e.sh e2e/core-ux.spec.ts` inside the
  frontend container with `E2E_BASE_URL`/`FRONTEND_HEALTH_CONTAINER` exported.
- PASS requires both backend bundle and Playwright run to succeed. On failure,
  CI uploads the packet generated under
  `test-results/failures/FEED-PERSONALIZED-DAILY-*.tar.gz`.
- Optional replay (for regression-proof PRs touching feed logging):
  `gracectl slice replay FEED-PERSONALIZED-DAILY --flow feed --limit 200 --json`.

#### `ADMIN-ENTITLEMENTS-FLOW`
- Command: `gracectl slice verify ADMIN-ENTITLEMENTS-FLOW --backend --frontend --json`.
- Backend coverage: baseline pipeline plus entitlements pytest pack
  (`tests/test_entitlements.py`, `tests/test_entitlements_unit.py`,
  `tests/test_one_off_entitlements_scaffold.py`, and
  `tests/test_admin_grant_one_off_alignment.py`).
- Frontend coverage: `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/admin.entitlements.spec.ts`.
- PASS requires zero failing checks; any admin Playwright drift blocks the PR.
- Optional replay: `gracectl slice replay ADMIN-ENTITLEMENTS-FLOW --flow admin --json`
  (wraps `tools/admin_logs/replay_last.py`).

#### `FORECAST-LADDER-CATALOG-FLIP`
- Command: `gracectl slice verify FORECAST-LADDER-CATALOG-FLIP --backend --frontend --json`.
- Backend coverage: pipeline + billing/entitlement pytest bundle (`tests/test_billing_checkout_sessions.py`,
  `tests/test_billing_checkout_resume.py`, `tests/test_one_off_access_runtime.py`,
  `tests/test_one_off_entitlements_scaffold.py`,
  `tests/test_legacy_workflow_one_off_alignment.py`,
  `tests/test_report_contract.py`, `tests/test_one_off_runtime_smoke.py`,
  `tests/test_admin_grant_one_off_alignment.py`).
- Frontend coverage: storefront/history/create suites (`e2e/billing-catalog-alignment.spec.ts`,
  `e2e/history-cta.spec.ts`, `e2e/report-create.spec.ts`,
  `e2e/report-failure.spec.ts`, `e2e/month-forecast-bridge-storefront.spec.ts`,
  `e2e/year-forecast-bridge-storefront.spec.ts`,
  `e2e/solar-return-bridge-storefront.spec.ts`,
  `e2e/synastry-bridge-storefront.spec.ts`, plus the billing-mock case with
  `E2E_ENABLE_ONE_OFF_RUNTIME=1`).
- PASS requires all storefront specs to stay green; upload catalog watch logs
  on failure for faster triage.
- Optional replay: `gracectl slice replay FORECAST-LADDER-CATALOG-FLIP --flow catalog --json`
  (invokes `forecast_catalog_watch.py` in replay mode).

#### `M-NATAL-SUMMARY-LAYER`
- Command: `gracectl slice verify M-NATAL-SUMMARY-LAYER --backend --frontend --json`.
- Backend coverage: pipeline plus all Natal pytest packs (context, style,
  validation fallback suites, generation/verifier tests).
- Frontend coverage: quality/report-create/forecast-read specs.
- PASS additionally requires a benchmark rerun: `gracectl slice replay M-NATAL-SUMMARY-LAYER --json`
  which wraps `python3 scripts/live_quality_benchmark.py --manifest docs/benchmark_manifests/natal_rerun_2026-03-19.json`.
- Attach the benchmark log to CI artifacts alongside the grace-report entry.

## Nightly Automation Profile

### Watchers (log-health loops)
- `gracectl watch run FEED-PERSONALIZED-DAILY --json`: tails
  `feed_admin_watch` (feed + admin logs). Schedule every 15 minutes; fail trigger
  opens an incident and uploads watcher logs from `logs/gracectl/FEED-PERSONALIZED-DAILY/`.
- `gracectl watch run ADMIN-ENTITLEMENTS-FLOW --json`: reuses the same watcher,
  providing admin-specific alerting while still tailing both feeds.
- `gracectl watch run FORECAST-LADDER-CATALOG-FLIP --json`: runs
  `forecast_catalog_watch.py` to ensure catalog checkout/resume activity inside
  the last 30 minutes. Use a 15-minute cron with auto-restart on non-zero exit.
- (Natal slice currently has no dedicated watcher; rely on nightly demo +
  benchmark replay.)

### Nightly smoke & replay sweep
- Run `gracectl env check --profile full --json` once at the top of the nightly pipeline.
- For each slice, execute `gracectl demo run <SLICE> --backend --frontend --replay --json --keep-going`.
  - Demos automatically call `slice verify`; combine with `--keep-going` so
    backend/fronted/replay can surface multiple failures in one pass.
- After demos, run standalone log replays where gates require persisted
  evidence:
  - `gracectl slice replay FEED-PERSONALIZED-DAILY --flow feed --limit 500 --json` (captures feed delivery stats).
  - `gracectl slice replay ADMIN-ENTITLEMENTS-FLOW --flow admin --limit 200 --json`.
  - `gracectl slice replay FORECAST-LADDER-CATALOG-FLIP --flow catalog --json`.
  - `gracectl slice replay M-NATAL-SUMMARY-LAYER --json` (benchmark rerun).
- Nightly PASS = all demos and replays exit 0. Collect the same artifacts as PR
  runs plus replay JSON files under `logs/gracectl/<SLICE>/replay-*.json`.

## Cron Shortcuts

| Purpose | Suggested cadence | Command | Notes |
| --- | --- | --- | --- |
| Feed + Admin health | `*/15 * * * *` | `cd /opt/astro-project && GRACECTL_REPORT_PATH=test-results/grace-report.json gracectl watch run FEED-PERSONALIZED-DAILY --json >> logs/feed_admin_watch.log 2>&1` | Covers both FEED-PERSONALIZED-DAILY and ADMIN-ENTITLEMENTS-FLOW because the watcher tails both logs; configure alerting on non-zero exit. |
| Catalog/storefront health | `*/15 * * * *` | `cd /opt/astro-project && gracectl watch run FORECAST-LADDER-CATALOG-FLIP --json >> logs/forecast-catalog-watch.log 2>&1` | Mirrors existing `forecast_catalog_watch` instructions and ensures cron writes to repo logs for triage. |
| Daily demo sweep | `0 3 * * *` | `cd /opt/astro-project && gracectl demo run FEED-PERSONALIZED-DAILY --backend --frontend --replay --json` (repeat per slice or call a wrapper script) | Provides an early-morning confirmation that env, verification, and log replay still pass before business hours. |
| Benchmark rerun (Natal) | `0 4 * * 1,4` | `cd /opt/astro-project && gracectl slice replay M-NATAL-SUMMARY-LAYER --json` | Replaces manual `scripts/live_quality_benchmark.py` invocations; upload benchmark logs on completion. |

## Artifact retention & follow-up
- Store `test-results/grace-report.json`, `logs/gracectl/**`, and
  `test-results/failures/**` for 14 days (PR) and 30 days (nightly) so repeated
  flakiness can be diagnosed.
- Wire CI status checks so that the "GRACE slices" context reflects the worst
  status reported in grace-report (FAILED > WARN > PASS).
- When a watcher cron or nightly job fails, automatically open an incident
  ticket referencing the slice, run ID, and failure packet path to enforce the
  "до зелёного" rule before merges proceed.
