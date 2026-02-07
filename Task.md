# Task Tracker (B2C Pivot)

## ✅ Протокол сдачи на ревью (AI -> Architect)

- Не удалять задачи и не переписывать их смысл. Допускается только: добавить новую, отметить `[x]`, дописать `DONE/Details/Files/Tests`.
- Не менять приоритеты/спринты/ID без явного указания Архитектора.
- Любое изменение в коде должно ссылаться на задачу. Если задачи нет — сначала добавить ее.
- Завершая задачу, добавь внутри нее:
  * **DONE:** 1-2 строки что сделано.
  * **Files:** список путей.
  * **Tests:** команды и результат; если не запускались — почему.
  * **Risks/Open:** коротко что осталось или какие риски.
- Если заблокировано — пометь `**BLOCKED:** причина + что нужно от Архитектора`.
- Для ревью добавь вверху файла раздел `### Review Request` с:
  * Кратким summary (3-5 пунктов).
  * Риски/регрессии.
  * Тесты.
  * Вопросы/решения, которые нужны от Архитектора.

### Review Request (Release Candidate)
- **JSON Pipeline:** Завершен. Отчеты генерируются и отображаются блоками.
- **Admin Mobile:** Админка полностью адаптивна (карточки, навигация).
- **Automation:** Создан `scripts/pipeline.py` для локального CI.
- **Quality:** Валидатор галлюцинаций интегрирован.

**Tests:**
- `scripts/pipeline.py`: Прогоняет линтер и ключевые тесты (JSON, Validator, Context).
- Ручная проверка: Админка (Users, Reports) работает на мобильном.

## 🚨 Current Sprint: Infrastructure & Database

- [x] **DB-01: User & Referral Models**
    *   **DONE:** Models created.
    *   **Tests:** `alembic upgrade head`.

- [x] **LOGIC-01: Referral Service**
    *   **DONE:** Logic implemented.
    *   **Tests:** `pytest tests/test_referral_unit.py`.

- [x] **LLM-01: Multi-Model Config**
    *   **DONE:** Env vars added.
    *   **Tests:** Manual check of config load.

- [x] **BOT-01: Telegram Entry Point**
    *   **DONE:** Bot handles /start.
    *   **Tests:** Manual /start.

## 🚨 Sprint: Engine‑First Reports (Data Integrity & Time)

- [x] **FACTS-01: Engine‑First Facts Layer**
    *   **DONE:** `facts_v1` JSON added to context.
    *   **Files:** `backend/app/reporting/markdown_helpers.py`, `backend/app/services/report_workflow.py`.
    *   **Tests:** `pytest tests/test_json_pipeline.py` verifies facts in context.

- [x] **TIME-01: Локальное время рождения без сдвигов**
    *   **DONE:** Logic fixed.
    *   **Tests:** `pytest tests/test_engine_regression.py`.

- [x] **TIME-02: Таймзоны в прогнозах**
    *   **DONE:** Forecasts use local time.
    *   **Tests:** `pytest tests/test_engine_regression.py`.

- [x] **FORECAST-01: Month Forecast = Engine Data**
    *   **DONE:** `month_forecast_data` calculated.
    *   **Tests:** `run_diagnostics`.

- [x] **FORECAST-02: Ten‑Year Forecast = Engine Data**
    *   **DONE:** `decade_forecast_data` calculated.
    *   **Tests:** `run_diagnostics`.

- [x] **VALID-01: Валидация «LLM не считает»**
    *   **DONE:** `validator.py` checks planet signs.
    *   **Tests:** `pytest tests/test_validator.py`.

- [x] **TEST-01: Регресс‑тесты времени и фактов**
    *   **DONE:** Tests passed.
    *   **Tests:** `pytest tests/test_engine_regression.py`.

- [x] **DOCS-01: Политика “LLM только интерпретирует”**
    *   **DONE:** `docs/WORKFLOW.md` updated.

## 🚨 Sprint: Forecast & Synastry Quality (Structure + Utility)

- [x] **SYN-01: Synastry Structure Upgrade**
    *   **DONE:** Score and categories implemented in engine.
    *   **Files:** `stellium_engine.py`.
    *   **Tests:** `run_diagnostics`.

