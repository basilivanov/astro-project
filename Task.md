# Astro Premium — план редизайна (русская версия)

## Итерация 1 (максимальный эффект быстро)

### 1. DAY-BRIEF-API-CONTRACT
- Реализовать агрегированный endpoint `DayBrief` (отдельный `/api/day/brief` или расширение текущего feed API).
- Структура `DayBrief` включает: `summary` (headline, subhead, `day_type`), `scores` по доменам (энергия, работа, отношения, фокус), массив `windows` с временными интервалами (`best|soft|caution`), массив `best_uses`, массив `risks`, список `personalized_factors` с impact + человеческим объяснением, блок `explainability` (confidence, использовано ли точное время рождения, количество факторов).
- Расчётные приоритеты на день (строго из ТЗ):
  - 35% — быстрые персональные транзиты к личным точкам;
  - 25% — лунная динамика и внутридневные окна;
  - 20% — медленный персональный фон (длительные транзиты, current theme);
  - 15% — натальная чувствительность/активные дома по сфере;
  - 5% — редкие усилители (lots, fixed stars) при повторном подтверждении.
- API должен фильтровать противоречивые сигналы и выдавать один канонический сценарий дня.
- Acceptance: pydantic-схема, unit-тесты на агрегацию/веса/сериализацию, документация в `docs/GRACE_ARTIFACTS.md`, `docker exec astro-project-backend-1 python3 scripts/pipeline.py` — PASS.

### 2. DAY-BRIEF-UI-REPLACE-HOME
- Полностью заменить текущий home (`/`) на экран «Сегодня» в терминах пользовательской пользы: вердикт дня, тип дня (push/balance/caution/deep_focus/recovery), карточки доменов с оценками, временная шкала окон, блок «что делать» vs «избегать», explainability-чипы («почему так»), CTA к `/week` и к платёжному сценарию.
- Убрать вкладки «Лента/Неделя/Каталог» сверху; доступ в каталог оставить через CTA (например, «Заказать отчёт»).
- Обновить home-аналитику: новые block/semantic_block, события `home.day_brief_view` и т. п.
- Acceptance: новый Playwright-спек (например, `frontend/e2e/day-brief.spec.ts`) проверяет вердикт, окна, действия/риски, premium CTA; `./scripts/run_e2e.sh e2e/day-brief.spec.ts` + `--last-failed` зелёные.

### 3. WEEK-MAP-API-CONTRACT
- Добавить агрегат `WeekMap`: `thesis`, `theme`, `day_cards` (день недели, score, mode, headline, best_for, avoid), `domains` (work/relationships/energy и т. д.), `major_factors`, `actions`, `risks`, `deep_sections` (ссылки на подробные блоки), `explainability`.
- Расчётные приоритеты на неделю:
  - 30% — медленный фон периода (прогрессии, solar arc, профекции/time lord, соляр);
  - 25% — точные недельные активации/станции;
  - 20% — профекция/солярная тема/управители периода;
  - 15% — декомпозиция по дням (лунная волна, доменная карта);
  - 10% — редкие усилители.
- Acceptance: схема + unit-тесты на веса и explainability; документация обновлена.

### 4. WEEK-MAP-UI-REDESIGN
- Перестроить `/week` в «Карту недели»: сверху тезис и тема недели, карта лучших/осторожных дней, три ключевые линии (что делать, что не делать, где прогресс), блоки действий/рисков, доменные карточки, explainability.
- Убрать служебные статусы («Навигатор недели», «Секции»), оставить лаконичные пользовательские формулировки.
- Сохранить `CatalogCheckoutResumeBanner`, но сделать его второстепенным относительно полезной информации.
- Acceptance: обновить/добавить Playwright-спек (например, расширить `week-home-refresh.regression.spec.ts`) для проверки тезиса/карты/доменов; targeted run PASS.

### 5. DATA-WEIGHTS-CALIBRATION + Агрегационный пайплайн
- Имплементировать helper, который применяет весовые таблицы `DayBrief`/`WeekMap` и поддерживает explainability (возврат топ-факторов с impact).
- Прописать пайплайн для дня:
  1. Определяем текущий жизненный фон пользователя.
  2. Фиксируем активные темы карты на период.
  3. Берём топ точных транзитов суток.
  4. Считаем лунную тактику и окна.
  5. Сопоставляем всё с доменами.
  6. Фильтруем противоречия, выбираем главный сценарий.
  7. Собираем headline/best/avoid/windows/explainability.
- Пайплайн недели:
  1. Определяем тему периода (прогрессии/дирекции/профекции/соляр).
  2. Выделяем наиболее активные сферы.
  3. Ловим точные триггеры недели.
  4. Разкладываем неделю на day_cards.
  5. Считаем доменные оценки.
  6. Выбираем главный тезис, стратегии, риски.
  7. Формируем deep sections.
