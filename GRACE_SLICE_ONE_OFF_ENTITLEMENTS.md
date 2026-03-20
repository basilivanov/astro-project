# GRACE Slice: True One-Off Report Entitlements

**Статус:** `natal_master` + `month_forecast` + `year_forecast` + `solar_return` flagged one-off e2e synced; broader one-off rollout still gated  
**Дата:** 2026-03-20  
**Язык:** RU  
**Опора на код:** `backend/app/routers/billing.py`, `backend/app/services/billing.py`, `backend/app/services/access_control.py`, `backend/app/services/one_off_entitlements.py`, `backend/app/main.py`, `backend/app/models.py`, `backend/app/migrations_v2.py`, `backend/app/core/config_business.py`, `backend/app/core/feature_flags.py`, `frontend/app/create/page.tsx`, `frontend/app/create/create-page-client.tsx`, `frontend/app/billing/complete/page.tsx`, `frontend/app/billing/complete/billing-complete-page-client.tsx`, `frontend/app/read/[id]/page.tsx`, `frontend/app/reports/page.tsx`, `frontend/lib/product-billing.ts`, `tests/test_one_off_entitlements_scaffold.py`, `tests/test_billing_checkout_sessions.py`, `tests/test_billing_checkout_resume.py`, `tests/test_one_off_access_runtime.py`, `tests/test_one_off_runtime_smoke.py`, `tests/test_legacy_workflow_one_off_alignment.py`, `tests/test_admin_grant_one_off_alignment.py`, `frontend/e2e/billing-mock.spec.ts`, `frontend/e2e/month-forecast-bridge-storefront.spec.ts`, `frontend/e2e/year-forecast-bridge-storefront.spec.ts`, `frontend/e2e/solar-return-bridge-storefront.spec.ts`, `frontend/e2e/admin.entitlements.spec.ts`, `frontend/e2e/billing-catalog-alignment.spec.ts`, `frontend/e2e/report-create.spec.ts`, `docs/BILLING_CATALOG_ALIGNMENT_2026-03-19.md`, `GRACE_SLICE_FORECAST_LADDER.md`

## 1. Цель slice

Зафиксировать уже ship-нутый backend phase-2 для настоящих one-off entitlement на:

- `month_forecast`
- `year_forecast`
- `natal_master`
- `solar_return`
- `synastry`

С обязательным покрытием:

- storage/state model;
- typed catalog / feature-flag contract;
- webhook branching;
- post-payment resume;
- access-control и consumption semantics;
- migration/rollout рисков.

Этот документ фиксирует current reality:

- `natal_master`, `month_forecast`, `year_forecast` и `solar_return` уже имеют реальный end-to-end one-off bridge behind feature flags;
- `GET /api/users/me` уже отдает additive `report_access` alongside `report_unlocks`;
- legacy `/api/workflows/report*` уже переведены на structured access/consume path для one-off типов под флагами;
- остальной one-off catalog все еще остается rollout-срезом и не считается полностью переведенным.

## 2. Что реально есть в коде сейчас

### 2.1 Billing runtime и typed contract

`backend/app/routers/billing.py`

- `POST /api/billing/pay` принимает `product_type` или `pack_id`.
- Для `subscription` всегда берет `SUBSCRIPTION_PRICE = 299`.
- Для report-like продуктов берет цену из `REPORT_PRICES[...]` и через `resolve_catalog_product(...)` различает `subscription`, `credits`, `report_unlock`.
- Если `ENABLE_PERSISTENT_CHECKOUT_SESSIONS=true`, создает локальную `billing_checkout_session`, сохраняет `return_path`/`draft_payload`, кладет `checkout_session_id` в metadata и строит `return_url` как `/billing/complete?checkout=...`.
- Уже есть `GET /api/billing/sessions/{resume_token}` для чтения статуса своей checkout session.
- Уже есть `POST /api/billing/sessions/{resume_token}/resume` для idempotent server-side resume `report_unlock` session через обычный B2C create workflow.
- В mock-режиме webhook handler вызывается синхронно прямо из роутера.

`backend/app/services/billing.py`

- `create_checkout_session(...)` уже пишет persistent checkout session с `resume_token`, `idempotence_key`, `return_path` и `draft_payload`.
- `create_payment(...)` уже умеет работать с `return_url` и `idempotence_key` из session.
- `handle_payment_succeeded(...)` уже расщеплен на три ветки:
  - `subscription`
  - `credits`
  - `report_unlock`
