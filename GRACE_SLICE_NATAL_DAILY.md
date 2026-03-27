# GRACE Slice: natal + forecast + daily frontend

## Intent / Назначение
Этот sync-pass фиксирует только текущий user-facing slice: `natal_master`, shared forecast create/read, personalized daily feed v2 и безопасное чтение chunk-based отчетов. Это не whole-project remap.

## Scope / Границы

### In Scope
- `natal_master`: create -> async generation -> `/read/[id]`.
- `section_context.insight_pack` для всех текущих natal-секций.
- Runtime wiring `STYLE_CONTRACT.md` в premium natal prompts.
- Shared forecast context для `week/month/year/ten_year_forecast`.
- Forecast read surfaces: `/week` и generic `/read/[id]`.
- Daily feed на `/` с состояниями `ready/fallback/empty/error` и facts-first personalization v2.
- Safe block parsing и fallback card в `frontend/components/blocks/report-renderer.tsx`.

### Out Of Scope
- Billing, referrals, admin, bot delivery.
- Horary/synastry/solar как отдельные доменные срезы.
- Полная редакторская карта для каждого forecast-продукта.
- Полная переделка root GRACE-артефактов вне touched slice.

## Modules / Модули

### M-NATAL-CONTEXT-ENGINE
- Файлы: `backend/app/services/report_workflow.py`.
- Экспорты: `build_section_context`, `build_report_context`, `build_forecast_window`.
- Реальное состояние:
  - natal prompts получают trimmed `section_context`;
  - для всех текущих natal section ids кладется deterministic `section_context.insight_pack` c версиями `natal_v2_p0..p4` и `cross_links`;
  - forecast context инжектит `week_forecast_data`, `month_forecast_data`, `year_forecast_data`, `decade_forecast_data`.
- Инварианты:
  - `input_frame` и `technical_appendix` не режутся;
  - `final_synthesis` исполняется после остальных секций;
  - `birth_time_known=false` вырезает house-based natal sections.

### M-NATAL-PROMPT-CONTRACT
- Файлы: `backend/app/reporting/section_templates.py`, `backend/app/llm/orchestrator.py`, `STYLE_CONTRACT.md`, `NATAL_V2_FACTS_MAP.md`.
- Реальное состояние:
  - natal templates явно завязаны на `section_context.insight_pack`;
  - orchestrator читает `STYLE_CONTRACT.md`, кэширует краткий hint и добавляет его в runtime prompt;
  - runtime style hint сейчас применяется только к `executive_summary`, `synthesis`, `love_intimacy`;
  - `executive_summary` получает отдельный runtime addendum про sharp life-first logline.
- Инварианты:
  - JSON block contract остается строгим;
  - модель verbalize-ит deterministic conclusions, а не заменяет их своим каркасом.

### M-NATAL-SUMMARY-LAYER
- Файлы: `backend/app/services/report_workflow.py`, `backend/app/llm/orchestrator.py`.
- Экспорты: `build_section_validation_fallback_content`, `generate_section_content`.
- Реальное состояние:
  - `executive_summary` и `final_synthesis` имеют отдельный deterministic insight-pack path и compact validation fallback;
  - fallback для summary-layer больше не обязан показывать user-facing блок `Дополнено автоматически` в unit/deterministic path;
  - validator теперь принимает живой `balance_wheel` формат с заголовками вида `Дом 8`, `Дом 9`, а не только жесткий шаблон `8 Дом`;
  - representative live rerun все еще показывает, что summary-layer полностью не стабилизирован: `executive_summary` иногда течет в repair-leak, `final_synthesis` местами слишком статичен.
- Инварианты:
  - `executive_summary` должен покрывать жизненную сцену, ресурс, риск, отношения, деньги и фокус роста;
  - `final_synthesis` должен оставаться коротким chart-specific closing, а не generic motto block;
  - balance-wheel validator обязан пропускать house-structured live output и резать общую простыню без явных домов.

### M-FORECAST-DATA-ENGINE
- Файлы: `backend/app/services/report_workflow.py`, `stellium_engine.py`, `backend/app/reporting/section_templates.py`.
- Реальное состояние:
  - `build_forecast_window()` формирует окно в target TZ;
  - engine считает week/month/year/decade datasets;
  - section templates потребляют `week_forecast_data`, `month_forecast_data`, `year_forecast_data`, `decade_forecast_data`.
- Инварианты:
  - forecast идет через тот же async report workflow, что и natal;
  - `week_forecast` имеет отдельный `week_strategy` contract и отдельную `/week` surface.

