# Quality Telemetry Runbook

Подробный runbook по quality telemetry для Wave 5. Документ фиксирует канонические backend-события качества, их payload, источники в коде, правила включения `trace_id` / `model` / `prompt_version` / `benchmark_linkage`, и быстрые команды для проверки через pytest / pipeline / grep.

## Scope

Этот runbook покрывает централизованные backend quality events:

- `quality.schema_failure`
- `quality.invalid_json`
- `quality.fallback_activated`
- `quality.prompt_repair`
- `quality.repair_success`
- `quality.benchmark_linked`

Канонический emitter: `backend/app/logging_utils.py` через `emit_quality_event(...)`.

Канонические JSONL sinks:

- `logs/feed.jsonl` — quality events попадают сюда через `FEED_EVENTS`
- stdout / structlog renderer — для локального запуска и `docker logs`

## Canonical source map

### Emitter and payload builder

- `backend/app/logging_utils.py:249` — `build_grace_log_payload(...)` добавляет `module`, `fn`, `block` и correlation envelope.
- `backend/app/logging_utils.py:266` — `log_grace_event(...)` пишет структурированный GRACE event через `structlog`.
- `backend/app/logging_utils.py:315` — `emit_quality_event(...)` разрешает только шесть quality events и стандартизует payload.
- `backend/app/logging_utils.py:21` — `FEED_EVENTS` включает все `quality.*` события, поэтому они дублируются в `logs/feed.jsonl`.

### DayBrief sources

- `backend/app/services/day_brief.py:1043` — `build_day_brief_telemetry(...)` собирает telemetry envelope (`trace_id`, confidence, prompt metadata).
- `backend/app/services/day_brief.py:1070` — `_log_day_brief_event(...)` пишет обычный day event и при необходимости зеркалит его в `quality.*`.
- `backend/app/services/day_brief.py:1111` — `day_brief.validation_failed` → `quality.schema_failure`.
- `backend/app/services/day_brief.py:1114` — `day_brief.fallback` → `quality.fallback_activated`.
- `backend/app/services/day_brief.py:1117` — `day_brief.built` + `benchmark_run_id` → `quality.benchmark_linked`.

### WeekBrief sources

- `backend/app/services/week_brief_service.py:175` — `_log_week_brief(...)` пишет week event и при необходимости зеркалит его в `quality.*`.
- `backend/app/services/week_brief_service.py:194` — `week_brief_validation_failed` → `quality.schema_failure`.
- `backend/app/services/week_brief_service.py:197` — `week_brief_fallback_triggered` → `quality.fallback_activated`.
- `backend/app/services/week_brief_service.py:199` — `week_brief_built` + `benchmark_run_id` → `quality.benchmark_linked`.
- `backend/app/services/week_brief_service.py:201` — `week_brief_invalid_json` → `quality.invalid_json`.
- `backend/app/services/week_brief_service.py:204` — `week_brief_prompt_repair` → `quality.prompt_repair`.
- `backend/app/services/week_brief_service.py:206` — `week_brief_repair_success` → `quality.repair_success`.

### Correlation and request propagation

- `backend/app/middleware/correlation.py:72` — `CorrelationIdMiddleware` создаёт новый `trace_id` на каждый HTTP request, принимает `X-Correlation-Id`, возвращает `X-Correlation-Id` и `X-Trace-Id` в response headers.
- `backend/app/logging_utils.py:176` — `bind_correlation_ids(...)` создаёт `correlation_id` + `trace_id` для non-HTTP scopes.
- `frontend/lib/correlation.ts:180` — frontend прокидывает `X-Correlation-Id`.
- `frontend/lib/correlation.ts:181` — frontend прокидывает `X-Trace-Id`.

## Event catalog

Ниже перечислены все quality events, их trigger conditions, обязательные payload fields и поля, которые появляются только в некоторых flows.

### 1. `quality.schema_failure`

**Когда пишется**

- `DayBrief`: при `day_brief.validation_failed`.
- `WeekBrief`: при `week_brief_validation_failed`.

**Источники**

- `backend/app/services/day_brief.py:1111`
- `backend/app/services/week_brief_service.py:194`

**Обязательный базовый payload**

- `event`
- `timestamp`
- `module`
- `fn`
- `block`
- `trace_id`
- `model`
- `prompt_version`
- `fallback_mode`
- `confidence_bucket`

**Часто встречающиеся дополнительные поля**

