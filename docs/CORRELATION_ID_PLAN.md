# Correlation & Trace ID Rollout Plan (2026-03-22)

Context sources: `docs/LOGGING_AUDIT.md`, `backend/app/logging_utils.py`, `backend/app/main.py`, `frontend/lib/analytics.ts`, `frontend/components/catalog/catalog-analytics.ts`, and watcher scripts under `tools/log_watch/`.

## Backend Middleware
- Introduce `backend/app/middleware/correlation.py` with `CorrelationIdMiddleware`. Register it in `backend/app/main.py` before routers so every FastAPI request is wrapped.
- Middleware responsibilities:
  - Read incoming `X-Correlation-Id` (fallback to `X-Request-Id`). Validate as UUIDv4 or alphanumeric ≤64 chars; otherwise generate a new `uuid4`.
  - Always create a fresh `trace_id = uuid4()` for each HTTP request. Persist the original header (if valid) as `correlation_id` to allow multi-hop reuse.
  - Bind ids into `structlog.contextvars` (`correlation_id`, `trace_id`, `correlation_source`: header vs generated). Use `try/finally` to clear context to prevent leakage across concurrent async tasks.
  - Store ids on `request.state` and expose helper `get_request_correlation(request: Request)` for routers/background tasks. When scheduling `BackgroundTasks` or `asyncio.create_task`, pass these ids explicitly so log helpers can attach them.
  - Add headers to every response: `X-Correlation-Id` (stable) and `X-Trace-Id` (per-request) so browsers and watcher tooling can capture them. Ensure HEAD/OPTIONS still receive headers.
  - Log a `diagnostic.correlation_middleware` event when invalid IDs are sanitized (rate-limited) so observability can detect upstream issues.
- CLI / scheduler boundaries:
  - Provide `logging_utils.bind_correlation_ids(source: str)` helper for jobs outside FastAPI (cron/scheduler). Jobs should generate a new `correlation_id` per logical run and call the helper prior to logging. Store id on job context so child tasks reuse it.
  - Document fallback behavior in `RUNBOOK.md`: when middleware is bypassed (e.g., direct script), engineers must invoke `bind_correlation_ids` or pass explicit ids into log helpers.

## Logging updates
- Extend `backend/app/logging_utils.py`:
  - Add contextvar accessors `set_correlation_ids`, `get_correlation_ids`, `with_correlation_context` (context manager) to standardize binding from middleware and background jobs.
  - Update `log_catalog_event`, `log_admin_report_event`, and other helper entrypoints to accept optional `correlation_id` / `trace_id`. Default to `get_correlation_ids()` when parameters are missing so existing callers automatically benefit once middleware binds context.
  - Ensure `catalog_event_fields` writes ids into payload when available; keep them as root-level keys to preserve compatibility with `feed_admin_sink` JSONL format.
  - Expand `feed_admin_sink` allowlist to include `billing.*`, `scheduler.*`, `daily.*`, `diagnostic.*`, `llm.*`, matching gaps identified in `docs/LOGGING_AUDIT.md`. This ensures correlation metadata survives in all major slices.
  - For legacy logs (e.g., `scheduler` module) add lightweight wrappers that pull ids from context and emit `scheduler.run` events with correlation info so watchers can stitch jobs.
- Background pipelines:
  - When `start_scheduler()` kicks off tasks (see `backend/app/main.py`), generate a dedicated correlation id per scheduled run, bind it, and include job name in log context. This ensures daily feed pipeline logs align with the same id across `feed.jsonl`.
  - Update analytics ingestion (`backend/app/services/analytics.py`) to log `analytics.event_received` with both ids so events can be correlated back to frontend telemetry.

## Frontend propagation
- Build a `CorrelationManager` in `frontend/lib/correlation.ts`:
  - Use `sessionStorage` (key `astro.correlation_id`) to persist the active id. Expose `getCorrelationId()`, `setCorrelationId(id, { reason })`, and `newCorrelation(flow?: string)`.
  - Maintain a lightweight `traceId` generator for each outbound network request (e.g., `crypto.randomUUID()` per fetch).
- Update `frontend/lib/analytics.ts`:
  - Accept optional `correlationId`/`traceId` arguments. When absent, pull from `CorrelationManager`, generating + storing a new id for first event of a flow.
  - Include `correlation_id` and `trace_id` fields in the analytics payload. Attach `X-Correlation-Id` header (and optionally `X-Trace-Id`) to `/api/analytics/event` fetch calls so middleware treats telemetry as first-class requests.
  - Provide a helper `withCorrelationHeaders(init?: RequestInit)` returning headers merged with `X-Correlation-Id` for general API calls.
- Catalog-specific flows (`frontend/components/catalog/catalog-analytics.ts`):
  - When checkout/history/resume flows start, call `CorrelationManager.newCorrelation("catalog_checkout")` and pass resulting id to all `trackCatalogEvent` invocations.
  - For resume tokens, continue hashing but include correlation metadata in payload so backend `catalog.checkout_resume_*` logs include the same id.
- Broader UI coverage:
  - Replace `console.error` usage in `/create`, `/week`, `/profile` pages with `trackEvent("ui.error", { correlation_id: ... })`. Document contract so developers know to import `CorrelationManager` when instrumenting new surfaces.
  - For SSR (Next.js server components), thread the header from `request` into props so client components can seed the stored id.

