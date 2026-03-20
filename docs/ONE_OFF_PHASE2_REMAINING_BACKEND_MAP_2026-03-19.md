# One-off Runtime: Remaining Gaps After Workflow Alignment + Completion Bridge

## Что уже закрылось в текущей wave

- `report_entitlements`, `billing_checkout_sessions`, `resolve_report_access()` и `consume_report_access()` уже работают в production-shaped runtime под флагами.
- `GET /api/users/me` уже больше не ограничен только `report_unlocks`:
  - profile отдает additive `report_access` snapshot через `build_report_access_snapshot(...)`;
  - `/create` уже использует его как primary runtime truth, сохраняя fallback на legacy поля для совместимости.
- Legacy `/api/workflows/report` и `/api/workflows/report/async` больше не висят полностью на bool/subscription path:
  - для one-off типов под флагами они уже используют тот же structured access/consume flow;
  - это покрыто `tests/test_legacy_workflow_one_off_alignment.py`.
- Completion/resume path больше не является только scaffold:
  - `/billing/complete` уже существует;
  - `/create` уже умеет поллить checkout session и запускать обычный `/api/reports/create`;
  - это покрыто backend resume tests и flagged e2e.
- Frontend bridge больше не ограничен только natal/month/year:
  - `solar_return` уже входит в `REPORT_UNLOCK_BRIDGE_PRODUCT_TYPES`;
  - flagged mock e2e покрывает `/create` -> `/billing/complete` -> `/read` и сохранение `solar_current_location`.
- Admin gift flow больше не выпадает из one-off runtime:
  - `grant(type="report")` создает `ReportEntitlement(source=ADMIN_GRANT)` и сразу consume-ит его в `Report`;
  - canonical alias normalization покрыта `tests/test_admin_grant_one_off_alignment.py`.

Итог: три старых P0-блокера уже закрыты. Current map ниже фиксирует только то, что реально осталось.

## Оставшиеся блокеры по приоритету

### 1. `report_access` уже есть, но его adoption еще не завершен

**Где:** `backend/app/main.py`, `backend/app/services/access_control.py`

**Что ломает:**

- Профиль уже отдает `report_access` и `report_unlocks`, но многие surfaces вне `/create` по-прежнему смотрят на `can_access_premium`.
- `check_user_access()` остается compatibility helper для legacy callers, а не замена structured per-report contract.
- При следующем cutover нужно явно решить, где `can_access_premium` остается legacy-only полем, а где UI полностью переходит на `report_access`.

### 2. Frontend bridge все еще не покрывает весь one-off catalog

**Где:** `frontend/lib/product-billing.ts`, `frontend/app/create/create-page-client.tsx`, `frontend/app/reports/page.tsx`

**Что ломает:**

- `solar_return` уже bridged behind flags, но `synastry` пока остается subscription-first и не имеет такого же flagged bridge.
- `/reports` catalog по умолчанию честно продает premium через `299₽/мес`, но канонический one-off catalog flip еще не случился.
- `ten_year_forecast` все еще вне ясного commercial registry.

### 3. WebApp path все еще create-aligned, а не direct-resume

**Где:** `frontend/app/create/create-page-client.tsx`, `frontend/app/billing/complete/billing-complete-page-client.tsx`, `backend/app/routers/billing.py`

**Что ломает:**

- Текущий рабочий path это `GET /api/billing/sessions/{token}` + обычный `/api/reports/create`.
- `POST /api/billing/sessions/{token}/resume` уже есть, но не является активным frontend path.
- Это не P0-баг, но следующая wave должна либо закрепить create-aligned strategy, либо явно перевести WebApp на direct resume.

### 4. Единый product registry еще не доведен до конца

**Где:** `backend/app/services/one_off_entitlements.py`, `backend/app/routers/billing.py`, `frontend/app/admin/users/[id]/page.tsx`

**Что ломает:**

- Billing/access runtime уже знает canonical one-off types.
- Admin и часть product surfaces до сих пор живут на отдельном наборе кодов и правил.
- Нет одного финального места, которое определяет canonical code, aliases, billing kind и rollout state для всех product surfaces.

## Рекомендуемый порядок добивки

1. Довести adoption `report_access` за пределы `/create` и объявить `can_access_premium` compatibility-only полем там, где это безопасно.
2. Расширить flagged bridge на `synastry`; отдельно решить судьбу `ten_year_forecast`.
3. Принять явное решение по frontend resume strategy: оставить create-aligned path или переключиться на direct `POST /resume`.
4. Довести единый product registry до явного owner-source для billing/access/admin surfaces.
5. Только после этого выключать legacy subscription fallback и делать broader catalog flip.

## Минимальный тестовый профиль для следующего pass

- Backend:
  - coverage на consumer-paths, которые используют `/api/users/me.report_access`
  - coverage на final registry normalization across admin/billing/access
- E2E:
  - one-off bridge для `synastry`
  - storefront/default-subscription coverage для bridged `solar_return`
  - already-paid reopen `/create?type=...` для всех bridged one-off типов
  - direct `/resume` path, только если он станет active frontend contract