- При `billing_kind=report_unlock` и `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME=true` runtime выдает `report_entitlement`, линкует его к checkout session и не трогает `subscription_active_until`.
- Повторные webhook/payload по тому же `payment_id` или уже-success session обрабатываются идемпотентно.
- `handle_payment_canceled(...)` уже переводит checkout session в `canceled`.

`backend/app/services/one_off_entitlements.py`

- уже содержит typed contract:
  - `BillingKind`
  - `CheckoutSessionStatus`
  - `EntitlementStatus`
  - `AccessGrantSource`
  - `AccessDecision`
- уже содержит backend `PRODUCT_CATALOG` с тремя billing-семантиками:
  - `subscription`
  - `credits`
  - `report_unlock`
- фиксирует `ONE_OFF_REPORT_TYPES` для `natal_master`, `month_forecast`, `year_forecast`, `solar_return`, `synastry`.

### 2.2 Access control runtime

`backend/app/services/access_control.py`

- `check_user_access(...)` и `consume_access_if_needed(...)` остаются legacy boolean helpers для старых caller-ов.
- Horary живет отдельно:
  - 1 free/week для активной подписки;
  - потом `CRD` через `transactions`.
- Structured `resolve_report_access(...)` и `consume_report_access(...)` уже живут в runtime `access_control.py`.
- Для one-off типов при `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME=true` runtime:
  - допускает legacy subscription access, если `LEGACY_PREMIUM_SUBSCRIPTION_ACCESS=true`;
  - иначе ищет active entitlement и возвращает `AccessDecision`;
  - при consume атомарно проставляет `reports.access_source`, `reports.entitlement_id`, `reports.checkout_session_id`, переводит entitlement в `consumed` и session в `resumed`.

### 2.3 Report creation runtime

`backend/app/main.py`

- `/api/reports/create` уже вызывает `resolve_report_access(...)` до создания `Report` и `consume_report_access(...)` после создания строки отчета.
- Для one-off flow linkage-поля `Report.access_source`, `Report.entitlement_id`, `Report.checkout_session_id` уже реально заполняются.
- `Report.input_payload` уже хранит snapshot входных данных.
- `GET /api/reports/{id}` проверяет только ownership `report.user_id == user.id`; read-access не зависит от активной подписки.
- `GET /api/users/me` уже отдает `report_unlocks`, собранные через `build_report_unlock_snapshot(...)`, причем снапшот zero-filled по известным one-off типам.
- Тот же `GET /api/users/me` уже отдает `report_access`, собранный через `build_report_access_snapshot(...)`, и `feature_flags`, так что frontend может выбирать bridge branch без отдельного config endpoint.

Это важно: уже сегодня чтение готового отчета отделено от entitlement. Значит one-off entitlement должен тратиться на `create`, а не на `read`.

### 2.4 Frontend/runtime coupling

`frontend/app/reports/page.tsx` + `frontend/lib/product-billing.ts`

- storefront по умолчанию все еще subscription-first для non-horary:
  - `299₽/мес` для premium catalog;
  - `199₽` только для horary;
- narrow bridge сознательно ограничен `natal_master`, `month_forecast`, `year_forecast` и `solar_return` через `REPORT_UNLOCK_BRIDGE_PRODUCT_TYPES`.

`frontend/app/create/create-page-client.tsx`

- Для большинства non-horary по-прежнему отправляет `product_type = "subscription"`.
- Для `natal_master`, `month_forecast`, `year_forecast` и `solar_return`, когда одновременно включены `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME` и `ENABLE_PERSISTENT_CHECKOUT_SESSIONS`, переключается на реальный one-off paywall:
  - отправляет `product_type = report_type`;
  - передает `return_path` и `draft_payload`;
  - читает `/api/users/me.report_access`, `/api/users/me.report_unlocks` и `feature_flags`;
  - показывает generate CTA вместо pay CTA, если unlock уже есть.
- Для `solar_return` тот же resume path сохраняет `solar_current_location` через session draft и не теряет его при автозапуске `POST /api/reports/create`.
- При возврате с `checkout=...` поллит `GET /api/billing/sessions/{resume_token}` и после `status = succeeded` запускает обычный `/api/reports/create`.

`frontend/app/billing/complete/billing-complete-page-client.tsx`

- route уже существует;
- поллит `GET /api/billing/sessions/{resume_token}`;
- если `resumed_report_id` уже есть, сразу уводит в `/read/{id}`;
- иначе возвращает пользователя в `/create?type={session.report_type}&checkout=...`, где срабатывает обычный create-flow.