## Watcher/CI impact
- Update watcher utilities (`tools/log_watch/common.py`) to parse/display `correlation_id` & `trace_id` columns. Provide CLI filters `--correlation-id=<uuid>` for quick slicing.
- Modify `feed_admin_watch.py` and `forecast_catalog_watch.py` to include correlation id in alert summaries and Slack/Telegram payloads (once alerts are wired), enabling engineers to jump from alert → logs → analytics quickly.
- Extend `WATCHER_EXPANSION_PLAN.md` / `CI_GRACECTL_PLAN.md` with:
  - A regression test ensuring middleware runs (e.g., hitting `/healthz` must echo correlation header).
  - Tasks to add jq-based checks during CI that verify JSONL lines contain correlation fields after running sample requests.
- Ensure `scripts/pipeline.py` backend quick suite gains unit coverage for middleware + logging helpers (simulate incoming header, assert `structlog` emits ids). Frontend quick suite (`./scripts/run_e2e.sh --last-failed`) should include an assertion that `fetch` sends `X-Correlation-Id` (exposed via Playwright request inspection).
- Document debugging workflow in `docs/gracectl_watch_demo.md`: include new commands referencing correlation ids so on-call runbooks stay accurate.

## Implementation Checklist
- [x] Middleware: `CorrelationIdMiddleware` реализован, читает `x-correlation-id`/`x-request-id`, выставляет response headers и санитизирует входные значения.
- [x] Logging helpers: context binding/accessor APIs реализованы; `log_*` helpers принимают optional ids; sink routing переведён на `JSONL_ROUTES` с prefix-based dispatch.
- [ ] Frontend telemetry: build `CorrelationManager`, update `trackEvent`/`trackCatalogEvent`, and standardize header propagation for all API/analytics calls (browser + SSR).
- [ ] Watchers & CI: enhance log watchers for correlation filters, update docs/runbooks, and add automated checks (pipeline unit tests + Playwright coverage) validating propagation.
- [ ] Testing: once implemented, run `docker exec astro-project-backend-1 python3 scripts/pipeline.py` and `./scripts/run_e2e.sh --last-failed` to confirm end-to-end ids flow from browser to JSONL logs.

## Week Surface Telemetry Contract
- File owner: `frontend/app/week/page.tsx`.
- Shared resume bridge: `frontend/components/catalog/catalog-checkout-resume.tsx` via `CatalogCheckoutResumeBanner`.
- Canonical surface value stays `week` for all `trackCatalogEvent(...)` calls emitted by the page and the embedded resume banner.
- The page seeds catalog analytics context on mount with `surface: "week"`, `flow_id: FLOW-FORECAST-CATALOG`, `correlation_id`, optional `checkout_token`, `entry_point`, and `entry_semantic_block` from search params.
- `CorrelationManager` / `startCatalogCorrelation("week_page")` establish the browser correlation id once; all page fetches must continue through `correlatedFetch(...)` so `/api/reports/*` requests carry `X-Correlation-Id`.
- Error telemetry uses `ui.error` with `surface: "week"` and semantic `block`; keep this shape when extending week-side actions.
- Current page-specific events emitted from `frontend/app/week/page.tsx` include:
  - `week.fetch_start`
  - `week.fetch_success`
  - `week.fetch_empty`
  - `week.generate_start`
  - `week.generate_success`
  - `week.generate_error`
  - `week.cta_click`
  - `week.section_toggle`
  - `week.read_full_report`
- `CatalogCheckoutResumeBanner` must be passed `surface="week"`; its telemetry remains in the shared `catalog.checkout_resume_*` namespace while inheriting the week correlation/context envelope.
- Resume/banner events expected on the week surface:
  - `catalog.checkout_resume_ready`
  - `catalog.checkout_resume_start`
  - `catalog.checkout_resume_success`
  - `catalog.checkout_resume_cancel`
  - `catalog.checkout_resume_status`
- Entry links into `/week` should continue to populate `entry_point` and, when meaningful, `entry_semantic_block` (example: homepage deep CTA uses `CTA_WEEK`) so downstream telemetry can attribute the landing source.


## History Surface Telemetry Contract
- File owner: `frontend/app/reports/history/page.tsx`.
- Shared analytics helpers live in `frontend/components/catalog/catalog-analytics.ts`; the embedded resume bridge still renders through `frontend/components/catalog/catalog-checkout-resume.tsx` via `CatalogCheckoutResumeBanner`.
- Canonical surface value stays `history` for all `trackCatalogEvent(...)` calls emitted by the page and the embedded resume banner.
- On mount, the page establishes the browser correlation once via `startCatalogCorrelation(checkoutToken ? "history_checkout_resume" : "history_view")` and pushes `user_id`, optional `checkout_token`, and `correlation_id` into shared catalog analytics context with `setCatalogAnalyticsContext(...)`.
- Shell states use one canonical payload, `historyShellAnalytics`, with `event_name = "catalog.history_view"`, `module = M-REPORTS-HISTORY`, `contract = FN-HISTORY-VIEW`, `block = semantic_block = SHELL_RENDER`, `surface = "history"`, and `entry_point = "history-page-shell"`.
- History fetch and user-intent telemetry is emitted through `trackCatalogEvent(...withCatalogTrace(...))`, so `catalog.history_start|success|error|filter|cta|open_report` inherit the same correlation envelope and semantic block labels.
- `CatalogCheckoutResumeBanner` must be passed `surface="history"` and `entryPoint="history-inline-resume"`; its shared `catalog.checkout_resume_*` events then continue the already-bootstrapped history session instead of minting a second flow.
- `/reports/history` is therefore the canonical history → resume bridge: history actions describe prior-order intent, while resume-banner events preserve the same `correlation_id` / `checkout_token` context for checkout recovery and log stitching.