- `correlation_id`
- `correlation_source`
- `reason`
- `error`
- `generation_mode` — для DayBrief
- `report_id`, `report_type`, `report_status` — для WeekBrief

**Семантика**

Используется для schema mismatch / validation failure после сборки или нормализации payload. Это основной маркер того, что LLM output или сборка DTO не прошли canonical validation.

### 2. `quality.invalid_json`

**Когда пишется**

- Только `WeekBrief`: когда chunk parsing дал invalid JSON и сервис перешёл в degraded/repair path.

**Источники**

- `backend/app/services/week_brief_service.py:201`

**Обязательный базовый payload**

- `event`
- `timestamp`
- `module`
- `fn`
- `block`
- `trace_id`
- `model`
- `prompt_version`
- `fallback_mode`
- `confidence_bucket`

**Часто встречающиеся дополнительные поля**

- `correlation_id`
- `correlation_source`
- `report_id`, `report_type`, `report_status`
- `reason`
- `error`
- `primary_reason_code`
- `reason_codes`
- `chunk_parse_degraded`
- `missing_required_sections`
- `stub_mode`

**Семантика**

Сигнализирует, что LLM/section chunk вернул невалидный JSON и quality loop пошёл по repair/fallback пути.

### 3. `quality.fallback_activated`

**Когда пишется**

- `DayBrief`: при `day_brief.fallback`.
- `WeekBrief`: при `week_brief_fallback_triggered`.

**Источники**

- `backend/app/services/day_brief.py:1114`
- `backend/app/services/week_brief_service.py:197`

**Обязательный базовый payload**

- `event`
- `timestamp`
- `module`
- `fn`
- `block`
- `trace_id`
- `model`
- `prompt_version`
- `fallback_mode`
- `confidence_bucket`

**Часто встречающиеся дополнительные поля**

- `correlation_id`
- `correlation_source`
- `reason`
- `error`
- `generation_mode` — для DayBrief
- `report_id`, `report_type`, `report_status` — для WeekBrief

**Семантика**

Главный runtime-индикатор, что система перешла на deterministic/render-safe fallback и не отдала чистый primary output.

### 4. `quality.prompt_repair`

**Когда пишется**

- Только `WeekBrief`: когда после invalid/degraded parse запускается prompt repair step.

**Источники**

- `backend/app/services/week_brief_service.py:204`

**Обязательный базовый payload**

- `event`
- `timestamp`
- `module`
- `fn`
- `block`
- `trace_id`
- `model`
- `prompt_version`
- `fallback_mode`
- `confidence_bucket`

**Часто встречающиеся дополнительные поля**

- `correlation_id`
- `correlation_source`
- `report_id`, `report_type`, `report_status`
- `reason`
- `error`
- `primary_reason_code`
- `reason_codes`
- `chunk_parse_degraded`
- `missing_required_sections`
- `stub_mode`
- `repair_outcome`

**Семантика**

Фиксирует вход в repair loop. Если событие есть, downstream reviewer должен проверить, был ли затем `quality.repair_success` или система ушла в fallback.

### 5. `quality.repair_success`

**Когда пишется**

- Только `WeekBrief`: когда repair path успешно восстановил пригодный payload.

**Источники**

- `backend/app/services/week_brief_service.py:206`

**Обязательный базовый payload**

- `event`
- `timestamp`
- `module`
- `fn`
- `block`
- `trace_id`
- `model`
- `prompt_version`
- `fallback_mode`
- `confidence_bucket`

**Часто встречающиеся дополнительные поля**

- `correlation_id`
- `correlation_source`
- `report_id`, `report_type`, `report_status`
- `repair_outcome`
- `chunk_parse_degraded`

**Семантика**

Показывает, что repair loop не только стартовал, но и завершился успешно. Это важный сигнал для quality loops, где invalid JSON не должен автоматически означать hard failure.

### 6. `quality.benchmark_linked`

**Когда пишется**

- `DayBrief` или `WeekBrief` при successful build event, если в telemetry прокинут `benchmark_run_id`.

**Источники**

- `backend/app/services/day_brief.py:1117`
- `backend/app/services/week_brief_service.py:199`

**Обязательный базовый payload**

- `event`
- `timestamp`
- `module`
- `fn`
- `block`
- `trace_id`
- `model`
- `prompt_version`
- `fallback_mode`
- `confidence_bucket`
- `benchmark_run_id`

**Ожидаемые дополнительные поля**

- `benchmark_link`
- `correlation_id`
- `correlation_source`
- `generation_mode` — для DayBrief
- `report_id`, `report_type`, `report_status` — для WeekBrief

