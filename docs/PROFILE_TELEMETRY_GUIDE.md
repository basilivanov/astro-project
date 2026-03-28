# Profile Telemetry Guide

## Scope

Документ описывает telemetry-контракт для surface `/profile`, `/profile/edit` и admin dashboard surface `/admin/dashboard`: profile view/edit, referral CTA, subscription status и admin dashboard telemetry. Документ фиксирует канонические `flow_id`, `surface`, `block` и связь с общим catalog/resume telemetry.

## Источники данных

### Frontend

- `frontend/app/profile/page.tsx` — profile overview surface, загрузка `/api/users/me`, referral CTA, audience switch, навигационные CTA и subscription status presentation.
- `frontend/app/profile/edit/page.tsx` — profile edit surface, загрузка/сохранение профиля и edit-specific telemetry.
- `frontend/app/admin/dashboard/page.tsx` — admin dashboard surface, загрузка summary данных и dashboard CTA/section telemetry.
- `frontend/components/catalog/catalog-analytics.ts` — общий transport/context layer для catalog telemetry (`setCatalogAnalyticsContext`, `startCatalogCorrelation`, `trackCatalogEvent`).
- `frontend/lib/correlation.ts` — correlation bootstrap и correlated fetch.

### Backend

- `backend/app/main.py` — backend entrypoint для profile/admin API routes и analytics ingest, источник backend-side логирования/доставки telemetry событий.
- `backend/app/services/analytics.py` — allowlist и backend transport для frontend analytics событий.

## Базовый telemetry contract

- Канонический `flow_id` для profile и admin telemetry: `FLOW-FORECAST-CATALOG`.
- Profile overview использует `surface: "profile"`.
- Profile edit использует `surface: "profile_edit"`.
- Admin dashboard использует `surface: "admin_dashboard"`.
- Корреляция строится через `startCatalogCorrelation(...)`, `CorrelationManager.ensureCorrelationId()` и `correlatedFetch(...)` в profile/admin surfaces.
- Frontend должен вызывать `setCatalogAnalyticsContext({ user_id, correlation_id, flow_id })`, чтобы profile/admin события коррелировали с catalog/resume telemetry в одной цепочке.

## Связь с catalog/resume telemetry

Profile/admin telemetry не вводит отдельный telemetry transport и должен оставаться совместимым с уже зафиксированным catalog contract:

- profile/admin surfaces используют тот же `trackCatalogEvent(...)`, что и catalog/read/week surfaces;
- `correlation_id` должен совпадать с correlation chain catalog/resume сценариев, если пользователь приходит в profile/admin после checkout/resume;
- `flow_id: FLOW-FORECAST-CATALOG` сохраняет сквозную связь между profile событиями, catalog CTA и resume-banner telemetry;
- naming событий остаётся в пространстве `catalog.*`, чтобы backend allowlist/ingest в `backend/app/main.py` и `backend/app/services/analytics.py` не требовал отдельного profile-only transport.

Практически это означает:

- referral CTA из profile должен логироваться как catalog-совместимое surface event, а не как отдельный несвязанный marketing stream;
- subscription status на profile surface должен передавать тот же `user_id/correlation_id`, что и checkout/resume события, чтобы можно было связать paid state с предыдущим catalog flow;
- admin dashboard telemetry использует тот же envelope (`flow_id`, `surface`, `block`, `correlation_id`) для единообразной аналитики внутренних surfaces.

## Flow / surface / block mapping

### Canonical flow / surface

- `flow_id: FLOW-FORECAST-CATALOG`
- `surface: "profile"` — overview/profile landing
- `surface: "profile_edit"` — profile edit form
- `surface: "admin_dashboard"` — admin dashboard summary

### Canonical blocks

#### `frontend/app/profile/page.tsx`

- `ANALYTICS_CONTEXT_BOOTSTRAP` — bootstrap общего analytics context
- `PROFILE_DATA_FLOW` — open/load/error flow для profile payload
- `REFERRAL_CTA` — copy/share/open реферального CTA
- `SUBSCRIPTION_STATUS` — exposure статуса подписки
- `PROFILE_NAVIGATION` — переходы в edit/history/admin и др. profile menu CTA
- `AUDIENCE_SWITCH` — internal audience mode toggle для debug/admin preview

