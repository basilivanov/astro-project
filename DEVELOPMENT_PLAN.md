# AstroSaaS: B2C Telegram-First Pivot

## 🎯 Глобальная цель
Создать массовый B2C сервис астрологических прогнозов с доступом через Telegram Mini App и Web.
**Ключевые фичи:** Подписка (Recurrent), Реферальная система (Дни или Деньги), Виральность, Низкая себестоимость.

## GRACE Development Plan

Этот план дополняет продуктовый roadmap operational-слоем strict GRACE: как вести ближайшие slice-волны от baseline docs до Gate 3, кто за что отвечает и какие regression hooks обязательны до handoff.

### Active execution governance

- `Strict-GRACE source of truth`: `GRACE.md`; этот документ фиксирует local execution governance для active slice и не должен противоречить policy-level baseline.
- `Execution state`: проект находится в `execution` state, а не в `pre-execution`, потому что pilot slice, first-wave write scope, controller packet и reviewer criteria уже определены.
- `Pilot slice`: `M-NATAL-SUMMARY-LAYER`.
- `Pilot outcome`: довести quality hardening для `executive_summary` / `final_synthesis` до reviewer-ready Gate 3 handoff с benchmark-backed evidence.
- `First-wave write scope`: только документы governance + active-slice artifacts: `DEVELOPMENT_PLAN.md`, `docs/GRACE_ARTIFACTS.md`; `GRACE.md` используется как read-only canon reference, код первой execution-wave для этого governance-шага не расширяется.

### First controller packet requirements

Controller для каждой execution-wave обязан собрать и зафиксировать packet со следующими полями:

| Field | Requirement |
| --- | --- |
| `slice_id` | Явный slice ID, для active wave сейчас это `M-NATAL-SUMMARY-LAYER` |
| `wave_goal` | Узкая цель волны, сформулированная как проверяемый outcome |
| `exact_write_scope` | Исчерпывающий список файлов/модулей, которые worker может менять |
| `allowed_files` | Подмножество write scope или точный список entrypoints, если scope уже file-bounded |
| `in_scope_scenarios` | Какие business/runtime scenarios должны остаться в execution wave |
| `deferred_scenarios` | Что сознательно вынесено из wave и почему |
| `verification_profile` | Минимально-достаточный regression profile, обязательный до handoff |
| `logs_facts` | Какие structured logs / replay contours должны быть собраны и приложены |
| `benchmark_facts` | Какие benchmark rerun / summary facts нужны для slice decision |
| `regression_facts` | Какие quick regression результаты обязательны и где они зафиксированы |
| `gate_conditions` | Что считается `In Progress`, `Ready`, `Gate 3` для этой wave |
| `reviewer_packet` | Формат handoff: doc diff, evidence links, residual risk, explicit status |

Минимальный controller packet для active pilot slice обязан приложить три класса evidence: `logs facts`, `benchmark facts`, `regression facts`. Отсутствие любого из трёх переводит wave обратно в quality loop и запрещает Gate handoff.

### Reviewer criteria and exit rules

Reviewer проверяет только slice-bounded execution и должен уметь восстановить path `slice -> write scope -> verification -> evidence -> gate decision` без догадок.

| Reviewer check | Exit criteria |
| --- | --- |
| `Slice integrity` | Везде указан один и тот же active slice: `M-NATAL-SUMMARY-LAYER`; нет competing pilot формулировок |
| `Scope discipline` | Все изменения лежат в exact write scope первой волны; нет скрытого расширения на соседние модули |
| `Controller packet completeness` | Packet содержит logs, benchmark, regression facts и явные gate conditions |
| `Verification traceability` | Быстрый профиль и targeted checks перечислены и могут объяснить текущий state slice |
| `Deferred hygiene` | Deferred отмечает только реально вынесенное из wave; ничего из active execution не описано как неопределённое «когда-нибудь» |
| `Gate decision clarity` | Slice имеет явный статус `In Progress`, `Ready`, или `Gate 3`, плюс остаточный риск и следующий шаг |

Reviewer не принимает handoff, если хотя бы одно из условий нарушено, если evidence не объясняет текущий quality state, или если документы допускают двусмысленность по owner / scope / gate.

