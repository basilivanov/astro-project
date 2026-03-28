# Wave 5 Readiness

Короткий статус для руководства по пакету Waves 1-5: контракты и surface migration завершены, acceptance-профили унифицированы, ключевые hardening/smoke артефакты лежат в репозитории и используются как каноничные точки входа.

## 1) Статус волн

| Wave | Статус | Что зафиксировано |
| --- | --- | --- |
| Wave 1 — Contracts | Done | Закреплены DTO/brief-контракты для `DayBrief` и `WeekBrief`, документация и acceptance опираются на новый contract-first поток. |
| Wave 2 — Day backend + Today | Done | `Today` переведён на DTO-native `DayBrief`, задокументирован surface и блоки Today, убрана зависимость от legacy top-level synthesis. |
| Wave 3 — Week backend + Week | Done | `Week` опирается на `WeekBrief`/week map поток, задокументированы факторы, envelope/read-path и deterministic fallback evidence. |
| Wave 4 — Frontend hardening | Done | Добиты TypeScript/compliance хвосты, dev/prod flow и DTO docs оформлены, Today/Week surfaces стабилизированы для acceptance. |
| Wave 5 — Hardening / Quality loop | Done | Зафиксированы acceptance-профили, quality telemetry, smoke wrapper и handoff-ready smoke loop для backend + frontend. |

## 2) Каноничные acceptance-профили

| Профиль | Команда | Что покрывает |
| --- | --- | --- |
| Backend quick | `docker exec astro-project-backend-1 python3 scripts/pipeline.py` | Быстрая обязательная backend-проверка изменённой логики: pipeline, совместимость окружения, базовый contract/logging/runtime smoke. |
| Frontend quick | `./scripts/run_e2e.sh --last-failed` | Быстрая обязательная frontend/E2E-проверка после UI-изменений или повторный прогон последнего failing набора через Playwright container. |
| Smoke | `./scripts/run_smoke.sh` | Каноничный handoff-профиль: backend quick + целевой Playwright smoke набор (`admin`, `core-ux`, `report-create`, `quality`) с общим PASS/FAIL итогом. |

## 3) Что уже подтверждено

- GitHub publish / public repo flow задокументирован и приведён к каноничному процессу публикации и prod push.
- DTO docs для Today/Week surface оформлены и привязаны к текущим brief-контрактам.
- Today/Week hardening выполнен: surface migration, TS compliance, env-drift hardening и acceptance stability зафиксированы.
- Quality telemetry подтверждена: prompt/version/seed, trace/logging evidence и quality smoke входят в текущий handoff-контур.
- Smoke loop подтверждён как единая canonical acceptance entrypoint перед handoff/UAT.

## 4) Новые артефакты

| Артефакт | Назначение |
| --- | --- |
| `docs/PRODUCT_SURFACE_BRIEF.md` | Краткая карта продуктовых surface'ов и их текущих brief/DTO опорных точек для руководства и handoff. |
| `docs/TODAY_BLOCKS.md` | Структура блоков `Сегодня`, display conditions, DTO reuse map и telemetry/events для Today surface. |
| `docs/WEEKMAP_FACTORS.md` | Факторы WeekMap/WeekBrief, backend aggregation flow, envelope/read path и границы ответственности frontend/backend. |
| `docs/DEV_VS_PROD_FLOW.md` | Каноничный dev-vs-prod Git/GitHub flow, правила ветвления, smoke/acceptance перед push и publish checklist. |
| `docs/TESTING_GUIDE.md` | Текущая тестовая матрица и правила запуска acceptance-профилей: backend quick, frontend quick, smoke и более широкие прогоны. |
| `scripts/run_smoke.sh` | Единый smoke wrapper, который последовательно запускает backend quick и целевой Playwright smoke набор и возвращает успех только при PASS обоих этапов. |

## Итог

Пакет Waves 1-5 можно считать readiness-complete на уровне документации и acceptance governance: статус волн зафиксирован, каноничные acceptance-команды определены, а ключевые hardening/telemetry/smoke артефакты оформлены в репозитории.
