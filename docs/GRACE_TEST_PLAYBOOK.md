# GRACE Test Playbook

Working copy: commit snapshot `grace-2026-03-21` (see `verification-matrix.md`). This playbook links each active slice to the verification matrix (`VM-*` IDs), concrete regression commands, and the evidence/log contours captured in existing docs. Run all commands from `/opt/astro-project` unless noted otherwise.

## Shared Conventions
- Always start with `docker exec astro-project-backend-1 python3 scripts/pipeline.py` to keep `backend:quick` hooks green (`docs/GRACE_ARTIFACTS.md`).
- `VM-*` details live in `verification-matrix.md`; reference that file when a VM’s scope or command list changes.
- Treat controller-packet artifacts (benchmark JSON, log replays, Playwright traces) as part of the Gate; file them next to the source doc named below.
- Export fresh background-task logs with `python3 automation/export_evidence.py`; it copies recent `.task-logs` files into `test-results/evidence/rev-YYYY-MM-DD/` and writes `manifest.json` for the packet.

## Evidence Export
- **Purpose**: collect fresh `.task-logs` artifacts into a single evidence folder without manual copying.
- **Default command**: `python3 automation/export_evidence.py`
- **Options**:
  - `python3 automation/export_evidence.py --hours 6` — narrow the freshness window.
  - `python3 automation/export_evidence.py --dest rev-2026-03-27-task-logs` — override the destination folder name.
  - `python3 automation/export_evidence.py --dry-run` — preview selected files without copying.
- **Output**: copies matching logs into `test-results/evidence/<dest>/` and writes `test-results/evidence/<dest>/manifest.json` with source path, destination path, modified timestamp, and size.
- **When to run**: after the task-specific quick profile is green, before shipping the controller packet or updating Gate evidence.

## Slice Profiles

### M-NATAL-SUMMARY-LAYER
- **Purpose**: Harden `executive_summary` / `final_synthesis` fallbacks and style hints per `GRACE_SLICE_NATAL_DAILY.md` and the live benchmark follow-up in `docs/ASTRO_QUALITY_BENCHMARK_2026-03-19_NATAL_EXEC_SUMMARY_FOLLOWUP.md`.
- **VM IDs (`verification-matrix.md`)**:
  - `VM-NATAL-CONTEXT` — proves `section_context` and report contract integrity.
  - `VM-NATAL-STYLE-CONTRACT` — enforces runtime style hints from `STYLE_CONTRACT.md`.
  - `VM-NATAL-SUMMARY-REPAIR` — keeps deterministic summary-layer fallbacks clean.
  - `VM-FORECAST-CREATE-READ` + `VM-FORECAST-SEMANTICS` — cover shared forecast context that this slice still touches for mixed natal/forecast flows.
  - `VM-READ-QUALITY` + `VM-REPORTS-UX-CONSISTENCY` — guard `/read` and `/reports` rendering used by natal/forecast products.
- **Evidence export**:
  - Task logs: `python3 automation/export_evidence.py --dest rev-YYYY-MM-DD`.
  - Extra copies: `python3 automation/export_evidence.py --dest rev-YYYY-MM-DD --copy test-results/grace-report.json --copy logs/gracectl`.
  - Nightly bundle: `./automation/nightly_evidence_bundle.sh nightly-YYYY-MM-DD`.
  - Each revision writes `test-results/evidence/<rev>/manifest.json` and updates `test-results/evidence/manifest.revisions.json` for cross-revision indexing.