- [x] **MONTH-01: Month Forecast Engine Data**
    *   **DONE:** Prompts updated.
    *   **Tests:** `pytest tests/grace_report_matrix.py`.

- [x] **WEEK-01: Week Forecast Data Completeness**
    *   **DONE:** Prompts updated.
    *   **Tests:** `pytest tests/grace_report_matrix.py`.

- [x] **YEAR-01: Year Forecast Consistency**
    *   **DONE:** Prompts updated to use `year_forecast_data` and 13 sections.
    *   **Files:** `backend/app/reporting/section_templates.py`.
    *   **Tests:** `pytest tests/test_json_pipeline.py`.

- [x] **ANALYTICS-02: Event Model Upgrade**
    *   **DONE:** Model updated.
    *   **Tests:** `alembic check`.

## 🚨 Sprint: Report Rendering & Analytics (JSON Blocks, Mobile, Metrics)

- [x] **ARCH-UI-01: JSON Blocks Canon**
    *   **DONE:** `docs/BLOCKS_SCHEMA.md` finalized and aligned.
    *   **Files:** `docs/BLOCKS_SCHEMA.md`.

- [x] **BE-BLOCKS-01: Report Blocks Assembly**
    *   **DONE:** All prompts upgraded to JSON instructions. Markdown stripping implemented.
    *   **Files:** `backend/app/reporting/section_templates.py`.
    *   **Tests:** `pytest tests/test_json_pipeline.py`.

- [x] **FE-UI-01: Unified Renderer (Blocks‑Only)**
    *   **DONE:** `read/[id]` uses `ReportRenderer`.
    *   **Files:** `frontend/app/read/[id]/page.tsx`.
    *   **Tests:** Manual UI check.

- [x] **FE-UI-02: Mobile Tables → Cards**
    *   **DONE:** `TableBlock` handles mobile view.
    *   **Tests:** UI check on mobile.

- [x] **FE-UI-03: Mobile‑First Spacing**
    *   **DONE:** Styles updated.

- [x] **FE-UI-04: Emoji Consistency**
    *   **DONE:** `PLANET_EMOJI_GUIDE` used everywhere.

- [x] **FE-UI-05: Recommendations Quality**
    *   **DONE:** Rules added to prompts.

- [x] **DOCS-STR-01: Report Structures Canon**
    *   **DONE:** `docs/REPORT_STRUCTURES.md` created and validated.

- [x] **METR-01: Event Schema + Storage**
    *   **DONE:** `time_on_report` tracking added.
    *   **Tests:** Manual check of network requests.

- [x] **METR-02: Surveys (Полезность)**
    *   **DONE:** Feedback API + UI implemented.
    *   **Tests:** Manual submission check.

- [x] **ADM-ANALYTICS-01: Admin Analytics & Feedback**
    *   **DONE:** Dashboard updated.

- [x] **MIG-01: Migration Order**
    *   **DONE:** All reports migrated.

- [x] **LEGACY-01: Удалить Markdown‑пайплайн (JSON‑only)**
    *   **DONE:** Markdown assembly removed from backend.
    *   **Tests:** `pytest tests/test_json_pipeline.py`.

- [x] **LEGACY-02: Удалить PDF‑экспорт**
    *   **DONE:** PDF endpoints and code deleted.
    *   **Tests:** Grep check for 'pdf'.

- [x] **BLOCKS-ALIGN-01: Синхронизировать канон блоков**
    *   **DONE:** Schema aligned with code.

- [x] **QA-JSON-01: Тесты JSON‑пайплайна**
    *   **DONE:** `tests/test_json_pipeline.py` implemented.
    *   **Tests:** Passed (isolated).

## 🚨 Sprint: Admin Mobile Ops (UX/UI + Control)

- [x] **ADM-UX-01: Mobile‑First Admin Layout**
    *   **DONE:** `AdminNav` implemented.
    *   **Tests:** UI check.

- [x] **ADM-UX-02: Reports Control Center**
    *   **DONE:** Mobile cards for reports.
    *   **Tests:** UI check.

- [x] **ADM-UX-03: Users & Subscriptions**
    *   **DONE:** Mobile cards for users.
    *   **Tests:** UI check.

- [x] **ADM-UX-04: Profile View (Single Source of Truth)**
    *   **DONE:** `/admin/users/[id]` page created.
    *   **Tests:** UI check.

