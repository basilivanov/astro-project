# DayBrief QA Checklist

Канонический QA-чеклист для поверхности Today/DayBrief в рамках Wave 5. Документ нужен для ручной проверки основных состояний экрана, CTA-сценариев Premium и базовой telemetry-цепочки без чтения всей реализации.

## Scope и кодовые точки

- Основная поверхность Today рендерится в `frontend/app/page.tsx`.
- DayBrief-секции и CTA собираются в `frontend/components/today/daybrief-sections.tsx`.
- Канонические Playwright-сценарии находятся в `frontend/e2e/today-daybrief.spec.ts`.

## Перед началом

1. Откройте Today surface в локальном окружении с доступным frontend runtime.
2. Убедитесь, что mock/bootstrap сценарий для Telegram активен, если проверка идёт не из реального Telegram-контекста.
3. Для сверки DOM и copy используйте `data-testid` из фронта: `home-feed-page`, `feed-fallback-banner`, `today-verdict`, `today-windows`, `today-actions`, `today-risks`, `today-explainability`, `today-cta-panel`.
4. Для telemetry-проверок ориентируйтесь на события, которые фиксируются в e2e-спеке: `today.brief_view`, `today.score_tap`, а также home/feed-события при bootstrap и state transitions.

## Сценарий 1 — Loading state

Цель: убедиться, что экран не крашится и показывает промежуточное состояние, пока `/api/profile` и `/api/feed/today` ещё загружаются.

1. Откройте Today surface в состоянии, где ответы API задерживаются или страница только что смонтирована.
2. Проверьте, что shell страницы рендерится без белого экрана/500.
3. Проверьте, что статус поверхности соответствует loading-состоянию, а пользователь не видит битый layout.
4. Убедитесь, что после завершения загрузки экран переходит либо в `ready`, либо в `fallback`, либо в `error/empty` без повторного монтирования shell.

Ожидаемый результат:

- `frontend/app/page.tsx` сохраняет `ConsumerPageShell` и semantic shell даже во время загрузки.
- Нет runtime crash, hydration mismatch или пустого HTML вместо Today surface.
- Дальнейший переход в итоговое состояние происходит плавно и без пропажи hero/status блока.

## Сценарий 2 — Ready state

Цель: проверить основной DayBrief DTO happy-path.

1. Откройте Today surface с валидным `day_brief` payload.
2. Проверьте hero/summary: headline, subhead и статус `Готово`.
3. Проверьте, что видны ключевые секции:
   - `today-verdict`
   - score-карточки вроде `today-score-energy`
   - `today-windows`
   - `today-actions`
   - `today-risks`
   - `today-explainability`
   - `today-cta-panel`
4. Нажмите минимум на один score tile и убедитесь, что UI остаётся интерактивным.
5. Сверьте copy и структуру с `frontend/components/today/daybrief-sections.tsx`.

Ожидаемый результат:

- Все основные секции отображаются без fallback-banner.
- Score tiles кликабельны и не ломают layout.
- Explainability/personalized factors рендерятся только как поддерживающая секция, без дублирования hero copy.

## Сценарий 3 — Fallback state

Цель: проверить деградацию, когда точный DayBrief DTO недоступен и фронт показывает безопасный fallback.

1. Откройте Today surface в состоянии `fallback`.
2. Проверьте наличие `feed-fallback-banner`.
3. Убедитесь, что текст баннера явно маркирует fallback-режим, а не маскирует его под обычный ready-state.
4. Проверьте, что при fallback всё ещё доступны базовые блоки навигации и ориентации дня:
   - `today-verdict`
   - `today-windows`
   - `today-cta-panel`
5. Если используется legacy visual fallback, проверьте, что copy прямо упоминает “визуальный fallback”.

Ожидаемый результат:

- У пользователя остаётся usable Today screen без 500/blank state.
- Fallback-banner визуально отделён от ready-state.
- CTA и основные ориентиры дня остаются доступны даже в degraded mode.

## Сценарий 4 — Premium CTA modes

Цель: проверить, что Premium CTA различает referral и renewal сценарии.

### 4A. Referral CTA

1. Откройте ready-state, где `premium.show_upgrade_cta = false`, а secondary CTA ведёт в referral flow.
2. Проверьте `today-cta-copy`.
3. Проверьте `today-cta-premium`.

Ожидаемый результат:

- В helper copy есть явное указание на реферальный сценарий.
- Кнопка содержит badge/copy уровня `Реферал`.
- Label вторичного CTA соответствует referral-entrypoint, а не renewal.

### 4B. Renewal CTA

1. Откройте ready-state, где Premium активен, но требуется продление (`show_upgrade_cta = true`).
2. Проверьте `today-cta-copy`.
3. Проверьте `today-cta-premium`.

Ожидаемый результат:

- Helper copy явно предлагает продлить Premium.
- Secondary CTA содержит badge/copy уровня `Продление`.
- Сценарий renewal визуально отличается от referral и не смешивает оба entrypoint.

## Сценарий 5 — Telemetry smoke

Цель: подтвердить, что Today/DayBrief поверхность не только рендерится, но и отсылает базовые аналитические события.

1. Откройте ready-state Today surface.
2. Дождитесь первичного рендера.
3. Нажмите на score tile, например `today-score-energy`.
4. Проверьте telemetry/event buffer в используемом окружении или через Playwright assertions.

Минимум нужно подтвердить:

- Есть стартовое событие просмотра поверхности (`today.brief_view` или эквивалентное home/feed view событие).
- Есть событие score interaction: `today.score_tap`.
- События не теряют контекст `flow_id`/surface/block, который задаётся в `frontend/app/page.tsx`.

Подсказка по сверке:

- Каноническая проверка уже описана в `frontend/e2e/today-daybrief.spec.ts`, где читается буфер `__analyticsEvents` и проверяется наличие view/tap событий.

## Ручной smoke перед handoff

Выполните именно эти команды как минимальный acceptance-набор для документации/QA handoff:

```bash
cd frontend && npm exec tsc -- --noEmit
./scripts/run_e2e.sh e2e/today-daybrief.spec.ts -g "QA checklist smoke"
```

## Что считать fail

Любой из пунктов ниже означает, что Today/DayBrief поверхность не проходит QA-checklist:

- страница даёт 500, blank screen или hydration/runtime crash;
- fallback state не маркирован явно;
- ready state не показывает ключевые секции DayBrief;
- referral/renewal Premium CTA не различаются по copy/entrypoint;
- telemetry smoke не подтверждает хотя бы view + score tap события;
- ручные acceptance-команды падают.