`frontend/app/read/[id]/page.tsx`

- read surface уже показывает `report.access_source` в meta pills;
- для one-off bridge это делает видимым факт, что отчет открылся через `report_entitlement`.

Важно: backend `POST /api/billing/sessions/{resume_token}/resume` уже существует и покрыт backend-тестами, но текущий WebApp bridge для `natal_master`, `month_forecast`, `year_forecast` и `solar_return` идет через `GET /sessions` + обычный `/api/reports/create`, чтобы consume semantics оставались выровненными с главным workflow.

### 2.5 Что уже ship-нуто в phase 1 / phase 2

- `backend/app/models.py` и `backend/app/migrations_v2.py` уже добавили:
  - `report_entitlements`;
  - `billing_checkout_sessions`;
  - linkage-поля в `reports`.
- `backend/app/core/feature_flags.py` уже добавил rollout-флаги:
  - `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME=false` по умолчанию;
  - `ENABLE_PERSISTENT_CHECKOUT_SESSIONS=false` по умолчанию;
  - `LEGACY_PREMIUM_SUBSCRIPTION_ACCESS=true` по умолчанию.
- `tests/test_one_off_entitlements_scaffold.py` проверяет metadata/schema presence, typed catalog и safe defaults rollout-флагов.
- `tests/test_billing_checkout_sessions.py` проверяет persistent checkout sessions, return URL/resume metadata, cancel handling и idempotent `report_unlock` grant.
- `tests/test_billing_checkout_resume.py` проверяет idempotent `POST /api/billing/sessions/{resume_token}/resume` и linkage в `Report`.
- `tests/test_one_off_access_runtime.py` проверяет entitlement-based access decision, consume/linking в `Report` и zero-filled unlock snapshot.
- `tests/test_one_off_runtime_smoke.py` проверяет HTTP path `pay -> webhook -> /api/users/me.report_unlocks -> create -> consume -> second create = 402` и отдельный `/api/users/me.report_access` snapshot contract.
- `tests/test_legacy_workflow_one_off_alignment.py` проверяет, что `/api/workflows/report` и `/api/workflows/report/async` уже потребляют one-off entitlement под флагами и сохраняют legacy subscription behavior при выключенном runtime.
- `frontend/e2e/billing-mock.spec.ts` уже проверяет direct unlock indicator, `/billing/complete` bridge и факт, что `read` отдает `access_source = report_entitlement` для `natal_master`, `month_forecast`, `year_forecast` и `solar_return`.
- `frontend/e2e/month-forecast-bridge-storefront.spec.ts`, `frontend/e2e/year-forecast-bridge-storefront.spec.ts` и `frontend/e2e/solar-return-bridge-storefront.spec.ts` фиксируют обратную сторону rollout: при bridge-flags off `month_forecast`, `year_forecast` и `solar_return` все еще остаются subscription-first на `/reports` и `/create`.
- `tests/test_admin_grant_one_off_alignment.py` проверяет, что `grant(type="report")` создает и сразу consume-ит `ReportEntitlement(source=ADMIN_GRANT)` с canonical report type normalization.
- `frontend/e2e/admin.entitlements.spec.ts` держит UI-подтверждение того, что admin gift flow показывает canonical `synastry` после выдачи отчета.
- `frontend/e2e/report-create.spec.ts` держит stable `data-testid` на premium create/read path и на user-input срезах `synastry` / `solar_return`, чтобы billing bridge не ломал базовый create runtime.

### 2.6 Уже существующие ручные обходы

`backend/app/main.py`:

- `/api/admin/users/{id}/subscription/add-days`
- `/api/admin/users/{id}/grant`

Теперь `grant(type="report")` больше не обходит entitlement model:

- backend сначала создает `ReportEntitlement(source=ADMIN_GRANT)`;
- затем тот же grant flow atomically consume-ит entitlement в созданный `Report`;
- validator/admin normalizer приводит legacy alias values к canonical `synastry` и `solar_return` до consume path.

## 3. Что еще остается rollout gap

На 2026-03-20 narrow `natal_master` + `month_forecast` + `year_forecast` + `solar_return` bridge уже реально работает end-to-end behind flags. Canonical product direction остается таким:

- `Week` = `subscription`
- `Month/Year/Natal/Solar/Synastry` = `one_off`
- `Horary` = `credits / one_off`