**Семантика**

Связывает runtime event с benchmark evidence. Это bridge между live structured logs и benchmark/controller packet artifacts.

## Payload contract

### Canonical envelope from `emit_quality_event(...)`

Функция `backend/app/logging_utils.py:315` формирует следующую каноническую форму:

- `event` — имя события
- `timestamp` — добавляется `structlog.processors.TimeStamper`
- `module` — GRACE module id
- `fn` — функция-источник
- `block` — semantic block / GRACE block
- `correlation_id` — если есть request/non-request correlation context
- `trace_id` — обязательный operational trace identifier для quality analysis
- `correlation_source` — `header`, `request_id`, `generated`, либо custom source
- `model` — resolved model, переданный caller'ом
- `prompt_version` — prompt contract version
- `fallback_mode` — флаг degraded/fallback execution
- `confidence_bucket` — coarse confidence bucket
- `benchmark_run_id` — benchmark run identity, если есть
- `benchmark_link` — ссылка/URI/relative artifact path до benchmark evidence, если есть
- `...fields` — caller-specific extras (`reason`, `error`, `report_id`, `generation_mode`, `repair_outcome` и т.д.)

### DayBrief-specific extras

`backend/app/services/day_brief.py:1082` добавляет в обычный event и частично в quality event:

- `generation_mode`
- `birth_time_used`
- `confidence`
- `factor_count`
- `prompt_model`
- `prompt_seed`
- `personalization_level`
- `reason`
- `error`
- `benchmark_run_id`
- `benchmark_link`

Важно: в quality event поле `model` берётся из `telemetry["prompt_model"]`, а не из `prompt_model` key. То есть canonical quality key называется именно `model`.

### WeekBrief-specific extras

`backend/app/services/week_brief_service.py:208` прокидывает в quality event:

- `report_id`
- `report_type`
- `report_status`
- `reason`
- `error`
- `chunk_parse_degraded`
- `repair_outcome`

А upstream helper `backend/app/services/week_brief_service.py:229` формирует поля:

- `week_brief_llm_model`
- `week_brief_fallback_mode`
- `week_brief_confidence_bucket`
- `prompt_version`
- `prompt_seed`
- `benchmark_run_id`
- `benchmark_link`

На этапе эмита они нормализуются в canonical quality keys `model`, `fallback_mode`, `confidence_bucket`.

## How to enable `trace_id`, `model`, `prompt_version`, `benchmark_linkage`

### `trace_id`

HTTP path:

1. `CorrelationIdMiddleware` в `backend/app/middleware/correlation.py:72` автоматически создаёт новый `trace_id = uuid4()` на каждый request.
2. Middleware кладёт его в contextvars через `set_correlation_ids(...)`.
3. `emit_quality_event(...)` подмешивает его в payload либо из explicit arg `trace_id=...`, либо из активного correlation context.

Что нужно сделать разработчику:

- Убедиться, что код исполняется внутри FastAPI request lifecycle, либо
- Для background / CLI / benchmark path обернуть код в `correlation_scope(...)` или вызвать `bind_correlation_ids("source")`.

Минимальный пример:

```python
from backend.app.logging_utils import bind_correlation_ids, emit_quality_event

bind_correlation_ids("benchmark")
emit_quality_event(
    "quality.benchmark_linked",
    module="M-EXAMPLE",
    fn="run_case",
    block="ASSEMBLY",
    model="openai/gpt-4.1-nano",
    prompt_version="week_brief_prompt_v2",
    benchmark_run_id="bench-2026-03-27-001",
)
```

### `model`

`emit_quality_event(...)` не вычисляет model сам. Caller обязан передать resolved model.

Текущий canonical pattern:

- `DayBrief`: `backend/app/services/day_brief.py:1126` передаёт `model=telemetry["prompt_model"]`.
- `WeekBrief`: `backend/app/services/week_brief_service.py:218` передаёт `model=payload.get("week_brief_llm_model")`.
- Report generation paths используют `resolve_primary_model(...)` и `resolve_llm_fallback_model(...)` из `backend/app/services/report_workflow.py:3162` и `backend/app/services/report_workflow.py:3133`.

Правило:

- Для любого нового quality event сначала получить effective runtime model, затем передать её в `emit_quality_event(model=...)`.
- Не использовать ad hoc key names вместо canonical `model`.

### `prompt_version`

`prompt_version` должен приходить из prompt metadata текущего builder'а.

