# CatalogCheckoutResumeBanner

`CatalogCheckoutResumeBanner` (`frontend/components/catalog/catalog-checkout-resume.tsx`) — общий resume surface для возврата пользователя в незавершённый checkout flow из catalog/history/week/read/billing экранов.

## Что делает banner

- Показывается только при наличии `checkout` query param / `checkoutToken`.
- При `isReady && initData` синхронизирует состояние через `GET /api/billing/sessions/:token` с `X-Telegram-Auth`.
- Для `mock=1` без `runtime=1` не ходит в backend: сразу переводит баннер в `succeeded` с mock report type.
- Для `runtime=1` всегда использует реальный runtime fetch, даже если включён `mock=1`.
- Сохраняет `mock=1` и `runtime=1` в `resumeHref`, чтобы возврат шёл в тот же execution mode.
- Даёт три действия: `Назад`, `Вернуться`, `Отменить`.

## Status flow

- `checking` → начальное состояние до sync.
- `pending|created` → copy: продолжить оплату.
- `succeeded|resumed` → copy: оплата уже прошла, можно завершить запуск.
- `canceled` → copy: оформление отменено, можно попробовать снова.
- `failed` → copy: оплата завершилась ошибкой.
- `unauthorized` → нет Telegram init data.
- `error` → fetch/session sync недоступен.

Polling продолжается только для `pending` и останавливается на финальных статусах.

## Entrypoints и surface

Компонент не выбирает surface сам — его задаёт host page.

- Catalog: `surface="catalog"`, `entryPoint="catalog-inline-resume"` в `frontend/app/reports/page.tsx`.
- History: `surface="history"`, `entryPoint="history-inline-resume"` в `frontend/app/reports/history/page.tsx`.
- Week: `surface="week"`, `entryPoint="week-resume-banner"` в `frontend/app/week/page.tsx`.
- Read: `surface="read"`, локальный read CTA flow использует `entry_point="read_resume_banner"`; сам shared banner рендерится в read surface через `CatalogCheckoutResumeBanner`.
- Billing complete: `surface="billing"`, `entryPoint="billing-complete-resume-banner"`.

## Flow ID и correlation

- Shared catalog analytics helper по умолчанию работает в flow family `FLOW-FORECAST-CATALOG` (`frontend/components/catalog/catalog-analytics.ts`).
- При bootstrap баннера вызывается `startCatalogCorrelation("catalog_checkout_resume")`, поэтому `catalog.checkout_resume_*` события получают `flow_id="catalog_checkout_resume"` и новый `correlation_id` для resume session.
- После bootstrap в analytics context сохраняются:
  - `checkout_token`
  - `correlation_id`
  - surface/entry point envelope через payload конкретного события.

## Telemetry contract

Banner отправляет namespace `catalog.checkout_resume_*`:

- `catalog.checkout_resume_ready`
  - когда token привязан к analytics context;
  - поля: `surface`, `entry_point`, `flow_id`, `checkout_token_hash`, `correlation_id`.
- `catalog.checkout_resume_status`
  - один раз на каждый уникальный status;
  - block: `CHECKOUT_RESUME_STATUS_<STATUS>`.
- `catalog.checkout_resume_success`
  - только при `succeeded`.
- `catalog.checkout_resume_start`
  - по клику `Вернуться`.
- `catalog.checkout_resume_cancel`
  - по клику `Отменить`.

`checkout_token` не должен уходить в telemetry в открытом виде; используется hashed value из shared analytics helper.

## Runtime / mock matrix

- `mock=1`, `runtime=0` → synthetic succeeded state, без backend fetch.
- `mock=1`, `runtime=1` → реальный fetch `/api/billing/sessions/:token`, но UI остаётся в mock-friendly shell.
- `mock=0`, `runtime=1` → обычный production-like runtime flow.

Именно сценарий `mock=1&runtime=1` нужен для регрессий: он проверяет, что banner сохраняет тестовый shell, но использует реальное resume состояние и telemetry.

## Regression coverage

- `frontend/e2e/report-workflow.spec.ts`
  - catalog surface: `pending -> succeeded`, `canceled`, telemetry envelope, runtime flag preservation.
- `frontend/e2e/core-ux.spec.ts`
  - week surface: `failed`, telemetry envelope, runtime flag preservation.
- Дополнительно смежные сценарии уже есть в:
  - `frontend/e2e/billing-mock.spec.ts`
  - `frontend/e2e/week-home-refresh.regression.spec.ts`
  - `frontend/e2e/report-failure.spec.ts`