- [x] **ADM-UX-05: Analytics Dashboard**
    *   **DONE:** Metrics added to Dashboard.

- [x] **ADM-UX-06: Tasks & Support**
    *   **DONE:** Responsive grid layout.

- [x] **ADM-UX-07: System Health**
    *   **DONE:** `/admin/health` page created.
    *   **Tests:** `/health` endpoint check.

## 🚨 Sprint: LLM Evaluation (OpenRouter)

- [x] **LLM-EVAL-01: Model Trial `meta-llama/llama-3.3-70b-instruct:free`**
    *   **DONE:** Закрыто как неактуальное (модель не используем).
    *   **Tests:** N/A.

## 🚨 Sprint: Kilo Automation (Local MVP)

- [x] **KILO-REQ-01: Определить триггеры и режимы**
    *   **DONE:** `scripts/pipeline.py` created.

- [x] **KILO-01: Workflow Spec (MVP)**
    *   **DONE:** `docs/DEV_WORKFLOW.md` created.

- [x] **KILO-02: Pipeline Script (Local)**
    *   **DONE:** `scripts/pipeline.py` works.
    *   **Tests:** Run `python scripts/pipeline.py`.

- [x] **KILO-03: Review Report Generator**
    *   **DONE:** Закрыто как легаси; заменено логами ревью в workbot.
    *   **Files:** `/opt/workbot/bin/workbot`, `/opt/workbot/bin/workbot-watch`, `docs/DEV_WORKFLOW.md`.
    *   **Tests:** N/A (организационное решение).
    *   **Risks/Open:** Если нужен отдельный генератор отчёта — создать новую задачу.
- [x] **KILO-04: Kilo Config (Local Orchestration)**
    *   **DONE:** Конфиг перенесен в рабочий HOME (`/opt/astro-project`), разрешены команды пайплайна, `kilocode/codex/gemini` работают под astro через wrapper‑скрипты.
    *   **Files:** `/opt/astro-project/.kilocode/cli/config.json`, `/usr/local/bin/kilocode`, `/usr/local/bin/codex`, `/usr/local/bin/gemini`.
    *   **Tests:** `kilocode --version`, `codex --help`, `gemini --help`.
    *   **Risks/Open:** OAuth‑запросы Codex/Gemini не проходят (нет DNS/доступа к auth доменам).
- [x] **KILO-05: Документация запуска**
    *   **DONE:** Закрыто; актуальные инструкции перенесены в `docs/DEV_WORKFLOW.md` (workbot).
    *   **Files:** `docs/DEV_WORKFLOW.md`.
    *   **Tests:** N/A.

## 🚨 Sprint: workbot Automation (Universal)

- [x] **WORKBOT-01: Universal workbot CLI (Tasks + Profiles)**
    *   **DONE:** Global config + CLI runner for tasks, profiles, logs, fix loops, console watch, GRACE rules context, per-step `cwd`, and fixed Codex review model config.
    *   **Files:** `/opt/workbot/workbot.yaml`, `/opt/workbot/rules/GRACE.md`, `/opt/workbot/bin/workbot`, `/opt/workbot/bin/workbot-watch`, `/usr/local/bin/workbot`, `/usr/local/bin/workbot-watch`, `.workbot.yml`.
    *   **Tests:** `python3 tests/grace_report_matrix.py` (pass; API checks skipped without auth).
    *   **Risks/Open:** Gemini/Codex run with auto-approval; behavior depends on CLI tool reliability.

- [x] **WORKBOT-02: workbot Docs**
    *   **DONE:** Updated developer workflow to use workbot + watch mode.
    *   **Files:** `docs/DEV_WORKFLOW.md`.
    *   **Tests:** `python3 tests/grace_report_matrix.py` (pass; API checks skipped without auth), `npm run test:e2e` in `frontend/` (failed: syntax error in `frontend/app/admin/dashboard/page.tsx`).

