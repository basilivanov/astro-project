# GRACE Slice: Forecast Ladder / Day-Week-Month-Year

**Статус:** рабочий продуктовый slice; `natal_master` + `month_forecast` + `year_forecast` + `solar_return` one-off bridge synced behind flags  
**Дата:** 2026-03-20  
**Язык:** RU  
**Опора на код:** `frontend/app/page.tsx`, `frontend/app/week/page.tsx`, `frontend/app/read/[id]/page.tsx`, `frontend/app/reports/page.tsx`, `frontend/app/reports/history/page.tsx`, `frontend/app/create/page.tsx`, `frontend/components/consumer-page-shell.tsx`, `frontend/lib/product-billing.ts`, `backend/app/main.py`, `backend/app/services/report_workflow.py`, `backend/app/services/access_control.py`, `backend/app/services/one_off_entitlements.py`, `backend/app/core/config_business.py`, `backend/app/core/feature_flags.py`, `stellium_engine.py`, `docs/BILLING_CATALOG_ALIGNMENT_2026-03-19.md`, `docs/BLOCKS_SCHEMA.md`, `docs/REPORT_STRUCTURES.md`, `GRACE_SLICE_NATAL_DAILY.md`, `STYLE_CONTRACT.md`

## 1. Цель slice

Зафиксировать каноническую продуктовую матрицу для лестницы прогнозов `Day / Week / Month / Year` и ее связь с `Natal / Solar / Synastry / Horary`, не отрываясь от того, что уже реально есть в маршрутах frontend и в backend-расчетах.

Этот документ не меняет код. Он нужен как опорный артефакт для следующего product/backend/frontend среза.

## 1.1 Sync note 2026-03-20

- `/reports` и `/reports/history` уже переведены на тот же `ConsumerPageShell`, что и `/`, `/week`, `/read/[id]`.
- catalog/storefront для non-horary все еще сознательно синхронизирован с default runtime как `299₽/мес`.
- `natal_master`, `month_forecast`, `year_forecast` и `solar_return` теперь имеют narrow one-off e2e path behind `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME` + `ENABLE_PERSISTENT_CHECKOUT_SESSIONS`: `/create` -> `/billing/complete` -> `/read/[id]`.
- `synastry` в этом документе остается частью broader rollout gap, а default catalog/storefront для non-horary по-прежнему intentionally subscription-first.

## 2. Что реально есть в продукте сейчас

### Пользовательские поверхности

| Surface | Route | Что делает сейчас | Источник данных |
| :--- | :--- | :--- | :--- |
| Home | `/` | Показывает daily feed, traffic lights, CTA в хорар, CTA в каталог | `GET /api/users/me`, `GET /api/feed/today` |
| Week | `/week` | Показывает последний `week_forecast` пользователя или CTA на создание | `GET /api/reports/my`, `GET /api/reports/{id}` |
| Read | `/read/[id]` | Читает long-form отчет блоками | `GET /api/reports/{id}` |
| Catalog | `/reports` | Показывает карточки продуктов в shared consumer shell и честный runtime paywall | storefront data + `frontend/lib/product-billing.ts` |
| Create | `/create?type=...` | Либо сразу запускает генерацию, либо ведет в оплату | `POST /api/reports/create`, `POST /api/billing/pay` |
| History | `/reports/history` | История отчетов, фильтры по типам и CTA обратно в create flow в shared consumer shell | `GET /api/reports/my` |

### Реально поддерживаемые report types / capability types

| Тип | Есть в backend | Есть в user create | Есть в catalog | Есть отдельная surface |
| :--- | :--- | :--- | :--- | :--- |
| `feed_daily` | частично, только как access flag | нет | нет | home `/` |
| `week_forecast` | да | да | нет | week `/week` |
| `month_forecast` | да | да | да | только `read` |
| `year_forecast` | да | да | да | только `read` |
| `ten_year_forecast` | да | да | нет | только `read` |
| `natal_master` | да | да | да | только `read` |
| `solar_return` | да | да | да | только `read` |
| `synastry` | да | да | да | только `read` |
| `horary` / `horary_answer` | да | да | да | `create` + `read` |

