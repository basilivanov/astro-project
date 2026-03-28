# Today Screen Blocks / DayBrief Mapping

## Scope

This note captures the exact content skeleton for the new home screen `Сегодня` and maps UI blocks to the current `DayBrief` DTO already returned by `GET /api/feed/today`.

Primary source paths:
- `frontend/app/page.tsx`
- `frontend/components/today/daybrief-sections.tsx`
- `frontend/lib/day-brief.ts`
- `backend/app/services/day_brief.py`
- `backend/app/main.py`

## What `/api/feed/today` already provides

Current frontend `DayBriefDto` contract already contains the fields needed for the new `Сегодня` home shell:

- `version`
- `date`
- `personalization_level`
- `fallback_mode`
- `summary`
- `context`
- `scores`
- `windows`
- `best_uses`
- `risks`
- `personalized_factors`
- `explainability`
- `premium`
- `cta`

Important: the acceptance list says `summary, scores, windows, best_uses, risks, explainability, CTA, premium`. In the current live DTO, `cta` is present in the payload and normalized by frontend, while `personalized_factors` is the supporting payload used inside the explainability block.

## How DTO fields arrive into `/api/feed/today`

Backend flow today:

1. `backend/app/main.py` serves `GET /api/feed/today`.
2. Feed building resolves personalized facts/context and then uses `backend/app/services/day_brief.py`.
3. `build_day_brief_payload(...)` calls `_assemble_day_brief_payload(...)`.
4. `_assemble_day_brief_payload(...)` assembles the final DTO fields:
   - `summary` via `_build_summary(...)`
   - `context` via `_build_context(...)`
   - `scores` via `_build_score_items(...)`
   - `windows` from scored lunar timing windows
   - `best_uses` and `risks` via `_build_best_and_risks(...)`
   - `personalized_factors` via `_prepare_personalized_factors(...)`
   - `explainability` via `_build_explainability(...)`
   - `premium` via `_build_premium_state(...)`
   - `cta` via `_build_cta(...)`
5. Frontend receives the payload in `frontend/app/page.tsx`, then normalizes it through `normalizeDayBriefPayload(...)` in `frontend/lib/day-brief.ts`.
6. The page renders block components in this order:
   - `TodayVerdict`
   - `TodayScores`
   - `TodayWindows`
   - `TodayActions`
   - `TodayRisks`
   - `TodayExplainability`
   - `TodayCtaPanel`

## Recommended block order

Recommended home screen order stays aligned with the current implementation:

1. Verdict
2. Score strip
3. Best windows
4. Actions / best uses
5. Risks
6. Explainability
7. CTA

Rationale:
- top of screen answers `what kind of day is this?`
- middle answers `when / for what / what to avoid?`
- lower section explains `why`
- footer section answers `what next?`

## Block-by-block mapping

### 1. Verdict

**Purpose**
- Hero verdict for the day.

**DTO fields**
- `summary.headline`
- `summary.subhead`
- `summary.day_type`
- `context.label`

**Display rule**
- Always render when a renderable `DayBrief` exists.
- `context.label` is optional.

**Current labels**
- Badge label is derived from `summary.day_type`.
- Current localized mapping in UI:
  - `push` → `Можно разгоняться`
  - `balance` → `Держите баланс`
  - `caution` → `Нужна осторожность`
  - `deep_focus` → `Глубокий фокус`
  - `recovery` → `Восстановление`

**Recommended block label / naming**
- Block name: `Вердикт дня`
- Keep `summary.headline` as main title.
- Keep `summary.subhead` as supporting sentence.
- Keep `context.label` as compact astro context pill/subline.

**Telemetry**
- No separate block-specific event now.
- Covered by page-level load/view event `today.brief_view`.

### 2. Score strip

**Purpose**
- Quick status across core domains.

**DTO fields**
- `scores[]` items:
  - `key`
  - `title`
  - `value`
  - `status`
  - `advice`

**Display rule**
- Render if `scores.length > 0`.
- In current DTO this is expected to always be non-empty.

**Current labels**
- Labels come directly from `scores[].title`.
- Current score keys are:
  - `energy`
  - `money`
  - `love`
  - `focus`

**Recommended label set**
- `energy` → `Энергия`
- `money` → `Деньги`
- `love` → `Отношения`
- `focus` → `Фокус`

**Notes**
- `status` is reusable for color semantics only: `green | yellow | red`.
- `advice` is useful for tap/expand tooltip or detail drawer if product wants richer score interactions.

**Telemetry**
- Existing event: `today.score_tap`
- Existing payload keys:
  - `score_key`
  - `score_value`
- Existing semantic block: `DAY_BRIEF_SCORES`

### 3. Best windows

**Purpose**
- Show when action quality is highest/softest/riskier.

