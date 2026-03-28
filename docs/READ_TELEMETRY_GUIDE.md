# Read Telemetry Guide

## Scope

Документ описывает telemetry-цепочку для surface `/read/[id]`: открытие read surface, взаимодействия с resume banner, share CTA, failure/retry/support сценарии и связь с общим catalog/resume telemetry.

## Источники данных

### Frontend

- `frontend/app/read/[id]/page.tsx` — основной orchestration layer для read telemetry.
- `frontend/components/catalog/catalog-checkout-resume.tsx` — общий resume banner, который `/read/[id]` переиспользует для checkout resume telemetry.
- `frontend/components/catalog/catalog-analytics.ts` — общий transport/context layer для catalog telemetry (`setCatalogAnalyticsContext`, `trackCatalogEvent`).
- `frontend/components/catalog/create-shared.ts` — shared GRACE trace helpers (`withCatalogTrace`, module/block mapping).

### Backend

- `backend/app/main.py` → `GET /api/reports/{report_id}` — источник payload для read surface; возвращает `report`, `chunks`, `chart_svg`, `week_brief`, `week_brief_envelope` и пишет backend detail telemetry через `log_report_detail_success/error`.
- `backend/app/main.py` → `POST /api/reports/{report_id}/regenerate` — backend endpoint для retry из failure surface; пишет `log_bridge_resume_start`, `log_bridge_resume_success`, `log_catalog_surface_error` c `surface="bridge_regenerate"`.
- `backend/app/main.py` → `POST /api/support/tickets` — support endpoint, связанный с user support flow, но сам `/read/[id]` currently only tracks support/history CTA click and ведёт пользователя в history, без прямого POST с read page.

## Базовый telemetry contract

- Канонический `flow_id` для read surface: `FLOW-FORECAST-CATALOG`.
- Канонический `surface` для read UI: `read`.
- Для failure fallback используется `surface: "failure"`, но `flow_id` остаётся тем же `FLOW-FORECAST-CATALOG`.
- Корреляция строится через `CorrelationManager` в `frontend/app/read/[id]/page.tsx` и прокидывается в `trackCatalogEvent(...)`.
- Read page при bootstrap вызывает `setCatalogAnalyticsContext({ user_id, checkout_token, correlation_id, flow_id })`, чтобы связать read + catalog + resume события в одну correlation chain.

## Flow, surface, block mapping

### Flow / surface

- `flow_id: FLOW-FORECAST-CATALOG`
- `surface: "read"` — normal read state, share, open, time-spent, local resume CTA.
- `surface: "failure"` — failure fallback context для retry/support CTA.
- backend regenerate logs используют `surface: "bridge_regenerate"` как backend-side bridge surface.

### Block IDs

Из `frontend/app/read/[id]/page.tsx`:

- `LOADING_STATE`
- `SHARE_SECTION`
- `CTA_TRACKING`
- `RESUME_ENTRY`
- `FAILURE_CONTEXT`
- `FAILURE_RETRY`
- `FAILURE_SUPPORT`

Практическое назначение:

- `CTA_TRACKING` — open/time-spent/read fetch correlation.
- `SHARE_SECTION` — share/copy CTA.
- `RESUME_ENTRY` — read-level resume CTA actions, пришедшие из banner callbacks.
- `FAILURE_CONTEXT` — canonical fallback context payload.
- `FAILURE_RETRY` — regenerate click + correlated POST `/api/reports/{id}/regenerate`.
- `FAILURE_SUPPORT` — support/history CTA click на failure surface.

## Event chain для `/read/[id]`

### 1. Open read surface

При успешной загрузке `GET /api/reports/{id}` frontend вызывает:

- `catalog.read_opened`

Payload включает:

- `report_id`
- `report_type`
- `status`
- `entry_point`

`entry_point`:

- `read_resume_banner` — если route открыт с `checkout` query param.
- `read_direct` — если report открыт напрямую.

Block metadata:

- `block_id: CTA_TRACKING`
- `surface: read`
- `flow_id: FLOW-FORECAST-CATALOG`

### 2. Time spent on read surface

На unmount, если сессия длилась больше 1000 ms, frontend вызывает:

- `catalog.read_time_spent`

Payload включает:

- `report_id`
- `duration_ms`

Block metadata:

- `block_id: CTA_TRACKING`
- `surface: read`
- `flow_id: FLOW-FORECAST-CATALOG`

### 3. Section open / close behavior

Секции открываются через `toggleSection(sectionId)` и `toggleAllSections()`, но в текущей реализации отдельное telemetry-событие на open/close section **не отправляется**.

Важно зафиксировать это явно:

- UI поддерживает section expansion/collapse.
- `openedCount` и `allSectionsExpanded` используются только для local UI state.
- Для section open telemetry на сегодня нет отдельного `catalog.read_section_opened` или аналогичного события.

Если в будущем понадобится section-level telemetry, естественная точка расширения — `toggleSection(...)` с block-level mapping на read section cards.

## Resume banner telemetry

`/read/[id]` встраивает `CatalogCheckoutResumeBanner` с параметрами:

- `surface="read"`
- `entryPoint="read_resume_banner"`
- `checkoutToken`
- `onTrackAction={handleResumeCTA}`

Это даёт два связанных слоя telemetry.

### A. Shared banner events из `CatalogCheckoutResumeBanner`

Баннер сам отправляет canonical resume telemetry:

- `catalog.checkout_resume_ready`
- `catalog.checkout_resume_start`
- `catalog.checkout_resume_status`
- `catalog.checkout_resume_success`
- `catalog.checkout_resume_cancel`

Для этих событий `/read/[id]` задаёт:

- `surface: read`
- `entry_point: read_resume_banner`
- общий `flow_id: FLOW-FORECAST-CATALOG`

Статусы polling/session layer:

- `checking`
- `pending`
- `succeeded`
- `canceled`
- `failed`
- `unauthorized`
- `error`

### B. Local read CTA events

Через `onTrackAction={handleResumeCTA}` read page дополнительно пишет локальные события вида:

- `catalog.read_resume_ready`
- `catalog.read_resume_start`
- `catalog.read_resume_success`
- `catalog.read_resume_cancel`
- `catalog.read_resume_status`

Фактический suffix зависит от `action`, который баннер передаёт в callback.

Payload для этих событий включает:

- `report_id`
- `report_type`
- `entry_point`
- `action`

Block metadata:

- `block_id: RESUME_ENTRY`
- `surface: read`
- `flow_id: FLOW-FORECAST-CATALOG`

Итог: read page не заменяет banner telemetry, а дополняет его read-specific CTA envelope, сохраняя одну correlation chain.

## Share telemetry

Share CTA расположен в `SHARE_SECTION` и вызывает `handleShare()`.

При success-path отправляется:

- `catalog.read_share`

Payload включает:

- `report_id`
- `report_type`
- `action: native_share | clipboard_copy`
- `entry_point: share_button`
- `has_share_token: boolean`

Block metadata:

- `block_id: SHARE_SECTION`
- `surface: read`
- `flow_id: FLOW-FORECAST-CATALOG`

Privacy note:

- `page.tsx` явно фиксирует invariant, что raw checkout tokens и share hashes не должны уходить в telemetry payload.
- В telemetry уходит только sanitized boolean `has_share_token`, а не само значение `share` query param.

## Failure / error telemetry

### Frontend failure surface

Когда report не может быть показан в обычном режиме и используется failure fallback, frontend строит canonical context через `fetchFailureContext()`:

- `report_id`
- `report_type`
- `status`
- `entry_point`
- `retry_cta_id: read-regenerate-button`
- `support_cta_id: read-failure-history-link`
- `surface: failure`
- `flow_id: FLOW-FORECAST-CATALOG`

Это context payload затем используется в двух CTA.