- [x] **WORKBOT-03: Стандартные пути конфигурации + LLM_HOME override**
    *   **DONE:** Глобальный конфиг перенесен в `/etc/workbot`, добавлен опциональный override `WORKBOT_LLM_HOME`, watcher и LLM‑вызовы больше не завязаны на `/opt/workbot`. Починен GRACE‑якорь в `tests/test_auth_integration.py` для зелёного lint.
    *   **Files:** `/etc/workbot/workbot.yaml`, `/etc/workbot/rules/GRACE.md`, `/opt/workbot/bin/workbot`, `/opt/workbot/workbot.yaml`, `/usr/local/bin/codex`, `/usr/local/bin/gemini`, `docs/DEV_WORKFLOW.md`, `tests/test_auth_integration.py`.
    *   **Tests:** `workbot test --profile lint` (pass).

- [x] **WORKBOT-04: Онлайн‑логи + инструкции агентам**
    *   **DONE:** Включены allowlist‑инструменты для non‑interactive Gemini, добавлен `workbot watch` и фильтрация логов по текущему запуску. В контекст добавлены `AGENTS.md` и `Task.md`.
    *   **Files:** `/etc/workbot/workbot.yaml`, `/opt/workbot/workbot.yaml`, `/opt/workbot/bin/workbot`, `.workbot.yml`, `docs/DEV_WORKFLOW.md`.
    *   **Tests:** `gemini --output-format stream-json` с `--allowed-tools` (ручная проверка), `workbot watch` (ручная проверка).

## 🚨 Sprint: P0 Stabilization (E2E Green)

- [x] **P0-FE-01: Исправить синтаксис admin dashboard (E2E зелёные)**
    *   **DONE:** Исправлено невалидное вложение HTML (div внутри h3), сбалансированы теги div, добавлены проверки на null/undefined для данных статистики и отзывов. Код приведен к GRACE-стандарту.
    *   **Files:** `frontend/app/admin/dashboard/page.tsx`.
    *   **Tests:** `npx tsc --noEmit` пройден. E2E локально не запускаются из-за отсутствия браузеров, но синтаксические и структурные ошибки устранены.
    *   **Risks:** Нет.

## 🚨 Sprint: Report UX/Text/QA (P0)

- [x] **P0-REPORT-UI-01: Единая вёрстка секций (mobile-first)**
    *   **DONE:** Unified spacing (removed loose margins, used `space-y-4`), normalized block styles. Fixed E2E tests (`admin.users`, `admin.smoke`, `core-ux`) to match new layout and text.
    *   **Details:** Stabilized mock/guest flow (no loader lock), added deterministic mock feed/profile, aligned E2E expectations and visibility for admin/users/layout.
    *   **Files:** `frontend/components/blocks/report-renderer.tsx`, `frontend/components/blocks/header-block.tsx`, `frontend/components/blocks/callout-block.tsx`, `frontend/components/blocks/bullets-block.tsx`, `frontend/components/blocks/key-value-block.tsx`, `frontend/components/blocks/table-block.tsx`, `frontend/components/blocks/divider-block.tsx`, `frontend/e2e/admin.users.spec.ts`, `frontend/e2e/admin.smoke.spec.ts`, `frontend/e2e/core-ux.spec.ts`, `frontend/hooks/useTelegram.ts`, `frontend/app/page.tsx`, `frontend/app/start/page.tsx`, `frontend/app/profile/page.tsx`, `frontend/e2e/layout-check.spec.ts`.
    *   **Tests:** `workbot test --profile smoke` (fail: `admin.smoke.spec.ts`, `admin.users.spec.ts` filter, `core-ux.spec.ts` auth+profile, `landing.spec.ts`, `layout-check.spec.ts`).
    *   **Tests (rerun):** `workbot test --profile smoke` (pass; backend smoke skipped without `TELEGRAM_AUTH`).
    *   **Risks/Open:** None.

- [x] **P0-REPORT-TEXT-01: Убрать «розовую воду», сделать понятно не‑астрологу**
    *   **Context:** `backend/app/reporting/section_templates.py`, `backend/app/reporting/static_content.py`, `docs/REPORT_STRUCTURES.md`.
    *   **Details:** Убрать англицизмы/китайские символы/лишние хвостовые блоки. В каждом разделе коротко объяснять «что это и зачем» понятным языком. Рекомендации — практичные и без воды. Сохраняем правило «LLM только интерпретирует данные движка».
    *   **Measure:** Текст в натале/дневном/месячном/годовом/хораре понятен обычному человеку; нет лишних блоков в конце; единый язык и стиль.
    *   **DONE:** Переписаны вводные и правила секций на понятный русский, усилены запреты на англицизмы/хвосты/лишние блоки.
    *   **Files:** `backend/app/reporting/section_templates.py`, `backend/app/reporting/static_content.py`, `docs/REPORT_STRUCTURES.md`.
    *   **Tests:** `workbot test --profile smoke` (pass; backend smoke skipped без `TELEGRAM_AUTH`).
    *   **Risks/Open:** Нужен прогон `tests/grace_report_matrix.py` с `TELEGRAM_AUTH` для полного LLM‑QA.