## 3. Каноническое решение по продуктовой лестнице

### Главный принцип

- `Day` и `Week` это retention-слой.
- `Month` и `Year` это planning-слой.
- `ten_year_forecast` это long-horizon extension поверх planning-слоя, а не отдельный retention/discovery anchor.
- `Natal` это базовая карта личности, от которой персонализируются прогнозы.
- `Solar` это yearly-personal overlay.
- `Synastry` это relational overlay.
- `Horary` это interrupt-product для конкретного вопроса, а не часть ladder.

### Каноническая матрица

| Продукт | Каноническая роль | Главная surface | Монетизация канон | Текущий код/UX |
| :--- | :--- | :--- | :--- | :--- |
| Day | быстрый daily entry | `/` | `free` | free, но не персонализирован |
| Week | главный подписочный retention-продукт | `/week` + `/read/[id]` | `subscription` | runtime/storefront уже выровнены на subscription |
| Month | тактический personal planning | `/reports` -> `/create` -> `/read/[id]` | `one_off` | narrow flagged one-off bridge уже real e2e на `/create` и `/billing/complete`, но catalog/storefront по умолчанию все еще subscription-first |
| Year | стратегический annual planning | `/reports` -> `/create` -> `/read/[id]` | `one_off premium` | narrow flagged one-off bridge уже real e2e на `/create` и `/billing/complete`, но catalog/storefront по умолчанию все еще subscription-first |
| Ten-Year | long-horizon planning extension | `/create` -> `/read/[id]` | `one_off premium` | read/create runtime есть, но catalog/pricing/access и rollout по-прежнему не выровнены |
| Natal | базовая карта личности и onboarding anchor | `/reports` -> `/create` -> `/read/[id]` | `one_off` | narrow one-off bridge уже real e2e behind flags на `/create` и `/billing/complete`, но catalog/storefront по умолчанию все еще subscription-first |
| Solar | год от ДР до ДР, персональный overlay | `/reports` -> `/create` -> `/read/[id]` | `one_off` | canonical one-off; explicit `solar_current_location` уже есть, flagged create/complete/read bridge уже real e2e, но default storefront все еще subscription-first |
| Synastry | relational deep-dive | `/reports` -> `/create` -> `/read/[id]` | `one_off` | canonical one-off; create-flow уже собирает partner data, но broader one-off bridge и softer untimed mode все еще не доведены |
| Horary | быстрый ответ на конкретный вопрос | `/create?type=horary` -> `/read/[id]` | `one_off / credits`, плюс `1 free/week` для sub | это уже ближе всего к реальной модели |

## 4. Распределение по surface

### Что должно жить на Home `/`

- Только `Day`.
- Короткая бесплатная сводка.
- CTA вверх по лестнице:
  - в `Week`, если есть подписка;
  - в `Catalog`, если пользователь хочет глубже;
  - в `Horary`, если нужен быстрый ответ по ситуации.

На home не должен жить full `Month` или full `Year`.

### Что должно жить на Week `/week`

- Только `Week` как продукт-повторитель.
- Один pinned активный недельный прогноз.
- Короткая читабельная форма.
- Кнопка drill-down в полный `read`.

Week page не должна быть каталогом всех прогнозов.

### Что должно жить в Read `/read/[id]`

- Все long-form персональные продукты:
  - `Week`
  - `Month`
  - `Year`
  - `Ten-Year`
  - `Natal`
  - `Solar`
  - `Synastry`
  - `Horary`

`Read` это не discovery-surface, а consumption-surface.

### Что должно жить в Catalog `/reports`

- Все one-off и premium продукты.
- Не free `Day`.
- Не основной `Week`, если он подписочный anchor.

Каталог должен продавать глубину, а не заменять home/week.

## 5. Продукты по одному

### 5.1 Day

**Назначение:** бесплатный ежедневный вход в продукт.  
**User value:** за 5-10 секунд понять тон дня и стоит ли идти глубже.

**Детерминированная база, которая есть сейчас:**

