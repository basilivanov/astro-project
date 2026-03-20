# План внедрения GRACE baseline в roadmap проекта

## 1. Цель документа

Этот план фиксирует, как внедрять baseline `strict GRACE` в текущий roadmap проекта без полного архитектурного переворота. Подход: не «делаем GRACE отдельно», а встраиваем его как operating model в уже актуальные продуктовые приоритеты.

Текущие опорные приоритеты, которые нужно связать с GRACE:
- `frontend natal admin`
- `personalized daily`
- `natal summary fix`

Опорные GRACE-слайсы из проекта:
- `GRACE_SLICE_NATAL_DAILY.md`
- `GRACE_SLICE_ONE_OFF_ENTITLEMENTS.md`
- `GRACE_SLICE_FORECAST_LADDER.md`
- `GRACE_SLICE_ASTRO_QUALITY_RUBRIC.md`
- baseline policy из `GRACE.md`

---

## 2. Что берем из baseline GRACE как обязательный минимум

Из `GRACE.md` для этого проекта нужно брать не весь «идеальный пакет сразу», а минимально-обязательный baseline, который даст управляемость roadmap.

### 2.1 Обязательные артефакты baseline

Для активного GRACE rollout нужно завести и поддерживать в актуальном состоянии:
- `docs/requirements.xml`
- `docs/technology.xml`
- `docs/development-plan.xml`
- `docs/knowledge-graph.xml`
- `docs/verification-matrix.md`

### 2.2 Обязательные execution-ритуалы

Для каждой значимой волны работ по active slice исполняем:
- фиксацию `active slice` и `write scope`
- module contracts для затронутых модулей
- module maps для затронутого фронта/бэка
- compact change summary после meaningful change packet
- deterministic verification + trace evidence
- controller -> worker -> reviewer loop хотя бы в легкой форме

### 2.3 Что добавляем как локальную адаптацию проекта

Чтобы baseline не остался абстракцией, вводим project-level артефакт:
- `docs/GRACE_ARTIFACTS.md`

В нем фиксируем:
- какие XML/graph/verification артефакты уже существуют
- какие модули покрыты contracts/maps
- какие prompts считаются baseline prompts
- какие regression hooks обязательны для каждого slice
- какие feature flags и rollout gates относятся к каждому GRACE slice

Это не заменяет `GRACE.md`, а служит project index для быстрых handoff между агентами.

---

## 3. Соответствие текущих приоритетов и GRACE roadmap

### 3.1 `frontend natal admin`

Наиболее близко ложится на связку:
- `GRACE_SLICE_ONE_OFF_ENTITLEMENTS.md`
- `GRACE_SLICE_FORECAST_LADDER.md`

Почему:
- admin entitlements уже описаны как canonical grant path
- фронтенд еще не полностью синхронизирован с entitlement/runtime model
- есть явный residual frontend delta: `/create`, `/billing/complete`, `/reports`, `frontend/lib/product-billing.ts`

GRACE-фокус для этого приоритета:
- зафиксировать access model как business invariant
- сделать module contracts для admin/access/billing surfaces
- связать user flows с verification matrix и E2E gates
- не допустить drift между admin truth, catalog truth и read/create truth

### 3.2 `personalized daily`

Наиболее близко ложится на:
- `GRACE_SLICE_NATAL_DAILY.md`
- `GRACE_SLICE_ASTRO_QUALITY_RUBRIC.md`
- частично `GRACE_SLICE_FORECAST_LADDER.md`

Почему:
- daily уже определен как facts-first слой полезности
- в slice явно зафиксированы состояния `ready/fallback/empty/error`
- quality rubric задает правильный порог: для daily не нужен длинный эссе-режим, нужен короткий, персонализированный, практичный и mobile-readable output

GRACE-фокус для этого приоритета:
- закрепить daily как отдельный slice с ясным payload contract
- зафиксировать, что daily должен опираться на реальные facts/semantic layer, а не на свободную LLM-импровизацию
- добавить trace assertions по personalization source, fallback path и block readability