### M-FORECAST-SEMANTIC-LAYER
- Файлы: `backend/app/services/forecast_semantics.py`, `backend/app/services/report_workflow.py`, `backend/app/services/personalized_daily.py`.
- Экспорты: `build_daily_forecast_semantic_layer`, `build_week_forecast_semantic_layer`, `build_month_forecast_semantic_layer`.
- Реальное состояние:
  - daily/week/month используют узкий deterministic `semantic_layer`, собранный поверх уже рассчитанных фактов, а не поверх новых LLM-теорий;
  - month prompt context дополняется `campaign_arc`, `event_cards`, `phases`, `status_summary`, `central_task`;
  - month fallback рендерится как weekly campaign structure, а не как generic motivational paragraph;
  - personalized daily feed прокидывает `semantic_layer.headline` и `semantic_layer.practical_move` в facts-first prompt/fallback path.
- Инварианты:
  - `semantic_layer` должен усиливать human-readable pacing, но не подменять исходные forecast facts;
  - month output должен звучать как кампания `сначала -> затем -> к середине -> в финале`;
  - generic month blur без событий, tension и practical move считается невалидным.

### M-API-ENTRY-READ
- Файлы: `backend/app/main.py`.
- Экспорты: `create_b2c_report`, `run_report_generation`, `get_report_detail`, `user_regenerate_report`, `get_daily_feed`.
- Реальное состояние:
  - create возвращает `report_id` сразу и запускает background generation;
  - `get_report_detail` отдает отсортированные `chunks` и `chart_svg`;
  - `input_frame` скрыт из user detail response;
  - daily endpoint на любой ошибке возвращает safe payload, а не 500.
- Инварианты:
  - read доступен только владельцу;
  - chunk status является каноническим lifecycle;
  - `traffic_lights` в feed payload всегда присутствуют.

### M-READ-RESILIENCE-SURFACE
- Файлы: `frontend/app/create/page.tsx`, `frontend/app/read/[id]/page.tsx`, `frontend/app/week/page.tsx`, `frontend/components/blocks/report-renderer.tsx`.
- Реальное состояние:
  - `week_forecast` create flow редиректит на `/week`;
  - остальные продукты читаются через `/read/[id]`;
  - `/read/[id]` использует `parseReportBlocks()` и `extractReportFallbackText()` для safe rendering;
  - первые 3 секции auto-expand;
  - malformed или non-JSON chunk content остается читаемым через fallback card;
  - completed-but-empty payloadы показывают empty state вместо падения.
- Инварианты:
  - unsupported block types тихо игнорируются;
  - renderer принимает только поддерживаемые block families;
  - `chart_svg` optional, но безопасен.

### M-DAILY-FEED-SURFACE
- Файлы: `frontend/app/page.tsx`, `backend/app/main.py`, `backend/app/services/feed_service.py`, `backend/app/services/personalized_daily.py`.
- Реальное состояние:
  - homepage грузит `/api/users/me` и `/api/feed/today` параллельно и передает `X-Telegram-Auth` в оба запроса;
  - frontend имеет явные состояния `ready`, `fallback`, `empty`, `error`;
  - backend собирает facts-first daily context: local timezone/location, Moon/day context, fast transit-to-natal hits, week/month/year horizon when profile is complete;
  - `feed_service` учитывает `cache_scope` и factual prompt lines, а fallback text может использовать personalized emphasis.
- Инварианты:
  - без Telegram context показывается landing;
  - invalid/missing auth header не ломает endpoint и откатывается в anonymous/general path;
  - feed failure не должен ломать страницу при валидном профиле.

## Use Cases / Кейсы

### UC-NATAL-FACTS-FIRST
- `SCN-NATAL-INSIGHT-PACK`: каждая natal section получает trimmed facts и deterministic `insight_pack`; `balance_wheel` validator принимает live house-level phrasing, если структура по домам сохранена.
- `SCN-NATAL-STYLE-CONTRACT`: premium natal prompts получают runtime `STYLE_CONTRACT.md` hint и остаются life-first.
- `SCN-NATAL-SUMMARY-REPAIRLESS`: summary-layer fallback должен оставаться compact и chart-anchored без user-visible repair-warning blocks в deterministic path.
- `SCN-FINAL-SYNTHESIS-CHART-SPECIFIC`: `final_synthesis` обязан собираться из chart-specific insight pack, а не из почти одинакового closing template.