**DTO fields**
- `windows[]` items:
  - `id`
  - `start`
  - `end`
  - `label`
  - `mode`
  - `advice`

**Display rule**
- Render if `windows.length > 0`.
- Current backend is designed to provide windows from lunar timing, so this should usually exist.

**Current labels**
- Block title in UI: `Окна дня`
- Window chip title uses `label`
- Time range uses `start`–`end`
- Mode is currently visual semantics only:
  - `best`
  - `soft`
  - `caution`

**Recommended naming**
- Block name: `Окна дня`
- Mode labels if text is needed:
  - `best` → `Лучшее окно`
  - `soft` → `Мягкое окно`
  - `caution` → `Осторожное окно`

**Telemetry**
- No dedicated event implemented now.
- Minimum recommendation: keep it passive for v1.

### 4. Actions / best uses

**Purpose**
- Show concrete high-value uses of the day.

**DTO fields**
- `best_uses[]` items:
  - `id`
  - `text`
  - `factor_id`
  - `impact`
  - `timeframe`

**Display rule**
- Render if `best_uses.length > 0`.

**Current labels**
- Current block title in UI: `Лучше использовать`

**Recommended naming**
- Preferred public title: `Что делать`
- Acceptable internal/dev title: `best_uses`
- Row metadata labels, if surfaced later:
  - `impact`: `high | medium | low`
  - `timeframe`: compact chip like `утро`, `день`, `вечер`, `весь день`

**Notes**
- `factor_id` already allows future linking from action item to explainability factor.

**Telemetry**
- No dedicated event implemented now.
- Recommendation for future if rows become clickable: `today.best_use_tap` with `item_id`, `factor_id`, `impact`, `timeframe`.

### 5. Risks

**Purpose**
- Show what can degrade the day if overused/mistimed.

**DTO fields**
- `risks[]` items:
  - `id`
  - `text`
  - `factor_id`
  - `impact`
  - `timeframe`

**Display rule**
- Render if `risks.length > 0`.

**Current labels**
- Current block title in UI: `Риски дня`

**Recommended naming**
- Preferred public title: `Где осторожно`
- Keep `Риски дня` as acceptable fallback label.

**Telemetry**
- No dedicated event implemented now.
- Recommendation for future if rows become clickable: `today.risk_tap` with `item_id`, `factor_id`, `impact`, `timeframe`.

### 6. Explainability

**Purpose**
- Explain why the verdict exists and how trustworthy it is.

**DTO fields**
- `explainability.confidence`
- `explainability.birth_time_used`
- `explainability.factor_count`
- `explainability.timing_precision`
- `explainability.top_signal_source`
- `explainability.explanation_depth`
- `personalized_factors[]`:
  - `id`
  - `label`
  - `impact`
  - `category`
  - `explanation_human`
  - `explanation_astro`
  - `source_models`
  - `weight`

**Display rule**
- Render if `explainability` exists.
- Personalized factor cards should render when `personalized_factors.length > 0`.
- Current implementation shows up to first 3 factors.

**Current labels**
- Block title: `Почему такой день`
- Confidence label: `Уверенность`
- Meta chips:
  - `Факторов: N`
  - `Точность: ...`
  - `Источник: ...`
- Time-source sentence:
  - `Точное время рождения учтено`
  - or `Без точного времени рождения — с мягкой поправкой на неопределённость`

**Recommended naming**
- Public block title: `Почему такой день`
- Internal block name: `Explainability`
- Recommended source labels mapping for user-friendly UI:
  - `transit_natal` → `Транзиты к наталу`
  - `transit_transit` → `Текущие транзиты`
  - `progressions` → `Прогрессии`
  - `directions` → `Дирекции`
  - `solar` → `Соляр`
  - `profections` → `Профекции`
  - `lunar` → `Лунный ритм`
  - `mixed` → `Смешанный сигнал`
- Recommended timing labels mapping:
  - `exact` → `Точная`
  - `approximate` → `Приближённая`

**Telemetry**
- No dedicated event implemented now.
- Recommendation if factor cards become interactive: `today.explainability_factor_tap` with `factor_id`, `category`, `impact`, `source_models`, `weight`.

### 7. CTA

**Purpose**
- Provide the next useful action after understanding the day.

**DTO fields**
- `cta.primary.type`
- `cta.primary.label`
- `cta.primary.href`
- `cta.secondary.type`
- `cta.secondary.label`
- `cta.secondary.href`
- `premium.subscription_active`
- `premium.subscription_active_until`
- `premium.days_left`
- `premium.show_upgrade_cta`
- `premium.show_resume_banner`

**Display rule**
- CTA panel should render whenever the page renders a `DayBrief`.
- If `cta` is absent, frontend already provides safe defaults:
  - primary: `Открыть неделю` → `/week`
  - secondary: referral/premium fallback