- **Test commands**:
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py` (backend quick).
  - `PYTHONPATH=. python3 -m pytest tests/test_natal_section_context.py tests/test_report_context.py`.
  - `PYTHONPATH=. python3 -m pytest tests/test_validation_relaxed.py tests/test_validation_template_fallback.py`.
  - `PYTHONPATH=. python3 -m pytest tests/verify_natal_generation.py tests/verify_natal_style.py`.
  - Benchmark loop: `python3 scripts/live_quality_benchmark.py --manifest docs/benchmark_manifests/natal_rerun_2026-03-19.json --llm-mode openrouter --out-dir tmp/gate_artifacts/FLOW-REPORT-GENERATION`.
- **Evidence / replay**:
  - Rerun artifacts under `tmp/gate_artifacts/FLOW-REPORT-GENERATION/` (JSON + markdown) plus the manifest above.
  - Narrative and scoring in `docs/ASTRO_QUALITY_BENCHMARK_2026-03-19_NATAL_EXEC_SUMMARY_FOLLOWUP.md`.
  - Benchmark run logs inside `tmp/quality_benchmark_runs/` for reproducibility notes.
- **Gate condition**: `N8 / Gate 3` stays ✅ only when the benchmark rerun reports `0` template/repair markers and the VM set above is green; attach the latest benchmark summary to the controller packet (`docs/GRACE_ARTIFACTS.md`).


### START-GATEWAY
- **Purpose**: Keep `/start` as the single strict-GRACE gateway for guest/mock/authenticated entry, with redirect telemetry and stable auth-wait/profile-routing hooks from `frontend/app/start/page.tsx`.
- **VM IDs (`verification-matrix.md`)**:
  - `VM-START-GATEWAY` — `/start` redirect/auth-wait/profile-check routing.
  - `VM-FEED-ROBUSTNESS` — downstream homepage/feed safety after gateway redirect.
- **Test commands**:
  - `./scripts/run_e2e.sh e2e/landing.spec.ts`.
  - `./scripts/run_e2e.sh e2e/core-ux.spec.ts`.
- **Evidence / replay**:
  - Playwright transcript for `frontend/e2e/landing.spec.ts` proving guest auth gate + mock redirect.
  - Structured analytics events `start.redirect_decision`, `start.auth_wait`, `start.profile_route` carrying `FLOW-HOME-FEED` with `START_GATE`, `AUTH_WAIT`, `PROFILE_ROUTE` semantic blocks.
- **Gate condition**: `/start` stays green only when guest, mock, and authenticated route decisions remain deterministic and no redirect path bypasses the gateway telemetry contract.

### CREATE-PAGE-CHECKOUT
- **Purpose**: Preserve the strict-GRACE create-page flow for catalog checkout, direct report creation, and one-off resume/hydration in `frontend/app/create/create-page-client.tsx`.
- **VM IDs (`verification-matrix.md`)**:
  - `VM-FORECAST-CREATE-READ` — create/read correctness for week/month/year/decade flows.
  - `VM-BILLING-ACCESS` — one-off checkout session persistence, resume, and entitlement bridge.
  - `VM-REPORTS-UX-CONSISTENCY` — shell/copy alignment around `/create` and `/reports`.
- **Test commands**:
  - `./scripts/run_e2e.sh e2e/report-create.spec.ts`.
  - `./scripts/run_e2e.sh e2e/report-failure.spec.ts`.
  - `./scripts/run_e2e.sh e2e/billing-catalog-alignment.spec.ts`.
  - `E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should resume direct mock checkout from billing complete to read"`.
- **Evidence / replay**:
  - Playwright traces for synastry/solar product input hydration and `/api/reports/create` payload capture.
  - Catalog analytics events emitted from `FLOW-FORECAST-CATALOG` with `TOKEN_RESOLUTION`, `CTA_PRIMARY`, `CTA_CANCEL`, and `PRODUCT_INPUT_SYN` semantic blocks.
  - Backend billing/report traces proving `/api/billing/sessions/{token}` resume and `/api/reports/create` handoff stay correlated.
- **Gate condition**: create-page remains green only when checkout-token restore, direct create CTA, and synastry/solar product-input hydration all pass without bypassing the correlation/telemetry contract.

### FEED-PERSONALIZED-DAILY
- **Purpose**: Keep personalized `/api/feed/today` deterministic and auth-safe as described in `docs/personalized_daily_feed_v2.md`.
- **VM IDs (`verification-matrix.md`)**:
  - `VM-FEED-ROBUSTNESS` — daily endpoint payload + homepage states.
- **Test commands**:
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
  - `PYTHONPATH=. python3 -m pytest tests/test_daily_feed_robustness.py tests/test_personalized_daily_service.py tests/verify_daily_feed.py`.
  - `python3 scripts/verify_api_responses.py` (HTTP contract check).
  - `./scripts/run_e2e.sh e2e/core-ux.spec.ts` (covers homepage ready/fallback/error branches).
  - Log replay: `python3 tools/feed_logs/replay_last.py /path/to/feed.jsonl`.
- **Evidence / replay**:
  - Gate 3 log in `docs/personalized_daily_feed_v2.md` (“Gate Evidence — FLOW-DAILY-FEED”).
  - Structured events `feed.entry|feed.debug|feed.error` plus watcher output from `tools/log_watch/feed_admin_watch.py`.
  - Store recent replay snippets in `logs/feed.jsonl` (or equivalent) referenced by the replay helper above.
- **Gate condition**: `F11 / Gate 3 backend quick + targeted UX smoke` — attach backend pytest + `core-ux` transcript + feed replay summary showing both personalized and anonymous modes green (per `docs/GRACE_ARTIFACTS.md`).