Unlock counters в `/api/users/me`, additive `report_access`, `billing complete` screen, read-level `access_source`, legacy workflow alignment и admin entitlement-first grant больше не являются rollout gap для `natal_master` / `month_forecast` / `year_forecast` / `solar_return`. Остаточные разрывы теперь такие:

1. bridge намеренно ограничен `natal_master`, `month_forecast`, `year_forecast` и `solar_return`; `synastry` все еще живет в subscription-first frontend/catalog;
2. `/reports` storefront и generic pricing helper остаются subscription-first для premium catalog; реальный one-off flip пока происходит только в profile-aware ветке `/create` для `natal_master` / `month_forecast` / `year_forecast` / `solar_return`;
3. safe-default флаги все еще выключены по умолчанию:
   - `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME=false`;
   - `ENABLE_PERSISTENT_CHECKOUT_SESSIONS=false`;
   - `LEGACY_PREMIUM_SUBSCRIPTION_ACCESS=true`;
4. текущий WebApp flow использует `GET /api/billing/sessions/{resume_token}` + обычный `/api/reports/create`; backend `/resume` существует, но не является активным frontend path;
5. `/api/users/me` уже экспортирует per-report `report_access`, но многие surfaces все еще держат `can_access_premium` как compatibility gate;
## 4. Ключевые архитектурные решения

### 4.1 One-off access = отдельный entitlement, не `transactions`, не `Report.paid`

Решение:

- ввести отдельную таблицу `report_entitlements`;
- одна покупка one-off = одна entitlement единица;
- entitlement живет независимо от конкретного `Report`, пока не будет consumed.

Почему не `transactions`:

- `transactions` сейчас это финансовый лог, а не access-state;
- через нее неудобно выразить `active -> consumed -> refunded/revoked`;
- нельзя надежно привязать “какая именно покупка открыла какой именно report”.

Почему не перегружать `Report.paid`:

- `paid` уже сейчас двусмысленный UI-флаг;
- report появляется только после успешного create;
- entitlement нужен раньше, чем существует `Report`.

### 4.2 Payment redirect должен опираться на persistent checkout session

Решение:

- ввести отдельную таблицу `billing_checkout_sessions`;
- `POST /api/billing/pay` сначала пишет локальную session, потом вызывает YooKassa;
- `return_url` содержит `resume_token`, а не просто `WEBAPP_URL`.

Почему не хранить state только во frontend:

- Telegram WebApp легко теряет local/session state при redirect;
- webhook приходит асинхронно и не обязан совпадать по времени с возвратом пользователя;
- без persistent session нельзя сделать idempotent resume.

### 4.3 Consumption происходит в момент `create report`, а не в webhook

Решение:

- webhook на one-off покупку только выдает `active entitlement`;
- entitlement списывается только при успешном создании `Report` записи;
- failed report не должен требовать повторной оплаты, потому что у пользователя уже есть `report_id` и существующий regenerate flow.

### 4.4 Resume после оплаты это convenience поверх entitlement, а не единственный путь

Решение:

- после оплаты пользователь получает `active entitlement`, даже если не нажал resume сразу;
- `/api/users/me` должен уметь показать доступные per-report unlocks;
- `/create?type=...` должен распознавать, что entitlement уже есть, и предлагать генерацию, а не повторную оплату.

Это защищает от кейса “оплата прошла, пользователь закрыл WebApp”.

### 4.5 Переход с legacy subscription access должен быть feature-flagged

Решение:

- новый entitlement runtime вводится отдельно от немедленного отключения старого `subscription_active_until` для premium reports;
- временный флаг:
  - `LEGACY_PREMIUM_SUBSCRIPTION_ACCESS=true`
- пока флаг включен, активная подписка может по-прежнему давать доступ к one-off типам;
- когда storefront и support готовы, флаг выключается.

Иначе rollout легко превратится в product regression для текущих подписчиков.

## 5. Целевая data model

### 5.1 `report_entitlements`

Эта схема уже добавлена в `backend/app/models.py` и `apply_v6_migrations()`; ниже зафиксирован канон полей для rollout-а.

Минимальная таблица:

```text
report_entitlements
- id UUID PK
- user_id UUID NOT NULL FK users.id
- report_type VARCHAR(64) NOT NULL
- status VARCHAR(32) NOT NULL
  active | consumed | refunded | revoked | expired
- source VARCHAR(32) NOT NULL
  payment | admin_grant | migration | support
- checkout_session_id UUID NULL FK billing_checkout_sessions.id
- granted_transaction_id UUID NULL FK transactions.id
- consumed_report_id UUID NULL FK reports.id
- scope_key VARCHAR(128) NULL
- notes TEXT NULL
- created_at TIMESTAMPTZ NOT NULL
- updated_at TIMESTAMPTZ NOT NULL
- consumed_at TIMESTAMPTZ NULL
- revoked_at TIMESTAMPTZ NULL
- expires_at TIMESTAMPTZ NULL
```

Индексы:

- `(user_id, report_type, status, created_at)`
- unique `(consumed_report_id)` where `consumed_report_id is not null`
- optional partial index on active rows:
  - `(user_id, report_type, created_at)` where `status = 'active'`

Замечания:

- `scope_key` в v1 можно не использовать.
- Поле оставляется на будущее под кейсы вроде `year_forecast:2027` или promo/grandfathering cohort.
- JSONB здесь не обязателен. Текущий repo и тесты уже широко используют `TEXT` для serialized state; для additive runtime migration это безопаснее.

### 5.2 `billing_checkout_sessions`

Эта схема уже добавлена в `backend/app/models.py` и `apply_v6_migrations()`; runtime `billing.py` уже пишет в нее записи, когда включен `ENABLE_PERSISTENT_CHECKOUT_SESSIONS`.

Минимальная таблица:

```text
billing_checkout_sessions
- id UUID PK
- user_id UUID NOT NULL FK users.id
- provider VARCHAR(32) NOT NULL
  yookassa | mock
- status VARCHAR(32) NOT NULL
  created | pending | succeeded | canceled | failed | expired | resumed
- billing_kind VARCHAR(32) NOT NULL
  subscription | credits | report_unlock
- product_code VARCHAR(64) NOT NULL
- report_type VARCHAR(64) NULL
- pack_id VARCHAR(64) NULL
- amount NUMERIC(10,2) NOT NULL
- currency VARCHAR(3) NOT NULL
- provider_payment_id VARCHAR(255) NULL
- provider_status VARCHAR(64) NULL
- idempotence_key VARCHAR(64) NULL
- resume_token VARCHAR(64) NOT NULL UNIQUE
- return_path VARCHAR(255) NULL
- draft_payload TEXT NULL
- entitlement_id UUID NULL FK report_entitlements.id
- resumed_report_id UUID NULL FK reports.id
- error_code VARCHAR(64) NULL
- error_message TEXT NULL
- created_at TIMESTAMPTZ NOT NULL
- updated_at TIMESTAMPTZ NOT NULL
- succeeded_at TIMESTAMPTZ NULL
- resumed_at TIMESTAMPTZ NULL
- canceled_at TIMESTAMPTZ NULL
```

Индексы:

- unique `(provider_payment_id)` where not null
- `(user_id, status, created_at desc)`
- `(resume_token)`

### 5.3 Минимальные расширения `reports`

Поля уже добавлены в `Report`, и phase-2 runtime уже заполняет их на entitlement-path через `consume_report_access(...)`.

Рекомендуемые additive поля:

```text
reports
- access_source VARCHAR(32) NULL
  subscription | trial | credits | report_entitlement | admin_grant | bypass
- entitlement_id UUID NULL FK report_entitlements.id
- checkout_session_id UUID NULL FK billing_checkout_sessions.id
```

`paid` оставить для backward compatibility UI, но не использовать как источник истины для entitlement логики.

## 6. Catalog/product contract

Текущий split между:

- `backend/app/core/config_business.py`
- `frontend/lib/product-billing.ts`
- runtime ветками в `billing.py` / `access_control.py`

уже однажды дал drift.

Что уже есть:

- backend map уже существует как `PRODUCT_CATALOG` в `backend/app/services/one_off_entitlements.py`;
- frontend витрина все еще держит отдельный display-layer в `frontend/lib/product-billing.ts`;
- именно поэтому drift уже уменьшен в storefront, но полностью не закрыт на уровне единого source of truth.

Следующий шаг:

- ввести единый backend product catalog map, из которого выводятся:
  - price;
  - `billing_kind`;
  - `report_type`;
  - paywall text;
  - access semantics.

Минимальная каноническая матрица:

| Product | billing_kind | access semantic |
| :--- | :--- | :--- |
| `subscription` | `subscription` | доступ к `week_forecast`, плюс legacy bundle через feature flag |
| `horary_pack_*` | `credits` | пополнение `CRD` |
| `natal_master` | `report_unlock` | 1 entitlement на `natal_master` |
| `month_forecast` | `report_unlock` | 1 entitlement на `month_forecast` |
| `year_forecast` | `report_unlock` | 1 entitlement на `year_forecast` |
| `solar_return` | `report_unlock` | 1 entitlement на `solar_return` |
| `synastry` | `report_unlock` | 1 entitlement на `synastry` |

`ten_year_forecast`:

- storage модель его поддерживает;
- rollout этого типа можно отложить отдельно.

## 7. Текущий access-control контракт

Phase 2 уже добавил structured contract в runtime, но legacy boolean helpers пока сохраняются для старых caller-ов.

### 7.1 Structured decision уже есть

Текущий сервисный контракт:

```text
resolve_report_access(user, report_type, db) -> AccessDecision
consume_report_access(user, report, db, decision=...) -> AccessDecision
```

Типовой ответ:

```json
{
  "allowed": true,
  "granted_via": "report_entitlement",
  "report_type": "month_forecast",
  "entitlement_id": "uuid-or-null",
  "remaining_unlocks": 1,
  "reason_code": "ok"
}
```

`granted_via`:

- `bypass`
- `free`
- `subscription`
- `trial`
- `credits`
- `report_entitlement`

### 7.2 Правила по report type

`week_forecast`

- `subscription` / `trial`
- не one-off в этом slice

`horary*`

- free weekly quota for active sub;
- затем `CRD`;
- этот path остается на legacy/credits модели.

`month_forecast`, `year_forecast`, `natal_master`, `solar_return`, `synastry`

- if bypass -> allow;
- else if `LEGACY_PREMIUM_SUBSCRIPTION_ACCESS=true` и активна подписка -> allow;
- else if есть active `report_entitlement` нужного типа -> allow;
- else deny with `reason_code=payment_required`.

### 7.3 Current consumption semantics

Когда `/api/reports/create` идет через phase-2 path:

- для subscription/trial ничего не списываем;
- для credits поведение как сейчас;
- для one-off:
  - выбирается active entitlement;
  - entitlement переводится в `consumed`;
  - `consumed_report_id` записывается в entitlement;
  - `reports.access_source`, `reports.entitlement_id`, `reports.checkout_session_id` заполняются;
  - связанная checkout session получает `resumed_report_id` и статус `resumed`.

Если generation позже падает:

- entitlement не возвращается автоматически;
- пользователь продолжает через существующий `POST /api/reports/{id}/regenerate`.

## 8. Текущий webhook/session контракт

### 8.1 Что уже ship-нуто

`handle_payment_succeeded(...)` уже маршрутизирует:

1. `subscription`
2. `credits`
3. `report_unlock`

Routing идет так:

- сначала checkout session из `metadata.checkout_session_id`;
- если это legacy payment без session, остается fallback в старую логику.

### 8.2 Идемпотентность

Phase-2 path уже гарантирует:

- duplicate webhook для уже `succeeded/resumed` session не удваивает обработку;
- `Transaction(type='payment')` пишется один раз;
- `report_entitlement` для одной checkout session создается один раз.

### 8.3 Отмена, resume и remaining gap

Уже есть:

- `payment.canceled` -> session `canceled`;
- provider create error -> session `failed`.
- отдельный backend resume endpoint;
- frontend completion screen `/billing/complete`;
- read-surface marker `access_source`.

Все еще отсутствует:

- явный provider webhook path для `failed/expired` beyond current create/cancel handling;
- webapp wiring на `POST /api/billing/sessions/{resume_token}/resume` вместо текущего `GET /sessions` + `/create` path;
- более широкий frontend rollout beyond `natal_master`, `month_forecast`, `year_forecast` и `solar_return`.

## 9. Post-payment resume

### 9.1 Уже реализованные backend pieces

Сейчас backend уже умеет:

- создавать persistent checkout session с `resume_token`;
- сохранять `return_path` и `draft_payload`;
- прокидывать `checkout_session_id`, `billing_kind`, `report_type` в provider metadata;
- строить `return_url = {WEBAPP_URL}/billing/complete?checkout={resume_token}`;
- отдавать `GET /api/billing/sessions/{resume_token}`;
- выдавать entitlement до возвращения пользователя в WebApp;
- показывать активные unlock-и и per-report access truth через `/api/users/me.report_unlocks` + `/api/users/me.report_access`.