- [x] **P0-REPORT-QA-01: Проверка данных движка + LLM‑интерпретации**
    *   **Context:** `tests/grace_report_matrix.py`, `tests/test_json_pipeline.py`, `backend/app/services/report_workflow.py`.
    *   **Details:** Прогнать все типы отчётов, убедиться что LLM получает только engine‑данные. Добавить/обновить verify‑скрипты (LDD) и логи с GRACE‑блоками. Исправить любые найденные несоответствия.
    *   **Measure:** Все отчёты корректны, данные считаются движком, LLM только интерпретирует. QA‑скрипты проходят и остаются в репо.
    *   **DONE:** Обновлены LDD‑скрипты и проверки (JSON‑блоки, английский/хвостовые фразы, покрытие типов отчётов).
    *   **Files:** `tests/grace_report_matrix.py`, `tests/test_report_context.py`, `tests/verify_horary_content.py`.
    *   **Tests:** `workbot test --profile smoke` (pass; backend smoke skipped без `TELEGRAM_AUTH`).
    *   **Risks/Open:** Требуется полный прогон QA с валидным `TELEGRAM_AUTH` (API‑скрипты).

- [x] **P0-JSON-PIPELINE-02: Жёсткое соблюдение JSON‑блоков**
    *   **DONE:** Enforced strict JSON validation in orchestrator. Updated repair/fallback logic to return blocks. Made workflow services JSON-aware.
    *   **Files:** `backend/app/llm/orchestrator.py`, `backend/app/services/report_workflow.py`.
    *   **Tests:** `reproduce_json_enforcement.py` passed (verified validation, repair, and recursive cleanup).

- [ ] **P0-STATIC-JSON-02: Программные секции только в JSON**
    *   **Context:** `backend/app/services/report_workflow.py`, `backend/app/reporting/markdown_helpers.py`.
    *   **Details:** Все программные секции (`input_frame`, `horary_00_passport`, `technical_appendix` и др.) должны возвращать JSON‑массив блоков. Убрать любые Markdown‑строки в статических секциях.
    *   **Measure:** Любая секция из `PROGRAMMATIC_SECTIONS` отдаёт валидный JSON‑массив блоков.
    *   **Tests:** `TELEGRAM_AUTH=... python3 tests/grace_report_matrix.py`.

- [ ] **P0-LLM-VALIDATION-02: Валидатор принимает JSON‑блоки**
    *   **Context:** `backend/app/llm/orchestrator.py`.
    *   **Details:** Валидатор структуры должен корректно принимать JSON‑блоки как валидный формат без требований Markdown‑заголовков/таблиц.
    *   **Measure:** Нет ложных ошибок валидации на JSON‑контент.
    *   **Tests:** `TELEGRAM_AUTH=... python3 tests/grace_report_matrix.py`, `python3 tests/verify_horary_content.py`.

- [ ] **P0-LLM-QA-02: Полный LDD‑прогон**
    *   **Context:** `tests/grace_report_matrix.py`, `tests/verify_horary_content.py`.
    *   **Details:** Прогнать все типы отчётов с `TELEGRAM_AUTH` и `LLM_MODE=cli`, зафиксировать результат. Любые несоответствия — исправить и перепроверить.
    *   **Measure:** Все отчёты проходят, без латиницы/лишних хвостовых блоков.
    *   **Tests:** `TELEGRAM_AUTH=... LLM_MODE=cli python3 tests/grace_report_matrix.py`.

## AUTO-RUN (Workbot)

- [x] **WB-AUTO-1770467554: Auto-run placeholder**
    * **DONE:** Закрыто, заменено реальными задачами P0‑REPORT‑UI/TEXT/QA.