### UC-FORECAST-CREATE-READ
- `SCN-FORECAST-CONTEXT-DATA`: forecast payload инжектит `forecast_window` и typed `*_forecast_data`.
- `SCN-FORECAST-SEMANTIC-LAYER`: week/month/daily получают `semantic_layer`, а month дополнительно получает `campaign_arc` для human-readable pacing.
- `SCN-WEEK-CREATE-READ`: `create?type=week_forecast` -> `POST /api/reports/create` -> `/week` -> latest week report read.
- `SCN-MONTH-FORECAST-REALDATA`: month forecast read path рендерит status/event markers из реального `month_forecast_data`.
- `SCN-GENERIC-FORECAST-READ`: non-week forecasts читаются через `/read/[id]` на том же chunk contract, что и natal.

### UC-REPORT-READ-QUALITY
- `SCN-READ-FALLBACK-CARD`: raw text или malformed JSON остаются видимыми через safe fallback card.
- `SCN-READ-EMPTY-SAFE`: completed report без usable blocks показывает explicit empty state.
- `SCN-CHART-SVG-OPTIONAL`: отчет остается читаемым даже если SVG не собрался.

### UC-FEED-DAILY
- `SCN-FEED-TODAY`: homepage показывает daily card + traffic lights при валидном feed.
- `SCN-FEED-PERSONALIZED-V2`: при полном профиле daily feed использует timezone/location пользователя, быстрые транзиты к наталу и horizon context из week/month/year.
- `SCN-FEED-FALLBACK-SAFE`: backend/network failure деградирует в fallback/empty/error state без page crash.

## Data Flow / Потоки

### Natal
`/create?type=natal_master` -> `POST /api/reports/create` -> `run_report_generation` -> `build_chart_data` -> `build_report_context` -> `build_section_context` + `insight_pack` -> `build_section_prompt` + runtime style hint -> `ReportChunk.content` -> `GET /api/reports/{id}` -> `parseReportBlocks` / fallback card -> accordion read UI.

### Forecast
`/create?type=week|month|year|ten_year_forecast` -> shared async workflow -> `build_forecast_window` + `*_forecast_data` injection -> forecast section templates -> `/week` for week or `/read/[id]` for generic forecast read.

### Daily
`/` -> `/api/users/me` + `/api/feed/today` + `X-Telegram-Auth` -> optional `authenticate_telegram_user` -> `build_personalized_daily_facts` -> `get_daily_vibe_llm` -> `ready|fallback|empty|error`; feed fallback не должен блокировать страницу.

**Actual current daily facts behavior**
- `build_personalized_daily_facts` кеширует deterministic facts по ключу `(local_date, timezone, location_label, profile_fingerprint)`; fingerprint включает natal/current geo + timezone + `sun_sign`.
- timezone резолвится как `current_timezone -> birth_timezone -> UTC`; invalid timezone деградирует в `UTC`, а локальная дата для кеша считается уже в resolved timezone.
- transit location приоритетит current lat/lon, затем birth lat/lon, затем строковые `current_location`/`birth_place`, и только потом fallback `Moscow`.
- `full` personalization включается только при наличии `birth_date` и `birth_place`; иначе сервис остается в generic/day-transit режиме без natal fast hits.
- fast hits ограничены быстрыми транзитами `Sun/Mercury/Venus/Mars` к личным натальным точкам `Sun/Moon/Mercury/Venus/Mars/ASC/MC`, сортируются по orb и режутся до top-5.
- fallback daily aspects берутся только из transit-to-transit набора по `Sun..Saturn`, тоже сортируются по orb и режутся до top-5.
- fact lines сейчас канонически собирают: local context, moon sign + phase, optional sun-sign profile, fast hits или общий фон дня, weekly context, month status/events, personalized traffic lights и short yearly month summary.
- `cache_scope` — это sha256 по публичным deterministic facts (`date`, personalization level, timezone, location, aspect summary, traffic lights, fact lines) и он не равен raw cache key.
- public meta публикует только безопасный срез (`date`, `timezone`, `location_label`, `personalization_level`, counts/flags и short summaries) без сырых natal coordinates.
- failure policy: отсутствие Sun/Moon ephemeris остается hard failure (`ValueError`), а week/month/year forecast layers деградируют по месту с warning logs вместо полного падения daily feed.
- traffic lights считаются в двух режимах: generic score от weekday traffic/day aspects/moon phase, либо personalized score от weekday base + natal hit effects + month status adjustments; результат clamp в `0..100` и map в `green/yellow/red`.

## Verification Mapping / Верификация

### VM-NATAL-CONTEXT
- Команды:
  - `PYTHONPATH=. python3 -m pytest tests/test_natal_section_context.py`
  - `PYTHONPATH=. python3 -m pytest tests/test_report_contract.py`
  - `PYTHONPATH=. python3 -m pytest tests/test_report_context.py`