#### `frontend/app/profile/edit/page.tsx`

- `EDIT_ANALYTICS_CONTEXT` — edit surface context bootstrap
- `PROFILE_EDIT_LOAD` — initial form load
- `PROFILE_EDIT_SUBMIT` — save/start/success/error
- `PROFILE_EDIT_FORM` — field interaction / validation surface

#### `frontend/app/admin/dashboard/page.tsx`

- `ADMIN_DASHBOARD_BOOTSTRAP` — dashboard open/context bootstrap
- `ADMIN_DASHBOARD_SUMMARY` — summary cards/data load
- `ADMIN_DASHBOARD_CTA` — переходы из dashboard в users/reports/clients/etc.
- `ADMIN_DASHBOARD_FILTERS` — period/filter interactions, если surface их использует

## Profile overview event chain

### 1. Open profile surface

При открытии `/profile` frontend должен отправлять:

- `catalog.profile_view`

Рекомендуемый payload:

- `surface: "profile"`
- `flow_id: "FLOW-FORECAST-CATALOG"`
- `block: "PROFILE_DATA_FLOW"`
- `action: "view_live" | "view_mock"`
- `entry_point` — например `profile_direct`, `profile_menu`, `profile_resume_return`

### 2. Profile payload loaded

После успешной загрузки `/api/users/me` frontend отправляет:

- `catalog.profile_loaded`

Рекомендуемый payload:

- `surface: "profile"`
- `block: "PROFILE_DATA_FLOW"`
- `status: "success"`
- `subscription_state` — derived state (`active`, `expiring`, `inactive`)
- `days_left`
- `is_partner`

При ошибке загрузки используется:

- `catalog.profile_error`

с полями:

- `surface: "profile"`
- `block: "PROFILE_DATA_FLOW"`
- `status: "error"`
- `action: "profile_load"`
- `message`

### 3. Subscription status exposure

Profile overview должен фиксировать состояние подписки отдельным surface event при наличии payload:

- `catalog.profile_subscription_status`

Рекомендуемый payload:

- `surface: "profile"`
- `block: "SUBSCRIPTION_STATUS"`
- `status: "active" | "expiring" | "inactive"`
- `days_left`
- `subscription_active_until`
- `is_partner`

Это событие нужно трактовать как exposure event, а не как billing mutation.

### 4. Referral CTA

Реферальный блок на `/profile` должен логировать как минимум:

- `catalog.profile_referral_cta_viewed` — показ referral CTA
- `catalog.profile_referral_cta_clicked` — клик/тап по CTA
- `catalog.profile_referral_code_copied` — успешное копирование кода

Рекомендуемый payload:

- `surface: "profile"`
- `block: "REFERRAL_CTA"`
- `cta_id` — например `copy_referral_code`, `share_referral_link`
- `referral_code_present: true | false`
- `share_channel` — если известен (`clipboard`, `telegram_share`, `native_share`)

### 5. Profile navigation CTA

Переходы по меню из `/profile` должны использовать общий contract:

- `catalog.profile_navigation_clicked`

Рекомендуемый payload:

- `surface: "profile"`
- `block: "PROFILE_NAVIGATION"`
- `cta_id` — например `open_edit_profile`, `open_history`, `open_admin_dashboard`
- `target_surface`

## Profile edit event chain

### 1. Open edit surface

При открытии `/profile/edit` frontend должен отправлять:

- `catalog.profile_edit_view`

Payload:

- `surface: "profile_edit"`
- `block: "PROFILE_EDIT_LOAD"`
- `action: "view"`

### 2. Form loaded

После успешной загрузки данных формы:

- `catalog.profile_edit_loaded`

Payload:

- `surface: "profile_edit"`
- `block: "PROFILE_EDIT_LOAD"`
- `status: "success"`

### 3. Save flow

На submit/save используются события:

- `catalog.profile_edit_submit`
- `catalog.profile_edit_success`
- `catalog.profile_edit_error`

Рекомендуемый payload:

- `surface: "profile_edit"`
- `block: "PROFILE_EDIT_SUBMIT"`
- `changed_fields` — список/счётчик изменённых полей
- `status: "start" | "success" | "error"`
- `message` — только для error