- transit chart на текущий момент;
- знак Луны;
- фаза Луны;
- до 5 локализованных аспектов из transit chart;
- fallback-текст при сбое LLM.

**Что сейчас не так:**

- feed считается для `Moscow`, а не для пользователя;
- feed не использует natal пользователя;
- `traffic_lights` задаются seed-рандомом от даты, а не астрологической моделью;
- `Day` не существует как report object и не сохраняется в history.

**Канонический surface:** home `/`.  
**Монетизация:** `free`.

**Рекомендуемый payload для frontend:**

```json
{
  "product": "day",
  "surface": "home",
  "personalization": "global_now",
  "date": "19.03.2026",
  "moon_sign": "Овен",
  "moon_phase": "Растущая Луна",
  "general_vibe": "Короткая сводка дня",
  "traffic_lights": {
    "health": "yellow",
    "money": "green",
    "love": "red"
  },
  "meta": {
    "source_location": "Moscow",
    "uses_natal": false
  }
}
```

**Рекомендуемые блоки:** `paragraph`, `traffic_lights`.

### 5.2 Week

**Назначение:** подписочный навигатор на ближайшие 7 дней.  
**User value:** понять ритм недели, опасные дни и лучшие окна действий.

**Детерминированная база, которая есть сейчас:**

- 7 transit chart по дням;
- знак и фаза Луны по каждому дню;
- heuristic `void_of_course`;
- ingress для `Sun`, `Mercury`, `Venus`, `Mars`;
- транзитные аспекты к натальным личным точкам;
- `tension_score` по каждому дню;
- weekly `summary.traffic_light`.

**Канонический surface:** `/week` как summary, `/read/[id]` как full read.  
**Монетизация:** `subscription`.

**Рекомендуемый payload/schema block pattern:**

```json
{
  "product": "week",
  "report_type": "week_forecast",
  "summary": {
    "traffic_light": "YELLOW",
    "avg_tension": 0.8
  },
  "days": [
    {
      "date": "2026-03-19",
      "weekday": "Thursday",
      "moon": {
        "sign": "Весы",
        "phase": "Растущая",
        "void_of_course": false
      },
      "ingresses": ["Меркурий -> Овен"],
      "aspects": [],
      "traffic_light": "GREEN",
      "tension_score": 0.0
    }
  ]
}
```

**Рекомендуемые block types в `read`:**

- `callout` для статуса недели
- `header` + `list` для каждого дня
- `traffic_lights` для финального резюме

### 5.3 Month

**Назначение:** тактический прогноз на 4-5 недель.  
**User value:** увидеть главные поворотные точки месяца и распределить усилия.

**Детерминированная база, которая есть сейчас:**

- скан 32 дней;
- `lunations`;
- `ingresses` для `Sun`, `Mercury`, `Venus`, `Mars`, `Jupiter`;
- `retrogrades` для `Mercury`, `Venus`, `Mars`, `Jupiter`, `Saturn`;
- major slow transits к личным точкам;
- `tension_index` и `status`.

**Канонический surface:** `catalog -> create -> read`.  
**Монетизация:** `one_off`.

**Рекомендуемый payload/schema block pattern:**

```json
{
  "product": "month",
  "report_type": "month_forecast",
  "status": "YELLOW",
  "tension_index": 2,
  "lunations": ["29.03 Новолуние в Овне"],
  "ingresses": ["20.03 Солнце -> Овен"],
  "major_transits": ["15.03 Сатурн квадрат Солнце"],
  "retrogrades": []
}
```

**Рекомендуемые block types в `read`:**

- `callout` для статуса месяца
- `list` для ключевых событий
- `paragraph` для стратегии
- `key_value` или `traffic_lights` для сфер

### 5.4 Year

**Назначение:** стратегический annual plan на 12 месяцев.  
**User value:** увидеть тему года, важные месяцы и стратегические окна.

**Детерминированная база, которая есть сейчас:**

- годовая profection: `house`, `lord`, `age`;
- active solar return summary: `datetime`, `asc_sign`, `sun_house`;
- solar arc hits с orb до `1.0`;
- 12 monthly snapshots по середине месяца;
- monthly `status`, `tension_index`, `aspects`.