- Acceptance: unit-тесты на пайплайны (входные mocked factors → ожидаемый вес/выход), документация.

### 6. NAVIGATION-AND-CATALOG-REFLOW
- Удалить вкладку «Каталог» из первичной навигации; входы в каталог/отчёты оставить через CTA внутри Today/Week.
- Убедиться, что referral/premium сценарии доступны; обновить телеметрию и `useTelegram` (Today — default entry).

### 7. POLICY: что показываем пользователю
- На UI остаются: выводы человеческим языком, доменные оценки, окна, сильные/слабые дни, 2–4 причины «почему так», confidence.
- Под капотом оставляем: сырые таблицы аспектов, десятки вторичных факторов, внутренние веса, шумные методы без подтверждений.
- Документировать политику → `docs/GRACE_ARTIFACTS.md` и `Task.md`.

## Итерация 2 (premium-дифференциация)

### 8. EXPLAINABILITY-CONFIDENCE-BLOCK
- В `DayBrief` и `WeekMap` выводим explainability-чипы: фактор/impact/человеческое объяснение + confidence score + признак «использовано точное время рождения».
- Добавить аналитическое событие `explainability.view`.
- Acceptance: UI рендерит чипы, Playwright проверяет наличие + telemetry payload.

### 9. PERSONAL-TIME-WINDOWS
- Расширить данные персональными временными окнами (best/caution/soft) как для дня, так и для недели; учитывать time-lord/profections где применимо.
- Acceptance: unit-тесты на слияние окон, Playwright-проверка визуализации timeline.

### 10. DOMAIN-ACTIONS-RISKS-LINKED
- Каждую рекомендацию/риск связываем с `factor_id` + временным горизонтом; UI/аналитика должны получать этот ID.
- Acceptance: схема + тесты (в том числе analytics snapshot) подтверждают наличие `factor_id`, документация обновлена.

---

## Текущие/исторические задачи (на русском)

### VM-BOT-NOTIFY
- Добавлены `tests/test_bot_notification.py` (телеметрия blocked chat/non-fatal) и `frontend/e2e/bot-notify.spec.ts` (Playwright покрытие).
- Обновлён `backend/app/services/notification.py` с helper для delivery telemetry.

### Партнёрские награды (Referral Partner Reward)
- `tests/test_referral_partner_reward.py` закрывает 15-дневную политику, защиту от двойных начислений и телеметрию.
- Acceptance: таргетированный pytest + backend quick.

### Auth/Profile Flow
- `tests/test_auth_profile_flow.py` проверяет gateway auth, ожидание профиля, завершение профиля и корреляцию.

### Start Gateway
- `frontend/e2e/start-gateway.spec.ts`, обновлён `frontend/app/start/page.tsx`, артефакты задокументированы.

### Admin Operations / RBAC / Diagnostics
- Соответствующие e2e спеки (`admin.operations`, `admin.rbac`, `admin.diagnostics`), обновлённые страницы и документация. Acceptance — Playwright pass.

### Voice Flow
- `tests/test_voice_flow.py` и `bot/tests/test_voice_flow.py`; внутри текущего контейнера pytest помечен как skipped (нет `bot/app`), но quick pipeline PASS.

### Read Failure Telemetry
- Новые unit + e2e (`tests/test_read_failure_flow.py`, `frontend/e2e/report-failure.spec.ts`), обновлён `frontend/app/read/[id]/page.tsx` и каталоговые компоненты.

### Report Workflow E2E
- `frontend/e2e/report-workflow.spec.ts` (async lifecycle + resume telemetry) — PASS.

### Обновление home/week поверхностей (март 2026)
- Табы, подсказки, premium блок, weekly traffic light; `frontend/e2e/week-home-refresh.regression.spec.ts` покрывает.

### YooMoney интеграция
- Бэкенд: alias env, stricter validation, failure-return URL.
- Фронт: `billing/complete` UX, CTA back/swipe, новая Playwright-спека.
- Acceptance: backend pytest, pipeline, targeted e2e; известный flake в mock paid flow задокументирован.

### Git / production snapshot (2026-03-27)
- Проверен `origin`: рабочий GitHub remote указывает на `git@github.com:basilivanov/astro-project.git`; репозиторий `git@github.com:basil/astro-project.git` не существует (`Repository not found`), поэтому remote не менялся.
- Подтверждён пользовательский git config: `user.name=Snapshot Bot`, `user.email=snapshot@example.com`.
- Production-ветка `prod-release-20260327` уже существует локально и на origin; снимок готовится без `--force`, поверх текущего состояния дерева (Waves 1–2 + docs + сопровождающие backend/frontend/tests изменения).
- Acceptance для git-этапа: `git remote -v` показывает GitHub origin, обычный `git push origin prod-release-20260327` проходит успешно, лог команд фиксируется без секретов.