Если форма имеет отдельные validation errors без сетевого запроса, их стоит относить к:

- `catalog.profile_edit_validation_error`

с `block: "PROFILE_EDIT_FORM"`.

## Admin dashboard telemetry

### Scope

Admin dashboard telemetry относится к `/admin/dashboard` и связанным summary/CTA на этой странице. Документ не покрывает все admin routes, только dashboard как верхнеуровневую admin surface.

### 1. Open dashboard

При открытии `/admin/dashboard` frontend должен отправлять:

- `catalog.admin_dashboard_view`

Payload:

- `surface: "admin_dashboard"`
- `flow_id: "FLOW-FORECAST-CATALOG"`
- `block: "ADMIN_DASHBOARD_BOOTSTRAP"`
- `action: "view"`

### 2. Summary loaded

После успешной загрузки dashboard summary/cards:

- `catalog.admin_dashboard_loaded`

Payload:

- `surface: "admin_dashboard"`
- `block: "ADMIN_DASHBOARD_SUMMARY"`
- `status: "success"`
- `cards_present`
- `period`

При ошибке:

- `catalog.admin_dashboard_error`

Payload:

- `surface: "admin_dashboard"`
- `block: "ADMIN_DASHBOARD_SUMMARY"`
- `status: "error"`
- `message`

### 3. Dashboard CTA

Переходы из summary cards / quick actions:

- `catalog.admin_dashboard_cta_clicked`

Payload:

- `surface: "admin_dashboard"`
- `block: "ADMIN_DASHBOARD_CTA"`
- `cta_id` — например `open_users`, `open_reports`, `open_clients`, `open_tickets`
- `target_surface`

### 4. Filters / period controls

Если dashboard содержит период/фильтры, их нужно логировать как:

- `catalog.admin_dashboard_filter_changed`

Payload:

- `surface: "admin_dashboard"`
- `block: "ADMIN_DASHBOARD_FILTERS"`
- `filter_id`
- `next_value`

## Backend notes (`backend/app/main.py`)

Backend для profile/admin telemetry должен оставаться точкой истины для ingest и server-side correlation:

- принимать frontend analytics envelope с `event`, `surface`, `block`, `flow_id`, `correlation_id`;
- не ломать allowlist `catalog.*` событий для новых profile/admin event names;
- при необходимости добавлять backend-side info logs для admin dashboard/profile API routes, но не дублировать frontend exposure events без явной причины;
- сохранять совместимость с существующим catalog/resume event pipeline.

Если backend пишет server-side diagnostics для profile/admin routes, рекомендуется использовать те же значения `surface`/`flow_id`, что и на frontend, чтобы логи и аналитика сходились.

## Implementation notes by file

### `frontend/app/profile/page.tsx`

Документируем как canonical source для:

- `catalog.profile_view`
- `catalog.profile_loaded`
- `catalog.profile_error`
- referral CTA events
- subscription status exposure
- navigation CTA events

### `frontend/app/profile/edit/page.tsx`

Документируем как canonical source для:

- `catalog.profile_edit_view`
- `catalog.profile_edit_loaded`
- `catalog.profile_edit_submit/success/error`
- optional validation error telemetry

### `frontend/app/admin/dashboard/page.tsx`

Документируем как canonical source для:

- `catalog.admin_dashboard_view`
- `catalog.admin_dashboard_loaded/error`
- dashboard CTA/filter telemetry

### `backend/app/main.py`

Документируем как canonical backend reference для:

- analytics ingest / allowlist compatibility
- profile/admin API route correlation
- server-side logging alignment с profile/admin surfaces

## Acceptance / self-check

После doc-only изменений использовать такие команды самопроверки:

- `cd /opt/astro-project/frontend && npm exec tsc -- --noEmit`
- `cd /opt/astro-project && ./scripts/run_e2e.sh e2e/core-ux.spec.ts -g "profile"`

## Related docs

- `docs/READ_TELEMETRY_GUIDE.md`
- `docs/WEEK_TELEMETRY_GUIDE.md`
- `docs/CATALOG_CHECKOUT_RESUME_BANNER.md`
- `docs/QUALITY_TELEMETRY_RUNBOOK.md`