**Канонический surface:** `catalog -> create -> read`.  
**Монетизация:** `one_off premium`.

**Рекомендуемый payload/schema block pattern:**

```json
{
  "product": "year",
  "report_type": "year_forecast",
  "target_year": 2026,
  "profection": {
    "house": 4,
    "lord": "Луна",
    "age": 33
  },
  "solar_return": {
    "datetime": "2025-10-30T19:50:00",
    "asc_sign": "Скорп",
    "sun_house": 1
  },
  "solar_arcs": [],
  "months": [
    {
      "month": 1,
      "status": "GREEN",
      "tension_index": 0,
      "aspects": []
    }
  ]
}
```

**Рекомендуемые block types в `read`:**

- `callout` для метафоры года
- `key_value` для `profection` + `solar_return`
- `header` + `list` для месяцев
- `divider` между кварталами или главами

### 5.5 Natal

**Назначение:** базовая карта личности и опорная персонализация для всей forecast ladder.  
**User value:** понять устойчивые паттерны, сильные стороны, риски, деньги, любовь и вектор роста.

**Детерминированная база, которая есть сейчас:**

- natal chart;
- дома и house context;
- natal aspects;
- patterns / geometries;
- fixed stars;
- Selena и Pars Fortuna;
- facts-first `section_context.insight_pack` для ключевых секций;
- баланс стихий/модальностей;
- deterministic packs для `executive_summary`, `synthesis`, `money_realization`, `love_intimacy`, `final_synthesis` и ряда других секций.

**Канонический surface:** `catalog -> create -> read`.  
**Монетизация:** `one_off`.

**Рекомендуемые block types:**

- `callout`
- `paragraph`
- `list`
- `key_value`
- `table` только в truly technical sections

### 5.6 Solar

**Назначение:** личный год от дня рождения до дня рождения.  
**User value:** yearly overlay поверх натала, более личный чем calendar year.

**Детерминированная база, которая есть сейчас:**

- natal chart;
- `solar_return` chart;
- секции `solar_theme`, `solar_money`, `solar_love`, `solar_strategy`.

**Канонический surface:** `catalog -> create -> read`.  
**Монетизация:** `one_off`.

**Рекомендуемый payload/schema block pattern:**

```json
{
  "product": "solar",
  "report_type": "solar_return",
  "base": "natal_plus_solar_return",
  "focus": ["theme", "money", "love", "strategy"]
}
```

**Рекомендуемые block types:**

- `callout` для темы года
- `list` / `paragraph` для money/love
- `callout` для strategy

### 5.7 Synastry

**Назначение:** relational overlay для пары.  
**User value:** понять совместимость не в общем, а по конкретным зонам отношений.

**Детерминированная база, которая есть сейчас:**

- две natal charts;
- synastry aspects;
- общий `score` 0-100;
- categories:
  - `sexual`
  - `emotional`
  - `intellectual`
  - `conflict`
  - `karmic`

**Канонический surface:** `catalog -> create -> read`.  
**Монетизация:** `one_off`.

**Рекомендуемый payload/schema block pattern:**

```json
{
  "product": "synastry",
  "report_type": "synastry",
  "score": 74,
  "categories": {
    "sexual": [],
    "emotional": [],
    "intellectual": [],
    "conflict": [],
    "karmic": []
  }
}
```

**Рекомендуемые block types:**

- `rating`
- `callout`
- `header` + `list`

### 5.8 Horary

**Назначение:** бинарный ответ на конкретный вопрос.  
**User value:** быстро принять решение, когда важен не общий жизненный контекст, а исход ситуации.

**Детерминированная база, которая есть сейчас:**

- карта на `now`;
- radicality score;
- significators `L1-L12` и `Moon`;
- dignities;
- applying/separating aspects;
- moon narrative;
- timing heuristics;
- verdict-oriented section structure.

**Канонический surface:** `create -> read`.  
**Монетизация:** `credits / one_off`, плюс `1 free/week` при подписке.

**Рекомендуемые block types:**

