# GRACE Test Matrix

> Legacy global matrix. Prefer `docs/REGRESSION_MAP.md` as the single durable regression map. Keep this file only for older detailed notes that have not yet been folded into packet-local matrices.

`docs/TEST_MATRIX.md` фиксирует минимально-достаточные тесты по активным GRACE-срезам и разделяет их на backend/front. Источник правды для списка — текущие DoD/checklist материалы: `verification-matrix.md`, `docs/GRACE_SLICE_AUTOMATION_MAP.md`, `docs/GRACE_ARTIFACTS.md` и rollout note для admin gate.

## Базовые профили DoD

### Backend

- `backend:quick` — `docker exec astro-project-backend-1 python3 scripts/pipeline.py`

### Frontend

- `frontend:quick` — `./scripts/run_e2e.sh --last-failed`
- `frontend:targeted` — `./scripts/run_e2e.sh e2e/<file>.spec.ts -g "<case>"`
- `smoke` — `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/core-ux.spec.ts e2e/report-create.spec.ts e2e/quality.spec.ts`
- `full-regression` — `./scripts/run_e2e.sh`

## Матрица по GRACE-срезам

| GRACE slice | Flow | DoD / gate focus | Backend tests | Frontend tests |
| --- | --- | --- | --- | --- |
| `M-NATAL-SUMMARY-LAYER` | `FLOW-REPORT-GENERATION` | Контекст, style contract, repair/fallback, forecast create/read, read quality, benchmark rerun перед Gate 3 | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_natal_section_context.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_report_contract.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_report_context.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_validation_relaxed.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_validation_template_fallback.py`<br>`PYTHONPATH=. python3 -m pytest tests/verify_natal_generation.py`<br>`PYTHONPATH=. python3 -m pytest tests/verify_natal_style.py`<br>`python3 scripts/grace_lint.py` | `./scripts/run_e2e.sh e2e/quality.spec.ts`<br>`./scripts/run_e2e.sh e2e/report-create.spec.ts -g "week forecast"`<br>`./scripts/run_e2e.sh e2e/forecast-realdata.spec.ts`<br>`./scripts/run_e2e.sh e2e/year-forecast-read.spec.ts`<br>`./scripts/run_e2e.sh e2e/ten-year-forecast-read.spec.ts`<br>`./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts` |
| `FEED-PERSONALIZED-DAILY` | `FLOW-DAILY-FEED` | Фактуальность `/api/feed/today`, deterministic fallback, удержание feed smoke и health probes | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_personalized_daily_service.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_daily_feed_robustness.py`<br>`PYTHONPATH=. python3 -m pytest tests/verify_daily_feed.py` | `./scripts/run_e2e.sh e2e/core-ux.spec.ts` |
| `ADMIN-ENTITLEMENTS-FLOW` | `FLOW-ADMIN-OPS` | Gate 3 evidence: entitlement-first grants, admin reports UI/detail flow, regeneration/audit smoke | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`<br>`docker exec astro-project-backend-1 python3 -m pytest -q tests/test_entitlements.py tests/test_entitlements_unit.py tests/test_one_off_entitlements_scaffold.py` | `./scripts/run_e2e.sh e2e/admin.entitlements.spec.ts`<br>`./scripts/run_e2e.sh e2e/admin.smoke.spec.ts` |
| `FORECAST-LADDER-CATALOG-FLIP` | `FLOW-FORECAST-CATALOG` | Catalog/runtime alignment, checkout bridge, billing access, storefront/history consistency, one-off runtime bridge | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_billing_checkout_sessions.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_billing_checkout_resume.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_one_off_access_runtime.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_one_off_runtime_smoke.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_legacy_workflow_one_off_alignment.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_admin_grant_one_off_alignment.py`<br>`PYTHONPATH=. python3 -m pytest tests/test_one_off_entitlements_scaffold.py` | `./scripts/run_e2e.sh e2e/billing-catalog-alignment.spec.ts`<br>`./scripts/run_e2e.sh e2e/report-create.spec.ts`<br>`./scripts/run_e2e.sh e2e/month-forecast-bridge-storefront.spec.ts`<br>`./scripts/run_e2e.sh e2e/year-forecast-bridge-storefront.spec.ts`<br>`./scripts/run_e2e.sh e2e/solar-return-bridge-storefront.spec.ts`<br>`./scripts/run_e2e.sh e2e/synastry-bridge-storefront.spec.ts`<br>`./scripts/run_e2e.sh e2e/history-cta.spec.ts`<br>`E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge natal one-off mock checkout through billing complete to read"`<br>`E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge month forecast one-off mock checkout through billing complete to read"`<br>`E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge year forecast one-off mock checkout through billing complete to read"`<br>`E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should bridge solar return one-off mock checkout through billing complete to read"`<br>`E2E_ENABLE_ONE_OFF_RUNTIME=1 ./scripts/run_e2e.sh e2e/billing-mock.spec.ts -g "should resume direct mock checkout from billing complete to read"` |

## Сводка по слоям

### Backend-first slices

- `M-NATAL-SUMMARY-LAYER`
- `FEED-PERSONALIZED-DAILY`
- `ADMIN-ENTITLEMENTS-FLOW`
- `FORECAST-LADDER-CATALOG-FLIP`

Для любого существенного backend-изменения в одном из этих срезов обязательный минимум — `backend:quick` плюс targeted pytest-пакет из строки slice.

### Frontend-first / UX gates

- `M-NATAL-SUMMARY-LAYER` — read/create/quality forecast UX
- `FEED-PERSONALIZED-DAILY` — `core-ux` smoke
- `ADMIN-ENTITLEMENTS-FLOW` — admin reports + entitlements smoke
- `FORECAST-LADDER-CATALOG-FLIP` — storefront, history CTA, billing bridge, one-off checkout flow

Для любого существенного frontend-изменения обязательный минимум — `frontend:quick` или targeted Playwright из строки slice; перед handoff на знакомый smoke использовать профиль `smoke`.

## Как пользоваться матрицей

1. Определить затронутый GRACE-срез.
2. Запустить `backend:quick` при любой существенной backend-правке.
3. Запустить targeted backend/front тесты из строки соответствующего slice.
4. Если меняется UI или flow даёт 500/краш — обновить или добавить воспроизводящий тест и довести профиль slice до PASS.
5. Перед Gate / handoff приложить evidence: какие команды из этой матрицы были зелёными.

## Источники

- `verification-matrix.md`
- `docs/GRACE_SLICE_AUTOMATION_MAP.md`
- `docs/GRACE_ARTIFACTS.md`
- `docs/rollout_notes/admin-entitlements-gate3-2026-03-20.md`