### 3.3 `natal summary fix`

Наиболее близко ложится на:
- `GRACE_SLICE_NATAL_DAILY.md`
- `GRACE_SLICE_ASTRO_QUALITY_RUBRIC.md`

Почему:
- `M-NATAL-SUMMARY-LAYER` уже выделен как отдельный проблемный слой
- в slice прямо записано, что `executive_summary` частично нестабилен, а `final_synthesis` местами слишком статичен
- quality rubric требует facts-first, cross-links, practical usefulness и mobile readability

GRACE-фокус для этого приоритета:
- оформить summary-layer как отдельный active slice
- привязать summary к `insight_pack` и `cross_links` как к hard contract
- проверять не только JSON validity, но и trace evidence, что summary verbalize deterministic conclusions

---

## 4. Ключевые этапы внедрения GRACE по roadmap

Ниже — рекомендуемый порядок внедрения baseline без лишней перегрузки.

## Этап 0. Зафиксировать GRACE baseline как рабочий контур проекта

### Что делаем
- Создаем `docs/GRACE_ARTIFACTS.md` как точку входа в project-level GRACE.
- Вносим туда список активных slice-ов:
  - `natal + forecast + daily frontend`
  - `one-off entitlements`
  - `forecast ladder`
  - `astro quality rubric`
- Фиксируем canonical test hooks и feature flags.
- Фиксируем, какие модули уже являются anchor-модулями для reasoning.

### Зачем
Без этого GRACE останется набором документов, а не operable roadmap baseline.

### Минимальный результат
- есть единый индекс артефактов
- новый агент понимает, какие документы каноничны
- handoff не зависит от памяти исполнителя

---

## Этап 1. Собрать active-slice artifact pack под текущие приоритеты

### Что делаем
Для текущих задач обновляем или дополняем:
- `docs/requirements.xml`
- `docs/development-plan.xml`
- `docs/knowledge-graph.xml`
- `docs/verification-matrix.md`

### Как резать по slice

#### Slice A — Natal Summary Fix
Use cases:
- корректный `executive_summary`
- корректный `final_synthesis`
- summary опирается на `insight_pack`
- summary mobile-readable и не уходит в generic/fallback drift

#### Slice B — Personalized Daily
Use cases:
- daily feed персонализирован по пользователю/контексту
- fallback не ломает UX
- payload остается кратким и пригодным для Home surface
- quality floor не проседает в cheap/fallback режимах

#### Slice C — Frontend Natal Admin / Entitlements
Use cases:
- admin grant truth совпадает с frontend access truth
- `/create`, `/billing/complete`, `/reports`, `/api/users/me` говорят одну и ту же access-правду
- one-off/runtime bridge не ломает legacy flows

### Зачем
Это превращает roadmap из списка задач в адресуемую execution model с use-case IDs, module IDs и verification связями.

---

## Этап 2. Ввести module contracts и module maps для активных модулей

Это первый практический GRACE-ритуал, который должен исполняться на задачах сразу.

### 2.1 Для `natal summary fix`

Оформить contracts/maps как минимум для:
- `backend/app/services/report_workflow.py`
- `backend/app/llm/orchestrator.py`
- `backend/app/reporting/section_templates.py`

Нужно явно зафиксировать:
- откуда summary берет deterministic truth
- где допустим fallback
- какие секции summary-layer считаются critical entrypoints
- какие invariants нельзя ломать (`insight_pack`, `cross_links`, block contract, concise close)

### 2.2 Для `personalized daily`

Оформить contracts/maps как минимум для:
- `backend/app/services/personalized_daily.py`
- `backend/app/services/forecast_semantics.py`
- frontend read/home surfaces, где рендерится daily
- `frontend/components/blocks/report-renderer.tsx` если daily идет через shared blocks

Нужно явно зафиксировать:
- источник personalization
- fallback policy
- allowed block types
- mobile-first constraints

