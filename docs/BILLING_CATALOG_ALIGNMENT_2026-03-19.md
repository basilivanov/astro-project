# Billing/Catalog Alignment 2026-03-19

## Update 2026-03-20

Каноническая target-модель в `GRACE_SLICE_FORECAST_LADDER.md` не изменилась:

- `Week` = `subscription`
- `Month`, `Year`, `Natal`, `Solar`, `Synastry` = `one_off`
- `Horary` = `credits / one_off`

Но current runtime теперь уже split на два слоя, а не на один старый subscription-only path.

## Что реально есть сейчас

### 1. Default storefront по-прежнему subscription-first

- `/reports` и default `/create` продолжают показывать non-horary как `299₽/мес`.
- `Horary` остается разовым продуктом / credits flow.
- `frontend/e2e/billing-catalog-alignment.spec.ts` фиксирует этот контракт для всего catalog.
- `frontend/e2e/month-forecast-bridge-storefront.spec.ts`, `frontend/e2e/year-forecast-bridge-storefront.spec.ts` и `frontend/e2e/solar-return-bridge-storefront.spec.ts` отдельно фиксируют, что при bridge-flags off `month_forecast`, `year_forecast` и `solar_return` все еще живут на subscription storefront.

### 2. Narrow one-off bridge уже существует behind flags

- `frontend/lib/product-billing.ts` включает bridge для `natal_master`, `month_forecast`, `year_forecast` и `solar_return`.
- Bridge активируется только при одновременных:
  - `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME=true`
  - `ENABLE_PERSISTENT_CHECKOUT_SESSIONS=true`
- В этой ветке `/create` переключается на `product_type = report_type`, передает `return_path` и `draft_payload`, а после оплаты идет через `/billing/complete`.
- Для `solar_return` тот же bridge сохраняет `solar_current_location` через draft/session path и покрыт mock e2e на `/create` -> `/billing/complete` -> `/read`.

### 3. Backend для one-off больше не отсутствует

- `backend/app/services/one_off_entitlements.py` уже держит typed catalog и `report_entitlements`.
- `backend/app/services/billing.py` уже умеет `report_unlock`, persistent checkout sessions и idempotent webhook path.
- `/api/billing/sessions/{resume_token}` и `/api/billing/sessions/{resume_token}/resume` уже существуют.
- Status endpoint теперь является частью bridge-contract: отдает owner-scoped checkout session, parsed `draft_payload` и логирует `catalog.checkout_resume_ready` для `succeeded|resumed`.
- Webhook-ветка `report_unlock` теперь имеет явные contract/log events: `billing.report_unlock.contract.start`, `billing.report_unlock.missing_report_type`, `billing.report_unlock.bridge_granted`, `billing.checkout_bridge.entitlement_linked`.
- `/billing/complete` уже возвращает пользователя в `/create` или сразу в `/read/{id}`.
- `GET /api/users/me` уже отдает не только `report_unlocks`, но и structured `report_access` snapshot для canonical one-off типов.

Итог: default catalog честно остается subscription-first, но controlled bridge для `natal_master`, `month_forecast`, `year_forecast` и `solar_return` уже больше не является гипотезой, а реальным rollout slice.

## Почему текущий split безопасен

- Не происходит whole-catalog cutover, пока `synastry` не получил такой же bridge и catalog/storefront не выровнен с runtime целиком.
- Default storefront не обещает one-off там, где он еще не rolled out.
- Bridge включен только там, где уже есть:
  - persistent checkout session,
  - post-payment completion screen,
  - entitlement grant + consume,
  - targeted backend/e2e verification.

## Что еще не готово для полного catalog flip

1. `report_access` уже shipped в `/api/users/me`, но broader frontend/admin surfaces все еще частично завязаны на compatibility-bool `can_access_premium`.
2. `synastry` еще не получил такой же flagged bridge.
3. WebApp пока использует create-aligned resume через `GET /sessions` + `/api/reports/create`, а не direct `POST /resume`.
4. `ten_year_forecast` все еще не доведен до canonical commercial registry.

## Вывод для rollout

Текущий alignment на 2026-03-20 такой:

- default storefront = subscription-first;
- flagged `/create` bridge = one-off для `natal_master`, `month_forecast`, `year_forecast` и `solar_return`;
- `/api/users/me` уже отдает `report_access` + `report_unlocks` для runtime-aware gating;
- full catalog flip пока делать рано.