### ADMIN-ENTITLEMENTS-FLOW
- **Purpose**: Preserve the Gate-3-ready admin entitlement workflow documented in `docs/rollout_notes/admin-entitlements-gate3-2026-03-20.md` (grant/create/reuse/consume + admin UI ops).
- **VM IDs (`verification-matrix.md`)**:
  - `VM-BILLING-ACCESS` — proof for entitlement-first access/runtime alignment.
  - `VM-REPORTS-UX-CONSISTENCY` — protects `/reports` shell and catalog consistency relied on by admin tools.
- **Test commands**:
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
  - `PYTHONPATH=. python3 -m pytest tests/test_entitlements.py tests/test_entitlements_unit.py tests/test_one_off_entitlements_scaffold.py`.
  - `PYTHONPATH=. python3 -m pytest tests/test_billing_checkout_sessions.py tests/test_billing_checkout_resume.py tests/test_one_off_access_runtime.py` (VM-BILLING-ACCESS matrix).
  - `E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge <product> one-off mock checkout through billing complete to read"` for each product listed in `verification-matrix.md`.
  - `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/admin.entitlements.spec.ts`.
- **Evidence / replay**:
  - Gate 3 packet `docs/rollout_notes/admin-entitlements-gate3-2026-03-20.md` plus Playwright traces in `frontend/test-results/`.
  - Backend/admin structured logs (`admin.entry`, `admin.queue`, `admin.section_regenerate`, `admin.export`, `admin.entitlement_grant`) replayed via `python3 tools/admin_logs/replay_last.py <admin-log.jsonl>`.
  - Combined feed/admin watcher summaries from `tools/log_watch/feed_admin_watch.py` for continuous monitoring.
- **Gate condition**: `A11 / Gate 3 rollout-ready on 2026-03-20` — keep both admin Playwright suites + VM-BILLING-ACCESS matrix green and attach the latest log replay snippet proving grant/reuse/consume telemetry.

### FORECAST-LADDER-CATALOG-FLIP
- **Purpose**: Align catalog/storefront/runtime for the day-week-month-year ladder per `GRACE_SLICE_FORECAST_LADDER.md` and `docs/BILLING_CATALOG_ALIGNMENT_2026-03-19.md` (shared consumer shell, one-off bridge, checkout resume).
- **VM IDs (`verification-matrix.md`)**:
  - `VM-FORECAST-CREATE-READ` — verifies week/month/year create/read flows.
  - `VM-FORECAST-SEMANTICS` — ensures semantic layer determinism for forecast copy.
  - `VM-READ-QUALITY` — shared read safety.
  - `VM-REPORTS-UX-CONSISTENCY` — storefront/history shell alignment.
  - `VM-BILLING-ACCESS` — checkout/entitlement bridge for one-off forecasts.
- **Test commands**:
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.
  - `PYTHONPATH=. python3 -m pytest tests/test_billing_checkout_sessions.py tests/test_billing_checkout_resume.py tests/test_one_off_access_runtime.py tests/test_one_off_entitlements_scaffold.py tests/test_legacy_workflow_one_off_alignment.py tests/test_report_contract.py`.
  - `./scripts/run_e2e.sh e2e/billing-catalog-alignment.spec.ts e2e/report-create.spec.ts e2e/report-failure.spec.ts`.
  - `./scripts/run_e2e.sh e2e/history-cta.spec.ts e2e/month-forecast-bridge-storefront.spec.ts e2e/year-forecast-bridge-storefront.spec.ts e2e/solar-return-bridge-storefront.spec.ts e2e/synastry-bridge-storefront.spec.ts`.
  - Catalog log watcher: `python3 tools/log_watch/forecast_catalog_watch.py --catalog-log logs/catalog.jsonl --window-minutes 30` (mirrors `logs/forecast-catalog-watch_MEMORY.md`).
- **Evidence / replay**:
  - Slice baseline doc `GRACE_SLICE_FORECAST_LADDER.md` + catalog alignment brief `docs/BILLING_CATALOG_ALIGNMENT_2026-03-19.md`.
  - Watcher snapshots stored in `logs/forecast-catalog-watch_MEMORY.md` and CLI output from `tools/log_watch/forecast_catalog_watch.py`.
  - Controller packet should include the latest billing/bridge Playwright traces (files under `frontend/test-results/`) and pytest outputs for the checkout/runtime tests above.
- **Gate condition**: `FLOW-FORECAST-CATALOG` remains at Gate 2 until catalog/runtime evidence is attached — ship a controller packet (doc + watcher log + regression transcripts) before promoting to Gate 3 (`docs/GRACE_ARTIFACTS.md`).

---

**Next steps**: when any slice adds a new `VM-*`, update this playbook alongside `verification-matrix.md` and `docs/GRACE_ARTIFACTS.md` so Purpose → VM → Tests → Evidence → Gate stays traceable.