### 9.2 Что еще не доведено до broader end-to-end

Уже есть:

- frontend route `/billing/complete`;
- backend `POST /api/billing/sessions/{resume_token}/resume`;
- create/paywall branch для `natal_master`, `month_forecast`, `year_forecast` и `solar_return`, который использует `report_access[type]` с fallback на `report_unlocks[type]`;
- frontend повторный вход в `/create?type=natal_master`, `/create?type=month_forecast`, `/create?type=year_forecast` или `/create?type=solar_return` как resume UX вместо повторной продажи подписки.

Все еще pending:

- распространить ту же механику на `synastry`;
- синхронизировать catalog-level storefront с flag-aware one-off rollout;
- решить, должен ли WebApp в будущем вызывать `POST /resume` напрямую или оставаться на create-aligned path.

### 9.3 Важное product-правило

Resume не должен быть обязательным в ту же сессию.

Если пользователь:

- закрыл WebApp;
- вернулся через день;
- открыл `/create?type=natal_master`, `/create?type=month_forecast`, `/create?type=year_forecast` или `/create?type=solar_return`

он должен увидеть “доступ уже оплачен” и получить кнопку генерации без повторной оплаты.

## 10. Минимальный delta от текущего состояния

### 10.1 Backend уже есть

- `POST /api/billing/pay` уже принимает `return_path` и `draft_payload`;
- `GET /api/billing/sessions/{resume_token}` уже ship-нут;
- `POST /api/billing/sessions/{resume_token}/resume` уже ship-нут;
- `GET /api/users/me` уже отдает:

```json
{
  "report_unlocks": {
    "natal_master": 1,
    "month_forecast": 0,
    "year_forecast": 0,
    "solar_return": 0,
    "synastry": 0
  },
  "report_access": {
    "natal_master": {
      "allowed": true,
      "granted_via": "report_entitlement",
      "remaining_unlocks": 1,
      "reason_code": "ok",
      "legacy_subscription_applied": false
    }
  }
}
```

- `/api/reports/create` уже использует structured access decision и link-ит entitlement/session в `Report`.

### 10.2 Backend remaining delta

- P0 backend delta для flagged runtime отсутствует;
- `/api/workflows/report*` уже используют тот же structured access/consume path для one-off типов под флагами;
- опциональный следующий шаг: перевести WebApp на `POST /api/billing/sessions/{resume_token}/resume`, если понадобится отдельный server-side shortcut;
- convergence еще нужна для broader `report_access` adoption и provider `failed/expired` handling.

### 10.3 Frontend remaining delta

- расширить bridge за пределы `natal_master`, `month_forecast`, `year_forecast` и `solar_return`;
- синхронизировать `/reports` catalog и helper copy с тем, что `natal_master`, `month_forecast`, `year_forecast` и `solar_return` уже могут идти как one-off behind flags;
- решить, оставлять ли create-aligned bridge как основной путь или переключать frontend на `POST /resume`.
- сохранить текущие stable `data-testid` на `/create` и `/billing/complete`, чтобы расширение rollout-а не деградировало e2e hardening.

## 11. Остаточный implementation surface

Минимально затрагиваемые файлы следующего pass, если расширять bridge дальше:

- `backend/app/routers/billing.py`
- `backend/app/main.py`
- `frontend/app/create/page.tsx`
- `frontend/app/billing/complete/page.tsx`
- `frontend/app/reports/page.tsx`
- `frontend/lib/product-billing.ts`
- admin flow для convergence с entitlement-моделью

Что не нужно переписывать ради этого slice:

- report reading endpoints;
- report rendering pipeline;
- report chunk storage;
- existing horary credits model;
- scheduler логика подписок.

## 12. Migration и rollout риски

### 12.1 In-flight legacy оплаты

Нужен legacy fallback:

- если metadata не содержит `checkout_session_id`, payment обрабатывается по старому пути;
- fallback нельзя удалять, пока не вымыты старые initiated платежи.

### 12.2 Product regression для текущих подписчиков

`LEGACY_PREMIUM_SUBSCRIPTION_ACCESS=true` по умолчанию пока обязателен, иначе активные подписчики потеряют обещанный premium access раньше storefront cutover.

### 12.3 Synastry / Solar input flow

Это уже не чистая entitlement проблема:

- `synastry` frontend уже собирает `partner_birth_date`, `partner_birth_location` и optional `partner_name`, но softer unknown-birth-time mode все еще не доведен;
- `solar_return` уже имеет явный `solar_current_location`, но fallback на current/birth location остается deliberate convenience behavior.