- `callout` для verdict
- `paragraph`
- `key_value`
- `table`
- `list`

## 6. Связь forecast ladder с Natal / Solar / Synastry / Horary

### Natal

- это фундамент персонализации;
- `Week`, `Month`, `Year` уже фактически считаются как `transits vs natal`;
- без `Natal` любой `Day` остается generic/global product.

### Solar

- это не замена `Year`, а отдельный годовой ракурс;
- `Year` отвечает на вопрос "что происходит в календарном году";
- `Solar` отвечает на вопрос "какой мой личный год между днями рождения";
- в текущем backend `year_forecast_data` уже использует solar return summary, значит связь продукта с Solar уже есть.

### Synastry

- это не следующая ступень ladder;
- это боковой relational mode;
- позже можно строить derivatives вроде `Relationship Week` или `Relationship Month`, но сейчас это отдельный read-product.

### Horary

- это не часть ladder;
- это interrupt product;
- он заменяет не `Week/Month/Year`, а моментальный вопрос "да/нет / когда / что мешает".

## 7. Frontend schema contract: что лучше держать единообразно

### Базовый принцип

Не изобретать новый renderer. Держать основной контракт через текущие block types из `docs/BLOCKS_SCHEMA.md` и `frontend/components/blocks/report-renderer.tsx`.

### Общий meta-слой, которого сейчас не хватает

Для всех `read`-продуктов полезен единый `report_meta`:

```json
{
  "product_family": "forecast|natal|relationship|horary",
  "horizon": "day|week|month|year|custom",
  "personalization_mode": "global|natal|synastry|horary",
  "window": {
    "start": "2026-03-19T00:00:00+03:00",
    "end": "2026-03-26T00:00:00+03:00",
    "timezone": "Europe/Moscow"
  },
  "deterministic_inputs": [
    "moon_phase",
    "ingresses",
    "transit_aspects",
    "profection",
    "solar_return"
  ]
}
```

### Рекомендуемый block repertoire по продуктовым семьям

| Семья | Основные блоки | Избегать |
| :--- | :--- | :--- |
| Day | `paragraph`, `traffic_lights` | длинные `list`, `table` |
| Week | `callout`, `header`, `list`, `traffic_lights` | тяжелые `table` |
| Month | `callout`, `list`, `paragraph`, `key_value` | избыточные `table` |
| Year | `callout`, `key_value`, `header`, `list`, `divider` | длинные монолитные paragraphs |
| Natal | `paragraph`, `callout`, `list`, `key_value` | table-first чтение |
| Solar | `callout`, `paragraph`, `list` | сложные таблицы |
| Synastry | `rating`, `callout`, `list` | техничный raw dump |
| Horary | `callout`, `key_value`, `table`, `list` | литературные intro-блоки |

## 8. Ключевые несоответствия current state

### P0 продуктовые

1. **One-off runtime больше не purely backend-only: `natal_master`, `month_forecast`, `year_forecast` и `solar_return` уже имеют narrow e2e bridge behind flags, но broader cutover все еще gated**
   - `frontend/app/create/page.tsx` для большинства non-horary по-прежнему отправляет `product_type: "subscription"`.
   - `/reports` и generic pricing helpers по-прежнему показывают default runtime как `299₽/мес`.
   - backend уже умеет persistent checkout sessions, `report_unlock` webhook grant, structured consume/link, `report_unlocks` snapshot и per-report `report_access`, а `natal_master`, `month_forecast`, `year_forecast` и `solar_return` уже используют этот path end-to-end; `synastry` и broader storefront cutover пока нет.

2. **Day feed не персонализирован**
   - `GET /api/feed/today` не использует пользователя.
   - Сводка строится по transit chart для `Moscow`.
   - Это глобальный daily, а не natal daily.

3. **Day traffic lights не астрологические**
   - `traffic_lights` сейчас строятся через seed-рандом от даты.
   - Это UI-метрика, а не детерминированный astro-score.

### P1 продуктовые

4. **Week существует как продукт и route, но отсутствует в catalog**
   - backend и `/week` route есть;
   - `/reports` не продает `week_forecast`.