- Secondary CTA mode is influenced by premium state:
  - `premium.show_upgrade_cta = true` → renewal/upgrade framing
  - else if secondary type is premium/referral → referral framing
  - else generic secondary action framing

**Current labels**
- Block title: `Следующий шаг`
- Current helper copy is derived by premium mode:
  - upgrade helper copy
  - referral helper copy
  - generic helper copy

**Recommended CTA type labels**
- `open_week` → `Открыть неделю`
- `open_today` → `Открыть сегодня`
- `ask_question` → `Задать вопрос`
- `open_premium` → `Смотреть Premium`
- `open_history` → `История разборов`
- `open_report` → `Открыть разбор`
- `renew_premium` → `Продлить Premium`
- `refer_premium` → `Получить Premium по рекомендации`
- `custom` → label comes from backend as-is

**Premium notes**
- `premium` is already separate from `cta`, but it actively changes CTA framing.
- `show_resume_banner` is present in DTO and available for future resume-state messaging, even if not fully surfaced inside `TodayCtaPanel` now.

**Telemetry**
- Existing events:
  - `today.cta_click`
  - `today.cta_secondary_click`
  - `today.premium_renewal_click`
  - `today.premium_referral_click`
- Existing event payload keys:
  - `entry_point`
  - `cta_id`
  - `href`
  - `status=click`
- Existing semantic blocks:
  - `CTA_PRIMARY`
  - `CTA_SECONDARY`
  - `CTA_PREMIUM_RENEWAL`
  - `CTA_PREMIUM_REFERRAL`

## Premium block behavior

There is no standalone premium hero block inside the day brief section list right now; instead premium state is consumed in two places:

1. `TodayCtaPanel`
   - changes helper copy
   - changes tone/badge of secondary button
   - changes which telemetry event fires
2. `TrialStatusWidget` in `frontend/app/page.tsx`
   - rendered after CTA when `profile` exists
   - uses `today.premiumActiveUntil ?? profile.subscription_active_until`
   - can also use `profile.referral_code`

So for product framing, `premium` should be treated as a cross-cutting state, not as an independent content block in the core `Сегодня` stack.

## Exact reusable keys for the new home screen

If the new `Сегодня` screen needs a minimal reusable contract, these keys already exist and should be reused directly from `/api/feed/today`:

- `summary.headline`
- `summary.subhead`
- `summary.day_type`
- `context.label`
- `scores[].key`
- `scores[].title`
- `scores[].value`
- `scores[].status`
- `scores[].advice`
- `windows[].id`
- `windows[].start`
- `windows[].end`
- `windows[].label`
- `windows[].mode`
- `windows[].advice`
- `best_uses[].id`
- `best_uses[].text`
- `best_uses[].factor_id`
- `best_uses[].impact`
- `best_uses[].timeframe`
- `risks[].id`
- `risks[].text`
- `risks[].factor_id`
- `risks[].impact`
- `risks[].timeframe`
- `personalized_factors[].id`
- `personalized_factors[].label`
- `personalized_factors[].impact`
- `personalized_factors[].category`
- `personalized_factors[].explanation_human`
- `personalized_factors[].explanation_astro`
- `personalized_factors[].source_models`
- `personalized_factors[].weight`
- `explainability.confidence`
- `explainability.birth_time_used`
- `explainability.factor_count`
- `explainability.timing_precision`
- `explainability.top_signal_source`
- `explainability.explanation_depth`
- `premium.subscription_active`
- `premium.subscription_active_until`
- `premium.days_left`
- `premium.show_upgrade_cta`
- `premium.show_resume_banner`
- `cta.primary.type`
- `cta.primary.label`
- `cta.primary.href`
- `cta.secondary.type`
- `cta.secondary.label`
- `cta.secondary.href`

## Suggested label inventory

Recommended RU labels for design/content alignment:

- Screen title: `Сегодня`
- Verdict block: `Вердикт дня`
- Score block: `Пульс дня` or `Сферы дня`
- Windows block: `Окна дня`
- Actions block: `Что делать`
- Risks block: `Где осторожно`
- Explainability block: `Почему такой день`
- CTA block: `Следующий шаг`

Recommended stable chip/field labels:

- `Уверенность`
- `Факторов`
- `Точность`
- `Источник`
- `Лучшее окно`
- `Мягкое окно`
- `Осторожное окно`

## Product conclusion

No backend contract extension is required for the requested home-screen skeleton. The current `DayBrief` payload from `/api/feed/today` already covers:

- verdict
- windows
- actions
- risks
- explainability
- CTA
- premium-driven CTA framing

The only work needed for a new home shell is naming/layout alignment and, if desired, extra telemetry for non-clickable informational rows/cards that later become interactive.