### Current slice lanes

| Slice | Flow ID | Scope now | Owner | Regression hooks | Gate target |
| --- | --- | --- | --- | --- | --- |
| `M-NATAL-SUMMARY-LAYER` | `FLOW-REPORT-GENERATION` | active pilot slice; quality hardening для `executive_summary` / `final_synthesis` | AI Agent (Developer/QA) | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; `tests/verify_natal_generation.py`; `tests/test_natal_section_context.py`; `tests/verify_natal_style.py`; representative rerun | Gate 3 note after clean rerun |
| `FEED-PERSONALIZED-DAILY` | `FLOW-DAILY-FEED` | factual daily personalization + auth-safe fallback | AI Agent (Developer/QA) | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; `tests/test_personalized_daily_service.py`; `tests/test_daily_feed_robustness.py`; `tests/verify_daily_feed.py`; `./scripts/run_e2e.sh e2e/core-ux.spec.ts` | targeted smoke + replay evidence |
| `ADMIN-ENTITLEMENTS-FLOW` | `FLOW-ADMIN-OPS` | admin one-off entitlement flow and report ops contour | AI Agent (Developer/QA) | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; `tests/test_entitlements.py`; `tests/test_entitlements_unit.py`; `tests/test_one_off_entitlements_scaffold.py`; `./scripts/run_e2e.sh e2e/admin.entitlements.spec.ts`; `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts` | keep Gate 3 green |
| `FORECAST-LADDER-CATALOG-FLIP` | `FLOW-REPORT-GENERATION` + catalog alignment | deferred next candidate after current pilot execution stabilizes | Architect + AI Agent (Developer) | slice doc required before opening | pre-execution baseline docs |

### Phase plan: baseline docs → Gate 3

1. `Freeze baseline docs`
   - Owner: Architect + AI Agent (Developer).
   - Update slice brief, invariants, known defects, and intended Gate in the relevant GRACE doc.
   - Exit rule: scope cuts are explicit; no silent TODO scope; active pilot slice is named consistently across all docs.
2. `Map artifacts and boundaries`
   - Owner: AI Agent (Developer/QA).
   - Sync `docs/GRACE_ARTIFACTS.md` graph, code entrypoints, test files, replay helpers, and residual risks.
   - Exit rule: active slice has traceable path `slice -> code/docs scope -> tests -> replay/benchmark -> gate` and exact write scope is listed.
3. `Execute narrow implementation wave`
   - Owner: AI Agent (Developer).
   - Limit changes to the documented slice boundary and update adjacent docs if runtime behavior changes.
   - Exit rule: changed path is covered by minimal sufficient backend/frontend checks.
4. `Run quick regression profile`
   - Owner: AI Agent (QA).
   - Always run `docker exec astro-project-backend-1 python3 scripts/pipeline.py` after substantial backend/doc-linked changes; add targeted pytest/E2E according to the touched slice.
   - Exit rule: quick profile is green or failures are fixed in the same wave.
5. `Capture runtime evidence`
   - Owner: AI Agent (QA).
   - For feed/admin slices, attach structured log contour + replay helper output; for natal quality slice, attach benchmark rerun / summary note; controller packet must explicitly record logs, benchmark, and regression facts.
   - Exit rule: runtime evidence can explain why the slice is or is not rollout-ready, and the reviewer packet is complete.
6. `Package Gate 3 handoff`
   - Owner: Architect + AI Agent (Developer/QA).
   - Update rollout note / summary, status table, residual risk, and next recommended step.
   - Exit rule: slice has a clear state: `In Progress`, `Ready`, or `Gate 3`.

### Nearest dev/QA tasks