5. **Month/Year/Natal/Solar уже выделились в narrow flagged bridge, но broader one-off ladder все еще не доведена**
   - `natal_master`, `month_forecast`, `year_forecast` и `solar_return` уже могут идти через `report_unlock` + `billing complete` + `access_source = report_entitlement`.
   - `synastry` пока не получил тот же frontend/catalog cutover.
   - storefront drift теперь уже частично осознанный и локализованный, а не общий для всех premium reports.

6. **`ten_year_forecast` read-capable, но не доведен до коммерческой матрицы**
   - backend sections, create meta и dedicated read coverage есть;
   - user-facing title mapping в `read/history` синхронизирован;
   - нет карточки в catalog;
   - нет price в `REPORT_PRICES`;
   - pay/access semantics остаются неявными.

7. **`year_forecast` брендирован как `Альманах 2026` в нескольких местах UI**
   - движок считает текущий target year;
   - копирайт жестко привязан к 2026.

### P2 capability mismatches

8. **`synastry` продается в user catalog, но broader commercial/runtime cutover все еще не доведен**
   - create-flow уже собирает `partner_birth_date`, `partner_birth_location` и optional `partner_name`;
   - flagged one-off bridge и softer product mode без точного времени рождения пока не реализованы.

9. **`solar_return` уже получил явный `solar_current_location`, но catalog/paywall semantics все еще split**
   - create-flow теперь честно спрашивает город активного личного года и сохраняет его через draft/resume path;
   - при bridge-flags off `/reports` и default `/create` все еще продают `solar_return` как часть subscription-first storefront.

10. **Есть orphan access flags `general_week` и `general_month`, но нет соответствующих user surfaces**
   - это намек на будущую бесплатную/облегченную ladder-ветку, но она не реализована в UX.

11. **Название хорара неоднородно**
   - встречаются `horary`, `horary_answer`;
   - landing/catalog/create/history используют разные имена.

12. **Legacy aliases еще существуют как compatibility layer, но primary admin path уже canonical**
   - backend normalizer все еще принимает `synastry_master` и `solar_return_master`;
   - основной admin UI и entitlement-first grant runtime уже используют `synastry` и `solar_return`.

## 9. Product decisions, которые стоит считать принятыми для следующего среза

1. `Day` остается free и lives on home.
2. `Week` закрепляется как subscription-retention product и живет на `/week`.
3. `Month` и `Year` считаются one-off planning products и живут через catalog/create/read.
4. `ten_year_forecast` закрепляется как long-horizon extension поверх ladder и читается через create/read, но не становится discovery-anchor до выравнивания catalog/billing.
5. `Natal` закрепляется как base-map product и источник персонализации для ladder.
6. `Solar` и `Synastry` остаются отдельными overlays, а не ступенями ladder.
7. `Horary` остается interrupt-product с credits + subscriber quota.
8. Весь long-form consumption остается на `read`, а не на `home/week/catalog`.
9. Любая будущая personalized `Day` версия должна строиться от `natal + current transits`, а не заменять `Week`.

## 10. Minimal GRACE scope следующей реализации

Если идти следующим срезом, минимально-достаточный scope такой:

1. Развести каноническую monetization-модель и реальный pay flow.
2. Привести catalog в соответствие product matrix.
3. Решить, остается ли `Day` global или делается personalized.
4. Довести `synastry` bridge/product precision до рабочего уровня; `solar` input уже выровнен, но catalog split еще остается.
5. Добавить единый `report_meta` для прогнозных read-продуктов.

### Operational note 2026-03-20

One-off entitlement phase 2 уже доведен до narrow `natal_master` / `month_forecast` / `year_forecast` / `solar_return` e2e slice behind flags, а `/api/users/me` уже отдает additive `report_access` alongside `report_unlocks`. Safe-default флаги по-прежнему `ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME=false` и `ENABLE_PERSISTENT_CHECKOUT_SESSIONS=false`, default storefront остается subscription-first, а детальный rollout gap теперь в основном про `synastry`, broader catalog flip и legacy bool adoption.