Текущий canonical pattern:

- `DayBrief`: `backend/app/services/day_brief.py:1059` — `prompt_meta.get("version")` или fallback `DAY_BRIEF_PROMPT_VERSION`.
- `WeekBrief`: `backend/app/services/week_brief_service.py:239` — `prompt_meta.get("version")`.

Правило:

- Prompt builder обязан возвращать metadata bundle с `version`.
- Emitter получает именно версию prompt contract, а не произвольную app version.

### `benchmark_linkage`

Benchmark linkage состоит из пары:

- `benchmark_run_id`
- `benchmark_link`

Текущий canonical pattern:

- `DayBrief`: `_log_day_brief_event(..., benchmark_run_id=..., benchmark_link=...)`.
- `WeekBrief`: `_log_week_brief(..., benchmark_run_id=..., benchmark_link=...)`.
- Наличие `benchmark_run_id` автоматически триггерит `quality.benchmark_linked`.

Рекомендации:

- `benchmark_run_id` делайте стабильным идентификатором конкретного rerun/case pack.
- `benchmark_link` храните как путь до артефакта, markdown summary, `tmp/quality_benchmark_runs/...` или иной reproducible locator.

Примеры хороших значений:

- `benchmark_run_id="natal-rerun-2026-03-19"`
- `benchmark_link="docs/ASTRO_QUALITY_BENCHMARK_2026-03-19_NATAL_RERUN.md"`
- `benchmark_link="tmp/quality_benchmark_runs/20260327T101500Z_natal_rerun.json"`

## Example logs

### `quality.schema_failure`

```json
{
  "timestamp": "2026-03-27T08:11:54.120345Z",
  "event": "quality.schema_failure",
  "module": "FEED-PERSONALIZED-DAILY",
  "fn": "build_day_brief_payload",
  "block": "ASSEMBLY",
  "correlation_id": "1d8b9b7f-b8d6-4b3d-8d80-8f39f1c6d991",
  "trace_id": "54c3fe54-f92c-4eb2-96d8-f0fdf7e74466",
  "correlation_source": "header",
  "model": "deterministic_repo",
  "prompt_version": "day_brief_prompt_v2",
  "fallback_mode": true,
  "confidence_bucket": "low",
  "generation_mode": "llm",
  "reason": "validation_failed",
  "error": "DayBrief validation error"
}
```

### `quality.invalid_json` → `quality.prompt_repair` → `quality.repair_success`

```json
{"event":"quality.invalid_json","module":"WEEK-BRIEF","fn":"build_week_brief_payload","block":"ASSEMBLY","trace_id":"7d90...","model":"deterministic","prompt_version":"week_brief_prompt_v2","fallback_mode":true,"confidence_bucket":"low","report_id":"42","primary_reason_code":"chunk_parse_degraded","reason_codes":["chunk_parse_degraded","fallback_policy"],"chunk_parse_degraded":true}
{"event":"quality.prompt_repair","module":"WEEK-BRIEF","fn":"build_week_brief_payload","block":"ASSEMBLY","trace_id":"7d90...","model":"deterministic","prompt_version":"week_brief_prompt_v2","fallback_mode":true,"confidence_bucket":"low","report_id":"42","repair_outcome":"retry_prompted"}
{"event":"quality.repair_success","module":"WEEK-BRIEF","fn":"build_week_brief_payload","block":"ASSEMBLY","trace_id":"7d90...","model":"deterministic","prompt_version":"week_brief_prompt_v2","fallback_mode":true,"confidence_bucket":"low","report_id":"42","repair_outcome":"salvaged"}
```

### `quality.benchmark_linked`

```json
{
  "timestamp": "2026-03-27T08:22:00.000000Z",
  "event": "quality.benchmark_linked",
  "module": "FEED-PERSONALIZED-DAILY",
  "fn": "build_day_brief_payload",
  "block": "ASSEMBLY",
  "trace_id": "95d0c9c5-9d3f-4b65-a4db-2e1d7c70b1d4",
  "model": "deterministic_repo",
  "prompt_version": "day_brief_prompt_v2",
  "fallback_mode": false,
  "confidence_bucket": "medium",
  "benchmark_run_id": "daybrief-rerun-2026-03-27",
  "benchmark_link": "tmp/quality_benchmark_runs/daybrief-rerun-2026-03-27.md"
}
```

## Verification commands

### Pytest: targeted quality telemetry checks

DayBrief quality event coverage:

```bash
python3 -m pytest -q tests/test_day_brief.py -k quality
```

WeekBrief quality event coverage:

```bash
python3 -m pytest -q tests/test_week_brief_service.py -k quality
```

Emitter contract coverage:

```bash
python3 -m pytest -q tests/test_logging_utils_grace.py
```

### Backend quick profile

Канонический быстрый прогон backend после существенных правок:

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
```

### Grep / log inspection

Показать все quality events в sink:

```bash
rg -n 'quality\.' logs/feed.jsonl
```

Показать только benchmark linkage:

```bash
rg -n 'quality\.benchmark_linked|benchmark_run_id|benchmark_link' logs/feed.jsonl
```

Показать события по конкретному trace:

```bash
TRACE_ID="<trace-id>"
rg -n "$TRACE_ID|quality\." logs/feed.jsonl
```

Показать источники эмита в коде:

```bash
rg -n 'emit_quality_event\(|quality\.(schema_failure|invalid_json|fallback_activated|prompt_repair|repair_success|benchmark_linked)' backend tests
```

### Pipeline + grep handoff flow

Практический handoff loop:

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py \
  && rg -n 'quality\.' logs/feed.jsonl | tail -n 20
```

## Where to find these records in docs / task packet

### Task packet

Основной packet reference:

- `docs/DAY_WEEK_TASK_PACKET.md:89` — секция `Quality telemetry`
- `docs/DAY_WEEK_TASK_PACKET.md:93` — список canonical backend quality events
- `docs/DAY_WEEK_TASK_PACKET.md:94` — требование про `trace_id`, model, prompt version, fallback mode, confidence bucket, benchmark linkage

### GRACE / artifacts docs

- `docs/LOGGING_AUDIT.md:8` — correlation model и logging envelope
- `docs/LOGGING_AUDIT.md:39` — `build_grace_log_payload()` / `log_grace_event()`
- `docs/GRACE_ARTIFACTS.md` — artifact inventory и evidence contour; см. секцию `Quality telemetry evidence`
- `docs/GRACE_TEST_PLAYBOOK.md:41` — benchmark rerun command
- `docs/ASTRO_QUALITY_BENCHMARK_HARNESS.md:13` — benchmark artifacts в `tmp/quality_benchmark_runs/`

### Runtime files / artifacts

- `logs/feed.jsonl` — основной JSONL sink для quality events
- `tmp/quality_benchmark_runs/` — benchmark outputs (`.json`, `.md`)
- `docs/benchmark_manifests/` — benchmark manifests для rerun

## Reviewer checklist

Перед handoff reviewer/architect должен быстро проверить:

- все шесть canonical `quality.*` событий описаны и доступны через единый emitter;
- новые quality emitters используют canonical keys `trace_id`, `model`, `prompt_version`, `benchmark_run_id`, `benchmark_link`;
- request path действительно создаёт новый `trace_id` на запрос;
- benchmark-linked scenarios оставляют воспроизводимую ссылку на evidence artifact;
- `tests/test_day_brief.py`, `tests/test_week_brief_service.py`, `tests/test_logging_utils_grace.py` остаются зелёными в рамках задачи;
- `docs/DAY_WEEK_TASK_PACKET.md`, `docs/TASK.md` и `docs/GRACE_ARTIFACTS.md` содержат discoverable ссылку на этот runbook.

## Normalized reason-code schema

Для `day_brief.*`, `week_brief.*`, `report.workflow.*` fallback/degradation событий используем единый набор:

- `chunk_parse_degraded`
- `missing_required_sections`
- `stub_mode`
- `validation_failures`
- `fallback_policy`

Правила:

- `primary_reason_code` — первая нормализованная причина для алертов/агрегаций.
- `reason_codes` — полный массив причин без дублей.
- При invalid JSON ожидается `chunk_parse_degraded`; при структурном fallback — `fallback_policy`; при пустых обязательных секциях — `missing_required_sections`; при schema/business validation — `validation_failures`; при stub execution path — `stub_mode`.

## Stage 1 report observability

- Dedicated sink routes `report.workflow.*`, `week_brief.*`, and `report.failure_packet` to `logs/report.jsonl`.
- Unified trace envelope is required on week/report observability events: `result`, `trace_id`, `scenario_id`, `reason_codes`.
- Stage 1 emits `report.workflow.model_resolution`, `report.workflow.chunk_parse_result`, `report.workflow.chunk_matrix`, `week_brief.fallback_decision`, and automatic `report.failure_packet`.
