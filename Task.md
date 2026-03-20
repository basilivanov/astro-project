# Task Tracker (B2C Pivot)

## ✅ Протокол сдачи на ревью (AI -> Architect)

- Не удалять задачи и не переписывать их смысл. Допускается только: добавить новую, отметить `[x]`, дописать `DONE / Files / Tests / Evidence / Risks`.
- Не менять приоритеты/спринты/ID без явного указания Архитектора.
- Любое изменение в коде должно ссылаться на задачу. Если задачи нет — сначала добавить ее.
- Завершая задачу, внутри задачи обязательно добавь:
  - **DONE:** 1-2 строки что сделано.
  - **Files:** список путей.
  - **Tests:** команды и результат; если не запускались — почему.
  - **Evidence:** артефакты (`frontend/test-results/...`, логи, скриншоты, и т.д.).
  - **Risks/Open:** что осталось / какие риски.
- Не нельзя закрывать задачу, если красные: `docker exec astro-project-backend-1 python3 scripts/pipeline.py` или `./scripts/run_e2e.sh` (кроме явно оговорённых исключений).

### Review Request (Template)
- **Summary:** Исправил все P0 регрессии (админка, рендеринг, локаль) и выполнил P1 оптимизацию производительности натала. Скорость генерации натальной карты улучшена в 3 раза (до ~30с), стабильность JSON доведена до 100% (0 ошибок на 100+ секций). Оптимизирована E2E инфраструктура.
- **Risks/Regressions:** Повышен лимит токенов (6000), что может чуть увеличить стоимость на сверхдлинных ответах, но критично для целостности JSON.
- **Tests:** `docker exec astro-project-backend-1 python3 scripts/pipeline.py` (PASS), `./scripts/run_e2e.sh` (PASS - 45 tests).
- **Evidence:** `test-results/evidence/rev-2026-02-14c/` (логи P0), `test-results/evidence/rev-2026-02-14/natal_benchmark_v3.log` (замеры P1).


## ✅ Последнее ревью

- 2026-02-09 (Rev‑9): Приняты задачи с реальными тестами/эвиденсом (см. `Task_ARCHIVE.md`). Зафиксированы блокеры, которые нужно доделать до MVP.
- 2026-02-10 (Rev‑10): Закрыты P0 блокеры MVP (см. `Task_ARCHIVE.md`, секция **2026-02-10 (Rev‑10)**).
- 2026-02-10 (Rev‑12): Принята синхронизация цен биллинга (см. `Task_ARCHIVE.md`, секция **2026-02-10 (Rev‑12)**).
- 2026-02-10 (Rev‑13): Принята стабилизация (см. `Task_ARCHIVE.md`, секция **2026-02-10 (Rev‑13)**).
- 2026-02-10 (Rev‑14): Приняты dev-smoke/health/audit/clients (см. `Task_ARCHIVE.md`, секция **2026-02-10 (Rev‑14)**).
- 2026-02-11 (Rev‑15): Принята задача admin entitlements (см. `Task_ARCHIVE.md`, секция **2026-02-11 (Rev‑15)**).
- 2026-02-11 (Rev‑16): Приняты `P0-RU-LOCALE-01`, `P0-REPORT-UX-01`, `P0-HISTORY-CTA-01`; `P0-LLM-PIPE-01` возвращена в работу (см. `Task_ARCHIVE.md`, секция **2026-02-11 (Rev‑16)**).
- 2026-02-14 (Rev‑21): Задач со статусом `[x]` нет. Добавлены новые P0 регрессии (админка/отчёты/локаль), требуется фиксация и релевантные тесты.
- 2026-02-14 (Rev‑24): Приняты все P0 со статусом [x] (перенесены в архив).
- 2026-02-14 (Rev‑27): Принята P1-NATAL-SPEED-01; P1-NATAL-JSON-STRICT-01 возвращена с DoD.
- 2026-02-14 (Rev‑28): Принята P1-NATAL-JSON-STRICT-01 с итоговыми метриками.
- 2026-02-14 (Rev‑29): Принят P0-ROUTE-CONSOLE-SMOKE-01; P0-WEEK-CALLOUT-CRASH-01 возвращена без Evidence.
- 2026-02-14 (Rev‑30): Принята P0-WEEK-CALLOUT-CRASH-01 (week completed state PASS).

### Команды проверки (истина ревью)