### Retry / regenerate click

При клике на retry вызывается:

- `catalog.read_regenerate_click`

Payload:

- весь failure context
- `action: regenerate`

Block metadata:

- `block_id: FAILURE_RETRY`
- `surface: failure`
- `flow_id: FLOW-FORECAST-CATALOG`

После этого выполняется correlated POST:

- `POST /api/reports/{report_id}/regenerate`

Backend telemetry для этого endpoint:

- `log_bridge_resume_start(..., surface="bridge_regenerate", report_id=...)`
- `log_bridge_resume_success(..., surface="bridge_regenerate", report=...)`
- `log_catalog_surface_error(surface="bridge_regenerate", ...)` для invalid id / not found / wrong status

Таким образом frontend failure CTA и backend regenerate bridge связаны через один пользовательский retry flow, но имеют разные `surface` значения:

- frontend CTA: `failure`
- backend bridge: `bridge_regenerate`

### Support / history click

При клике на failure support CTA вызывается:

- `catalog.read_support_click`

Payload:

- весь failure context
- `action: history`

Block metadata:

- `block_id: FAILURE_SUPPORT`
- `surface: failure`
- `flow_id: FLOW-FORECAST-CATALOG`

Текущий UX ведёт пользователя в `/reports/history`. Прямой вызов `POST /api/support/tickets` с `/read/[id]` сейчас не выполняется.

### Backend report load errors

Для `GET /api/reports/{report_id}` backend пишет own endpoint telemetry:

- success: `log_report_detail_success(user, report=report, chunk_count=...)`
- error: `log_report_detail_error(user, report_id=..., error=..., status_code=...)`

Это backend detail/report telemetry, а не catalog frontend telemetry, но оно является backend-source для read observability.

## Связь с catalog / resume telemetry

`/read/[id]` является частью общей catalog telemetry модели, а не isolated page.

Связь строится так:

- `FLOW-FORECAST-CATALOG` общий для catalog surfaces, checkout resume и read surface.
- `setCatalogAnalyticsContext(...)` на read page прокидывает `checkout_token`, `user_id`, `correlation_id`, `flow_id` в общий analytics context.
- `CatalogCheckoutResumeBanner` использует тот же transport (`trackCatalogEvent`) и тот же correlation chain.
- Поэтому sequence вида `catalog -> checkout -> read` может быть stitched together по общему correlation id / flow id.

Практически это означает:

- resume banner события (`catalog.checkout_resume_*`) — shared catalog primitives.
- read page события (`catalog.read_*`) — surface-specific слой над теми же primitives.
- regenerate backend (`bridge_regenerate`) — backend bridge continuation того же пользовательского flow после failure.

## Что именно сейчас отправляется

### Read page

- `catalog.read_opened`
- `catalog.read_time_spent`
- `catalog.read_share`
- `catalog.read_regenerate_click`
- `catalog.read_support_click`
- `catalog.read_<resume action>` через callback от resume banner

### Resume banner on read surface

- `catalog.checkout_resume_ready`
- `catalog.checkout_resume_start`
- `catalog.checkout_resume_status`
- `catalog.checkout_resume_success`
- `catalog.checkout_resume_cancel`

### Не отправляется сейчас

- отдельное telemetry-событие для открытия/закрытия section card
- direct support ticket creation telemetry из `/read/[id]`

## Acceptance / verification

Обязательные acceptance-команды для этой doc-задачи:

- `cd frontend && npm exec tsc -- --noEmit`
- `./scripts/run_e2e.sh e2e/quality.spec.ts -g "read"`

## Files to inspect during future updates

- `frontend/app/read/[id]/page.tsx`
- `frontend/components/catalog/catalog-checkout-resume.tsx`
- `frontend/components/catalog/catalog-analytics.ts`
- `frontend/components/catalog/create-shared.ts`
- `backend/app/main.py`
- `frontend/e2e/quality.spec.ts`