### 2.3 Для `frontend natal admin`

Оформить contracts/maps как минимум для:
- `backend/app/services/access_control.py`
- `backend/app/services/one_off_entitlements.py`
- `frontend/app/create/page.tsx`
- `frontend/app/billing/complete/page.tsx`
- `frontend/app/reports/page.tsx`
- `frontend/lib/product-billing.ts`

Нужно явно зафиксировать:
- кто владеет access decision
- где entitlement только отображается, а где реально consume-ится
- как frontend выбирает pay/generate/resume branch
- как admin grant converges с user-facing access model

---

## Этап 3. Зафиксировать baseline prompts и prompt contracts

GRACE roadmap в этом проекте нельзя внедрить без prompt layer, потому что критические бизнес-результаты зависят от LLM orchestration.

### Что делаем
В `docs/GRACE_ARTIFACTS.md` добавляем раздел `Baseline prompts`:
- какие prompt templates являются canonical
- какие runtime hints обязательны
- где проходит граница между deterministic context и model verbalization

### Где это особенно важно

#### Natal Summary Fix
- `executive_summary`
- `final_synthesis`
- sections, где style hint уже подключен

Нужно закрепить правило:
- prompt не придумывает новый каркас личности
- prompt verbalize-ит deterministic conclusions из `insight_pack` и `cross_links`

#### Personalized Daily
Нужно закрепить правило:
- daily prompt опирается на semantic layer / forecast facts
- не уходит в generic inspiration text
- держит короткий mobile-first format

#### Frontend Natal Admin
Prompt layer вторична, но нужно зафиксировать, что access/billing/admin flows не должны зависеть от prompt-specific условий.

---

## Этап 4. Привязать regression hooks к каждому GRACE slice

Это критичный этап, потому что без regression hooks baseline останется неисполняемым.

### 4.1 Общий принцип
В `docs/GRACE_ARTIFACTS.md` и `docs/verification-matrix.md` фиксируем для каждого slice:
- deterministic checks
- targeted backend tests
- targeted frontend E2E
- trace assertions
- rollout flags

### 4.2 Hooks для `natal summary fix`

Обязательные hooks:
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- точечные тесты на natal section context / summary behavior
- при необходимости repro-тест на summary leak/regression

Нужно проверять:
- summary опирается на нужный context
- block contract не сломан
- fallback path не маскирует regression
- output не деградировал в generic summary

### 4.3 Hooks для `personalized daily`

Обязательные hooks:
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- точечные тесты для `personalized_daily` / `forecast_semantics`
- E2E или targeted UI smoke для Home/daily surface

Нужно проверять:
- personalization source корректен
- `ready/fallback/empty/error` состояния отрабатывают
- mobile-readable output не ломается
- daily не скатывается в seed-random/generalized payload

### 4.4 Hooks для `frontend natal admin`

Обязательные hooks:
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- targeted tests для entitlements/admin alignment
- Playwright E2E по admin + create/billing/read flows

Нужно проверять:
- admin grant -> `/api/users/me` -> `/create` -> `/read` согласованы
- one-off bridge работает под flags
- catalog/create/billing complete не расходятся по access truth

---

## Этап 5. Встроить trace evidence и reviewer packets

Это главный переход от «просто задач» к GRACE execution.

### Что делаем
Для каждого значимого change packet добавляем короткий reviewer-friendly набор:
- active slice
- затронутые module IDs
- use cases / scenario IDs
- какие traces собраны
- какие tests/gates пройдены
- какие known gaps остаются

### Практически в этом проекте
Достаточно lightweight формата:
- change summary в PR/task note
- ссылки на test evidence
- если был провал — compact failure packet

### Где особенно важно
- `natal summary fix`, потому что regression может быть не syntactic, а semantic
- `personalized daily`, потому что fallback легко маскирует потерю personalization
- `frontend natal admin`, потому что regressions часто живут на стыке backend truth и frontend UX