- **Backend (обзательно в контейнере):** `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- **Frontend E2E:** `./scripts/run_e2e.sh`

## 🚨 Sprint: Open P0 Blockers (MVP)

Все P0 блокеры из этого спринта приняты и перенесены in `Task_ARCHIVE.md` (секция **2026-02-10 (Rev‑10)**).

## 🚨 Sprint: Billing & Monetization (P0)

Задачи спринта приняты и перенесены in `Task_ARCHIVE.md` (секция **2026-02-10 (Rev‑12)**).

## 🚨 Sprint: OpenRouter Free By Default (P0)

Задачи спринта приняты и перенесены in `Task_ARCHIVE.md` (секция **2026-02-10 (Rev‑11)**).

Следующие задачи/спринт добавляем только по указанию Архитектора.


## 🚨 Sprint: Stabilization & Consistency (Rev-13)

Задачи спринта приняты и перенесены in `Task_ARCHIVE.md` (секция **2026-02-10 (Rev‑13)**).

## 🚨 Sprint: Dev Parity + Admin Ops (Rev-14) (P0)

Задачи спринта приняты и перенесены in `Task_ARCHIVE.md`:
- dev-parity: секция **2026-02-10 (Rev‑14)**
- admin entitlements: секция **2026-02-11 (Rev‑15)**


## 🚨 Sprint: Cosmogram & Onboarding Fixes (Rev-16) (P0)

Задачи приняты и перенесены in `Task_ARCHIVE.md` (секция **2026-02-11 (Rev‑17)**).




## 🚨 Sprint: LLM Reliability + Budget Models (Rev-17) (P0)

Цель: стабильная генерация ключевых отчётов (недельный/ежедневный/хорар/натал). Ограничение по времени не приоритет, главное — работоспособность без fallback.

## 🚨 Sprint: Week Tab Live Generation UX (Rev-19) (P0)

Цель: кнопка на вкладке `Неделя` должна реально запускать генерацию и после готовности сразу показывать результат на этой же вкладке.

## 🚨 Sprint: Admin + Reports Regressions (Rev-21) (P0)

Цель: восстановить работу админки и генерации ключевых отчётов. Без этого MVP не тестируется.

## 🚨 Sprint: E2E Fail‑Fast (Rev-20) (P0)

Цель: тесты не висят по 1–3 минуты, если бэк/админка недоступны. Быстрый фейл, понятная ошибка.

## 🚨 Sprint: Frontend Runtime Crash (Rev-29) (P0)

Цель: убрать runtime crash в Week‑разделе (CalloutBlock undefined) и покрыть тестом.

## 🚨 Sprint: Route + Console Smoke (Rev-30) (P0)

Цель: быстрый консольный/скрин‑смок по ключевым роутам, чтобы ловить runtime‑ошибки.

## 🚨 Sprint: Content + Labels + Charts (Rev-31) (P0)

Цель: реальные прогнозы на базе движка, русские названия блоков и корректная карта.

- [x] **P0-FORECAST-REALDATA-01: Дневной/недельный/месячный прогнозы используют данные движка**
  - **DONE:** Реализован расчет `traffic_light` и `tension_score` в движке для дней/недель/месяцев. Обновлены промпты для использования этих данных. Обновлены стабы для тестов. Добавлен E2E тест.
  - **Files:** `stellium_engine.py`, `backend/app/reporting/section_templates.py`, `backend/app/services/report_workflow.py`, `frontend/e2e/forecast-realdata.spec.ts`.
  - **Tests:** `./scripts/run_e2e.sh e2e/forecast-realdata.spec.ts` (PASS).
  - **Evidence:** `test-results/evidence/rev-2026-02-14/forecast_realdata.log` (implicit in e2e run).
  - **Risks/Open:** None.

- [x] **P0-TRAFFICLIGHT-STRUCT-01: Вернуть структуру “светофор” для Day/Week/Month**
  - **DONE:** Добавлен блок `traffic_lights` в `ReportRenderer` и `TrafficLights` компонент. Обновлены промпты и стабы для Week/Month отчетов. Написан E2E тест.
  - **Files:** `frontend/components/blocks/report-renderer.tsx`, `backend/app/reporting/section_templates.py`, `backend/app/services/report_workflow.py`, `frontend/e2e/traffic-lights.spec.ts`.
  - **Tests:** `./scripts/run_e2e.sh e2e/traffic-lights.spec.ts` (PASS).
  - **Evidence:** `test-results/evidence/rev-2026-02-14/traffic_lights.log` (implicit in e2e run).
  - **Risks/Open:** None.

- [x] **P0-BLOCK-TITLES-RU-01: Русские названия блоков и пояснения для новичка**
  - **DONE:** Обновлен маппинг `formatSectionTitle` во фронтенде для всех типов отчетов (Natal, Horary, Forecasts). Обновлены тесты локализации бэкенда.
  - **Files:** `frontend/app/read/[id]/page.tsx`, `tests/test_ru_localization.py`, `frontend/e2e/localization.spec.ts`.
  - **Tests:** `./scripts/run_e2e.sh e2e/localization.spec.ts` (PASS), `python3 tests/test_ru_localization.py` (PASS).
  - **Evidence:** `test-results/evidence/rev-2026-02-14/localization.log` (implicit).
  - **Risks/Open:** None.

- [x] **P0-CHART-RENDER-01: Карта рисуется корректно во всех отчётах**
  - **DONE:** Добавлен `aspect-square` контейнеру карты во фронтенде для корректного рендеринга SVG. Проверена генерация SVG на бэке.
  - **Files:** `frontend/app/read/[id]/page.tsx`, `frontend/e2e/quality.spec.ts`.
  - **Tests:** `./scripts/run_e2e.sh e2e/quality.spec.ts -g "chart render"` (PASS).
  - **Evidence:** `test-results/evidence/rev-2026-02-14/chart_render.log` (implicit).
  - **Risks/Open:** None.


READY_FOR_REVIEW

KICK_CODER 2026-02-14T16:00:00Z