| Priority | Task | Owner | Regression hooks | Expected output |
| --- | --- | --- | --- | --- |
| P0 | Hold `ADMIN-ENTITLEMENTS-FLOW` green during adjacent one-off/catalog work | AI Agent (Developer/QA) | backend quick + targeted admin tests/E2E | no regression against 2026-03-20 Gate 3 note |
| P0 | Push `M-NATAL-SUMMARY-LAYER` from benchmark follow-up to clean Gate 3 note | AI Agent (Developer/QA) | backend quick + natal verifies + representative rerun | updated quality summary with clean evidence |
| P1 | Stabilize `FEED-PERSONALIZED-DAILY` smoke and close remaining `core-ux` drift | AI Agent (Developer/QA) | backend quick + feed pytest + `e2e/core-ux.spec.ts` + feed replay | repeatable feed smoke contour |
| P1 | Prepare `FORECAST-LADDER-CATALOG-FLIP` slice doc before broader billing/catalog edits | Architect + AI Agent (Developer) | doc review only at this phase | new baseline slice artifact |

### Exact write scope of first governance wave

Первая governance-wave для active execution ограничена следующими артефактами:

| Path / module | Allowed action | Reason |
| --- | --- | --- |
| `DEVELOPMENT_PLAN.md` | update | зафиксировать active pilot slice, controller/reviewer governance, exact write scope |
| `docs/GRACE_ARTIFACTS.md` | update | синхронизировать artifact inventory и execution loop с active governance |
| `GRACE.md` | read-only reference | canonical source для проверки, без локального policy drift |

Вне этого scope для первой governance-wave остаются backend/frontend code modules, дополнительные rollout notes и новые slice docs. Их открытие требует отдельного controller decision и нового packet.

## 🏗 Архитектура v3.0 (Hybrid)

### 1. Telegram Centric Auth
- **Вход:** Через Telegram Widget (Web) или `initData` (Mini App).
- **Идентификатор:** `telegram_id`.
- **Профиль:** Хранит настройки, баланс, статус партнера.
- **Onboarding:** Сбор данных (Дата/Время/Место) после входа. Режим "Без времени рождения" (Космограмма).

### 2. Billing Engine
- **Провайдер:** ЮKassa (поддержка рекуррентных платежей + СБП).
- **Модель:**
  - **Подписка:** 990₽/мес (полный доступ).
  - **Разовая покупка:** 299₽ за отчет.
- **Управление:** Кнопка "Управление подпиской" в профиле.

### 3. Referral & Viral System
- **Инвайт-ссылка:** `t.me/AstroGraceBot?start=ref_USERID`.
- **Логика вознаграждения:**
  - **Для Новичка (Referee):** 15 дней Premium-доступа бесплатно сразу после регистрации (Trial).
  - **Для Пригласившего (Referrer - User):** +15 дней к текущей дате окончания подписки (сдвиг даты списания).
  - **Для Партнера (Referrer - Partner):** 20% (настраиваемо) от платежей реферала на баланс (вместо дней). Режим включается админом.
- **Вывод:** Ручной, от 1000₽, через запрос в поддержку.

### 4. LLM Optimization (Cost/Quality)
- **High-End (Claude 3.5 / GPT-4o):** Для платных глубоких отчетов.
- **Low-Cost (GPT-4o-mini / Flash):** Для ежедневных гороскопов, хораров.
- **Hybrid Mode:** Шаблонизация аспектов + персонализация вступления.

### 5. Frontend (Mobile First)
- **Лендинг:** Продающая страница -> Бот.
- **App:** PWA / SPA внутри Telegram.
- **UI:** Bottom Navigation (Сегодня, Прогнозы, Создать, Профиль).

---

## 🛠 Компоненты и Модели

### Database (New Models)
- `User`: `telegram_id`, `is_partner` (bool), `balance` (decimal), `subscription_active_until` (datetime), `birth_time_known` (bool).
- `Subscription`: `status`, `next_billing_at`, `payment_method_id` (YooKassa).
- `Referral`: Связь `referrer` -> `referee`, `reward_type` (days/money).

### Integrations
- **Telegram Bot:** Aiogram 3.x.
- **Payments:** Yookassa SDK.

---

## 📈 Roadmap

1.  **Database Layer:** Миграции Users, Billing, Referrals.
2.  **Logic:** Сервис начисления бонусов (Дни vs Деньги).
3.  **Bot:** Вход, обработка реф-ссылок.
4.  **Frontend:** UI профиля и ленты.
5.  **Billing:** Интеграция платежей.