- Доказывает:
  - `insight_pack` versions/fields across natal sections;
  - prompt contracts опираются на `section_context.insight_pack`;
  - forecast context и dataset keys остаются каноническими;
  - `/api/reports/{id}` остается chunk-first.

### VM-NATAL-STYLE-CONTRACT
- Команды:
  - `PYTHONPATH=. python3 -m pytest tests/test_natal_section_context.py -k prompt_contract`
  - `python3 scripts/grace_lint.py`
- Доказывает:
  - runtime style hint из `STYLE_CONTRACT.md` реально присутствует в premium natal prompts;
  - базовые prompt-правила не выпали.

### VM-NATAL-SUMMARY-REPAIR
- Команды:
  - `PYTHONPATH=. python3 -m pytest tests/test_validation_relaxed.py`
  - `PYTHONPATH=. python3 -m pytest tests/test_validation_template_fallback.py`
  - `PYTHONPATH=. python3 -m pytest tests/test_natal_section_context.py`
- Доказывает:
  - summary fallback не обязан показывать `Дополнено автоматически` в deterministic/unit path;
  - `executive_summary` и `final_synthesis` могут собираться из insight pack без LLM вызова;
  - `balance_wheel` validator принимает live `Дом N` структуру и режет generic wall-of-text;
  - `final_synthesis` validator требует compact success-callout и chart-specific insight pack.

### VM-FORECAST-CREATE-READ
- Команды:
  - `./scripts/run_e2e.sh e2e/report-create.spec.ts -g "week forecast"`
  - `./scripts/run_e2e.sh e2e/forecast-realdata.spec.ts`
  - `./scripts/run_e2e.sh e2e/year-forecast-read.spec.ts`
  - `./scripts/run_e2e.sh e2e/ten-year-forecast-read.spec.ts`
- Доказывает:
  - week create flow редиректит корректно;
  - week/month surfaces показывают forecast markers из реальных generated data;
  - `year_forecast` и `ten_year_forecast` generic read paths остаются безопасными на chunk contract.

### VM-FORECAST-SEMANTICS
- Команды:
  - `PYTHONPATH=. python3 -m pytest tests/test_forecast_semantics.py`
  - `PYTHONPATH=. python3 -m pytest tests/test_month_forecast_validation.py`
  - `PYTHONPATH=. python3 -m pytest tests/test_report_context.py`
- Доказывает:
  - `semantic_layer` для daily/week/month реально строится и содержит human-readable anchors;
  - month prompt/fallback path сохраняет `campaign_arc`, weekly phases и practical move;
  - generic month paragraph без campaign semantics и factual anchors не проходит validator.

### VM-READ-QUALITY
- Команды:
  - `./scripts/run_e2e.sh e2e/quality.spec.ts`
- Доказывает:
  - invalid blocks игнорируются;
  - malformed sections остаются видимыми через fallback card;
  - empty completed report и chart SVG paths обработаны безопасно.

### VM-FEED-ROBUSTNESS
- Команды:
  - `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_daily_feed_robustness.py tests/test_personalized_daily_service.py`
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
  - `./scripts/run_e2e.sh e2e/core-ux.spec.ts`
- Доказывает:
  - API fallback payload shape стабилен;
  - personalized facts layer собирает fast hits, deterministic cache/meta и horizon context без поломки fallback path;
  - personalized/generic traffic-light scoring и cache-scope contract остаются детерминированными;
  - homepage выдерживает normal/fallback/empty/error daily states.

## Current Gaps / Текущие пробелы
- representative live natal slice все еще упирается в summary-layer:
  - `executive_summary` на части live cases продолжает протекать repair-leak;
  - `final_synthesis` в rerun остается слишком статичным между разными картами.
- non-horary premium reports по умолчанию все еще живут через runtime subscription alignment `299₽/мес`, но flagged one-off bridge уже реально существует для `natal_master`, `month_forecast`, `year_forecast` и `solar_return`; канонический next slice зафиксирован в `GRACE_SLICE_ONE_OFF_ENTITLEMENTS.md`.
- `ten_year_forecast` все еще не выведен в отдельную коммерческую surface: create/read есть, но catalog/pricing/access остаются несинхронизированными.
- Live style quality пока верифицируется на уровне contract/prompt, а не через deterministic editorial-output approval.
- `frontend/e2e/core-ux.spec.ts` сейчас имеет drift в mock fallback/empty/error ветках: live mock-auth path green, но отдельные mock-state assertions не срабатывают и требуют отдельного frontend follow-up.