---

## 5. Рекомендуемый порядок внедрения по задачам

## Wave 1 — Foundation

### Выполняем
1. Создать `docs/GRACE_ARTIFACTS.md`.
2. Подтянуть в него active slices, anchors, feature flags, test hooks.
3. Обновить `docs/verification-matrix.md` под три текущих приоритета.
4. Описать module contracts для минимального набора активных модулей.

### Почему сначала это
Это минимальная цена входа, после которой roadmap начинает исполняться по GRACE, а не «по памяти команды».

---

## Wave 2 — `natal summary fix`

### Выполняем
1. Выделяем отдельный active slice `M-NATAL-SUMMARY-LAYER`.
2. Фиксируем summary prompt contract.
3. Добавляем/обновляем repro tests на `executive_summary` и `final_synthesis`.
4. Привязываем acceptance к quality rubric: facts-first, cross-links, practical value, mobile readability.

### Результат
`natal summary fix` становится первым полноценным GRACE-managed slice.

---

## Wave 3 — `personalized daily`

### Выполняем
1. Формализуем daily payload и personalization contract.
2. Отделяем deterministic facts от LLM verbalization.
3. Добавляем regression hooks на states `ready/fallback/empty/error`.
4. Проверяем fit с forecast ladder: `Day` как короткий free layer, а не мини-натал.

### Результат
Daily получает управляемый quality floor и перестает быть «скользким» слоем, где personalization трудно доказать.

---

## Wave 4 — `frontend natal admin` / entitlements alignment

### Выполняем
1. Формализуем access-control contracts между backend и frontend.
2. Синхронизируем catalog/create/billing complete/admin surfaces через единый access truth.
3. Привязываем rollout к feature flags и explicit regression pack.
4. Фиксируем reviewer packet для admin/access regressions.

### Результат
Admin/frontend rollout идет как controlled GRACE slice, а не как серия несвязанных hotfix-ов.

---

## 6. Что именно должно появиться в проекте как результат baseline

Минимальный комплект внедрения:
- `docs/GRACE_ARTIFACTS.md`
- обновленные `docs/requirements.xml`, `docs/development-plan.xml`, `docs/knowledge-graph.xml`, `docs/verification-matrix.md`
- contracts/maps для active modules по трем приоритетам
- baseline prompts registry
- regression hooks registry
- lightweight controller/reviewer packet discipline для change waves

---

## 7. Краткая привязка «задача -> какие GRACE модули/ритуалы исполняем»

### `natal summary fix`
Исполняем:
- active slice declaration
- module contract: `M-NATAL-SUMMARY-LAYER`
- prompt contract для summary sections
- verification matrix update
- targeted repro tests
- trace evidence по `insight_pack -> summary output`

### `personalized daily`
Исполняем:
- active slice declaration
- module contracts для `personalized_daily` и semantic layer
- payload/schema freeze
- baseline prompt rules
- regression hooks на daily states
- trace evidence по personalization source

### `frontend natal admin`
Исполняем:
- active slice declaration
- access-control contracts
- frontend module maps для `/create`, `/reports`, `/billing/complete`
- regression hooks по admin/billing/create/read
- feature-flag rollout gates
- reviewer packet по access truth alignment

---

## 8. Итог

Правильное внедрение GRACE baseline в этом проекте — это не отдельный «методологический проект», а наложение artifact-driven discipline на уже актуальные product slices.

Рекомендуемый practical baseline:
1. сначала зафиксировать `GRACE_ARTIFACTS` и verification matrix;
2. затем прогнать через GRACE first-class slice `natal summary fix`;
3. после этого формализовать `personalized daily`;
4. затем довести `frontend natal admin` / entitlement alignment как rollout-heavy slice;
5. на каждом шаге требовать не только тесты, но и trace evidence + reviewer-friendly packets.

Такой порядок дает быстрый operational эффект и не требует полного re-bootstrap всего проекта.