### 12.4 Admin grant alignment

Primary admin grant path уже выровнен с entitlement-моделью:

- backend создает `ReportEntitlement(source=ADMIN_GRANT)` и consume-ит его в тот же `Report`;
- admin UI использует canonical product codes `synastry`, `solar_return`, `year_forecast`;
- legacy aliases остаются только как compatibility input в normalizer.

### 12.5 Runtime migration pattern

Проект по-прежнему живет на additive runtime migrations без полноценного Alembic-потока, поэтому:

- таблицы и поля должны оставаться additive;
- destructive schema changes в этом slice не допускаются;
- rollout должен переживать mixed code versions.

## 13. Рекомендуемый остаточный порядок

### Phase 1. Storage + session plumbing

- ship-нуто.

### Phase 2. Entitlement-aware backend access

- ship-нуто для backend под feature flags, включая admin entitlement-first grant alignment.

### Phase 3. Frontend resume and catalog switch

- partially ship-нуто:
  - `/billing/complete`;
  - `/create` с `product_type = "natal_master"`, `product_type = "month_forecast"`, `product_type = "year_forecast"` и `product_type = "solar_return"` under bridge flags;
  - paywall/generate branch по `report_access` + `report_unlocks` для `natal_master`, `month_forecast`, `year_forecast` и `solar_return`;
- pending:
  - тот же bridge для `synastry`;
  - catalog-level copy/pricing alignment beyond the narrow bridge.

### Phase 4. Legacy access cutover

- pending:
  - feature flag rollout;
  - support/runbook;
  - отключение subscription access для one-off типов.

## 14. Минимальный test pack для текущего slice

Backend:

- `PYTHONPATH=. python3 -m pytest tests/test_one_off_entitlements_scaffold.py`
- `PYTHONPATH=. python3 -m pytest tests/test_billing_checkout_sessions.py`
- `PYTHONPATH=. python3 -m pytest tests/test_billing_checkout_resume.py`
- `PYTHONPATH=. python3 -m pytest tests/test_one_off_access_runtime.py`
- `PYTHONPATH=. python3 -m pytest tests/test_one_off_runtime_smoke.py`
- `PYTHONPATH=. python3 -m pytest tests/test_admin_grant_one_off_alignment.py`

Frontend:

- `E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge natal one-off mock checkout through billing complete to read"`
- `E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge month forecast one-off mock checkout through billing complete to read"`
- `E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge year forecast one-off mock checkout through billing complete to read"`
- `E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge solar return one-off mock checkout through billing complete to read"`
- `E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should resume direct mock checkout from billing complete to read"`
- `./scripts/run_e2e.sh e2e/month-forecast-bridge-storefront.spec.ts`
- `./scripts/run_e2e.sh e2e/year-forecast-bridge-storefront.spec.ts`
- `./scripts/run_e2e.sh e2e/solar-return-bridge-storefront.spec.ts`
- `./scripts/run_e2e.sh e2e/admin.entitlements.spec.ts -g "should add unlimited subscription and grant report"`

Что еще понадобится после broader frontend cutover:

- E2E one-off pay -> return -> resume -> `/read/{id}` для `synastry`;
- delayed webhook on completion screen вне mock path;
- already-paid user reopening `/create?type=...` and seeing generate CTA для всех one-off типов, а не только для `natal_master` / `month_forecast` / `year_forecast` / `solar_return`.

## 15. Текущее решение

Для этого проекта правильная модель one-off доступа уже не только partially-implemented в backend, но и реально видна пользователю в narrow `natal_master` / `month_forecast` / `year_forecast` / `solar_return` slice behind flags:

- one-off покупка может создать persistent `billing_checkout_session`;
- webhook уже выдает `report_entitlement`, но не создает report автоматически;
- report creation уже atomically consume-ит entitlement;
- `/api/users/me` уже показывает оставшиеся unlock-и и per-report access truth;
- `/billing/complete` уже возвращает пользователя обратно в create/read;
- admin gifts для one-off типов теперь проходят через тот же entitlement-first consume path;
- готовые отчеты читаются по ownership как и сейчас и показывают `access_source = report_entitlement`.

Полный rollout все еще упирается не в backend-примитивы, а в расширение этого bridge на остальные one-off продукты, синхронизацию catalog-level UX и последующее отключение legacy subscription access.
