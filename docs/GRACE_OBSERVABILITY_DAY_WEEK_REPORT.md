# GRACE-совместимое ТЗ на observability для day / week / report

## Цель

Сделать так, чтобы по логам и trace evidence можно было **без ручного копания в БД, stdout и сыром контенте chunk-ов** быстро понять:

1. на каком шаге сломался pipeline,
2. почему включился `fallback_mode`,
3. какая секция/какой chunk стал first divergence point,
4. это проблема режима запуска, модели, генерации, парсинга, валидации или fallback-policy.

Документ опирается на GRACE-подход: critical-path логирование должно быть verification-oriented, с явными semantic blocks, evidence, failure conversion и traceability.

---

## Проблема текущего состояния

Сейчас weekly/report flow частично логируется, но этого недостаточно для быстрого расследования.

Что видно по симптомам:

- `build_week_brief_payload` уходит в `fallback_mode=true`.
- В логах видны признаки уровня `quality.invalid_json` / `chunk_parse_degraded`.
- `report_chunks` часто содержат только `week_strategy`, а остальные секции либо пустые, либо невалидны.
- Даже при живой модели (`openrouter`, `gpt-4.1-nano` / `gpt-4o-mini`) weekly всё равно деградирует, если секции не приходят в ожидаемом формате.

Главная проблема: **логов недостаточно, чтобы сразу увидеть first divergent point и root cause chain**.

---

## Требование верхнего уровня

Для любого `day_brief`, `week_brief` и `report_workflow` trace должен отвечать на 7 вопросов:

1. Какой был входной запрос?
2. В каком режиме реально запустилась генерация?
3. Какую модель и fallback-chain реально использовали?
4. Какие секции ожидались, а какие реально были сгенерированы?
5. Какая секция/какой chunk сломался первой?
6. Почему именно был включён fallback?
7. Какой следующий repair scope наиболее вероятен?

---

## Основные принципы observability

### 1. Один trace = одна расследуемая история

Для каждого `report_id` / `trace_id` должна собираться полная цепочка событий:

- request
- model resolution
- queue / section generation
- raw output received
- chunk persisted
- parse result
- validation result
- fallback decision
- final response
- failure packet (если был сбой или деградация)

### 2. Нельзя логировать только факт fallback

Нужно логировать:

- **когда** решили деградировать,
- **почему**,
- **на основании каких evidence**, 
- **какой блок сломался первым**.

### 3. Нормализованные reason codes

Причина деградации не должна быть только свободным текстом.

Нужен строгий набор `reason_code` / `reason_codes`, пригодный для аналитики, алертов и grep.

### 4. Chunk-level diagnostics обязательны

Для weekly-пайплайна недостаточно знать только итоговый `fallback_mode`.
Нужно видеть диагностический результат по каждой секции.

### 5. Failure packet обязателен для любого критичного fallback/fail

Если weekly/day/report собран с деградацией или упал — система должна автоматически сформировать compact failure packet в GRACE-стиле.

---

## Лог-каналы

### Нужно добавить отдельный sink

Сейчас weekly/report нельзя удобно расследовать через `feed.jsonl`.

Нужно добавить:

- `logs/report.jsonl`

### В этот sink должны маршрутизироваться

- `report.workflow.*`
- `week_brief.*`
- `report.quality.*`
- `quality.*` (если событие относится к weekly/report)
- `report.failure_packet`

### Дополнительно

Если day-brief тоже пойдёт через сложный assembly pipeline, имеет смысл либо:

- писать `day_brief.*` в `feed.jsonl` и `report.jsonl`,
- либо выделить единый `brief.jsonl`.

Но минимально критичный шаг сейчас — **отдельный `report.jsonl`**.

---

## Обязательный envelope для critical-path событий

Для всех событий day/week/report, относящихся к critical path, обязательны следующие поля:

```json
{
  "module": "M-REPORT-WORKFLOW",
  "fn": "generate_report_sections",
  "block": "GENERATION_PARALLEL_SECTIONS",
  "event": "report.workflow.section_output_parsed",
  "result": "ok|fail|retry|skip|degraded",
  "trace_id": "TRACE-...",
  "scenario_id": "SCN-WEEK-BRIEF-BUILD",
  "use_case_id": "UC-WEEK-REPORT-READ",
  "phase_id": "PHASE-FORECAST",
  "wave_id": "WAVE-WEEK-BRIEF",
  "report_id": "...",
  "report_type": "week_forecast",
  "chunk_id": "...",
  "section_id": "week_strategy",
  "timestamp": "ISO-8601"
}
```

### Обязательные поля

- `module`
- `fn`
- `block`
- `event`
- `result`
- `timestamp`
- `trace_id`
- `scenario_id`
- `use_case_id`
- хотя бы один идентификатор сущности: `report_id` / `user_id` / `request_id`

### Желательные поля

- `phase_id`
- `wave_id`
- `report_type`
- `section_id`
- `chunk_id`
- `correlation_id`
- `fallback_mode`

---

## Нормализованные reason codes

### Базовый список

```text
stub_mode
llm_request_failed
llm_timeout
llm_invalid_json
json_not_list
json_wrong_shape
empty_block_list
unsupported_block_types
insufficient_block_count
chunk_status_not_completed
missing_required_sections
required_section_empty
week_seed_days_missing
validation_failed
persistence_incomplete
parse_exception
fallback_policy_applied
legacy_mapping_degraded
```

### Правила

- В итоговом fallback event должно быть поле `reason_codes: string[]`.
- Если есть одна главная причина — дополнительно писать `primary_reason_code`.
- Если fallback вызван цепочкой проблем, первая причина должна быть самой ранней по pipeline.

### Пример

```json
{
  "event": "week_brief.fallback_decision",
  "result": "degraded",
  "fallback_mode": true,
  "primary_reason_code": "missing_required_sections",
  "reason_codes": [
    "missing_required_sections",
    "chunk_status_not_completed",
    "empty_block_list"
  ],
  "first_divergent_section": "week_relationships"
}
```

---

## События pipeline: обязательный минимум

Ниже — минимальный набор событий, который должен существовать в trace.

### 1. Вход в сценарий

#### `report.workflow.request_received`

Когда приходит запрос на создание/обновление отчёта.

Поля:
- `report_type`
- `source` (`api`, `admin`, `worker`, `scheduler`)
- `user_id`
- `request_payload_shape`
- `requested_mode`

---

### 2. Разрешение режима и модели

#### `report.workflow.model_resolution`

Должно сразу отвечать на вопрос: мы точно не в `stub`?

Поля:
- `requested_model`
- `resolved_model`
- `resolved_provider_mode`
- `fallback_chain`
- `generation_mode`
- `stub_mode`
- `source`

Пример:

```json
{
  "event": "report.workflow.model_resolution",
  "result": "ok",
  "report_id": "...",
  "requested_model": "openai/gpt-4.1-nano",
  "resolved_model": "openai/gpt-4.1-nano",
  "resolved_provider_mode": "openrouter",
  "fallback_chain": ["openai/gpt-4o-mini"],
  "generation_mode": "live",
  "stub_mode": false,
  "source": "POST /api/reports/create"
}
```

---

### 3. Сбор контекста

#### `report.workflow.context_ready`

Поля:
- `birth_data_present`
- `birth_time_used`
- `week_seed_days_present`
- `facts_count`
- `domain_signals_count`
- `fallback_inputs_used`

---

### 4. Разрешение набора секций

#### `report.workflow.section_specs_resolved`

Поля:
- `expected_sections`
- `required_sections`
- `optional_sections`
- `schema_version`

---

### 5. Очередь генерации

#### `report.workflow.chunk_queue_initialized`

Поля:
- `sections_total`
- `parallelism`
- `worker_mode`

---

### 6. Старт генерации секции

#### `report.workflow.section_generation_start`

Поля:
- `section_id`
- `prompt_contract_version`
- `model`

---

### 7. Получен raw output

#### `report.workflow.section_output_received`

Поля:
- `section_id`
- `raw_chars`
- `raw_kind` (`json`, `markdown`, `text`, `empty`, `unknown`)
- `llm_attempt`

---

### 8. Chunk сохранён

#### `report.workflow.chunk_persisted`

Поля:
- `section_id`
- `chunk_id`
- `chunk_status`
- `content_chars`

---

### 9. Результат parse/normalization по chunk

#### `report.workflow.chunk_parse_result`

Это ключевое диагностическое событие.

Поля:
- `section_id`
- `chunk_status`
- `content_kind`
- `json_valid`
- `json_top_type`
- `block_count`
- `supported_block_count`
- `unsupported_block_types`
- `summary_present`
- `degraded_reason`

Пример хорошего кейса:

```json
{
  "event": "report.workflow.chunk_parse_result",
  "result": "ok",
  "report_id": "...",
  "section_id": "week_strategy",
  "chunk_status": "completed",
  "content_kind": "json_list",
  "json_valid": true,
  "json_top_type": "list",
  "block_count": 6,
  "supported_block_count": 6,
  "unsupported_block_types": [],
  "summary_present": true,
  "degraded_reason": null
}
```

Пример плохого кейса:

```json
{
  "event": "report.workflow.chunk_parse_result",
  "result": "degraded",
  "report_id": "...",
  "section_id": "week_relationships",
  "chunk_status": "completed",
  "content_kind": "markdown",
  "json_valid": false,
  "json_top_type": null,
  "block_count": 0,
  "supported_block_count": 0,
  "unsupported_block_types": [],
  "summary_present": false,
  "degraded_reason": "llm_invalid_json"
}
```

---

### 10. Сводная матрица секций

#### `report.workflow.chunk_matrix`

Это первое событие, на которое должен смотреть разработчик при weekly-аварии.

Поля:
- `sections_total`
- `sections_completed`
- `sections_fallback`
- `sections_failed`
- `required_sections_missing`
- `section_statuses`

Пример:

```json
{
  "event": "report.workflow.chunk_matrix",
  "result": "degraded",
  "report_id": "...",
  "sections_total": 6,
  "sections_completed": 4,
  "sections_fallback": 1,
  "sections_failed": 1,
  "required_sections_missing": ["week_relationships", "week_events"],
  "section_statuses": {
    "week_strategy": "completed",
    "week_work_money": "completed",
    "week_relationships": "completed_but_invalid_json",
    "week_energy": "completed",
    "week_events": "missing",
    "week_timing": "failed"
  }
}
```

---

### 11. Старт сборки week brief

#### `week_brief.assembly_start`

Поля:
- `report_id`
- `required_sections_present`
- `sections_available`

---

### 12. Сборка deep sections

#### `week_brief.deep_sections_built`

Поля:
- `deep_sections_count`
- `topline_present`
- `days_map_present`
- `actions_present`
- `risks_present`

---

### 13. Решение о fallback

#### `week_brief.fallback_decision`

Ключевое событие weekly-assembly.

Поля:
- `fallback_mode`
- `primary_reason_code`
- `reason_codes`
- `first_divergent_section`
- `required_sections_missing`
- `quality_score`
- `confidence`

---

### 14. Финальная сборка

#### `week_brief.built`

Поля:
- `fallback_mode`
- `sections_rendered`
- `deep_sections_count`
- `telemetry_blocks`
- `response_size_chars`

---

### 15. Возврат API-ответа

#### `api.week_report.response_returned`

Поля:
- `http_status`
- `fallback_mode`
- `response_contract`
- `latency_ms`

---

## Failure packet (обязателен)

Если weekly/day/report завершился с `fallback_mode=true`, `status=failed` или критичной деградацией, надо автоматически формировать compact failure packet.

### Событие

#### `report.failure_packet`

### Поля

- `scenario_id`
- `report_id`
- `first_divergent_module`
- `first_divergent_fn`
- `first_divergent_block`
- `observed_evidence`
- `expected_evidence`
- `probable_next_repair_scope`

### Пример

```json
{
  "event": "report.failure_packet",
  "result": "fail",
  "scenario_id": "SCN-WEEK-BRIEF-BUILD",
  "report_id": "...",
  "first_divergent_module": "M-WEEK-BRIEF",
  "first_divergent_fn": "build_week_brief_payload",
  "first_divergent_block": "DEEP_SECTION_PARSE",
  "observed_evidence": {
    "required_sections_present": ["week_strategy"],
    "missing_sections": ["week_relationships", "week_events"],
    "chunk_parse_degraded": true
  },
  "expected_evidence": {
    "required_sections_present": [
      "week_strategy",
      "week_work_money",
      "week_relationships",
      "week_energy"
    ],
    "all_required_chunks_status": "completed",
    "json_block_lists_valid": true
  },
  "probable_next_repair_scope": [
    "backend/app/services/report_workflow.py",
    "backend/app/services/week_brief_service.py"
  ]
}
```

---

## Правила first divergence

Система должна уметь автоматически вычислять first divergence.

### Источник истины

First divergence — это **самое раннее событие в pipeline, после которого trace уже нельзя привести к успешному expected path без ремонта**.

### Приоритет определения

1. `model_resolution.stub_mode=true` → divergence в `MODEL_RESOLUTION`
2. не получен raw output → divergence в `SECTION_OUTPUT`
3. chunk сохранён, но не completed → divergence в `CHUNK_PERSISTENCE`
4. parse invalid json → divergence в `CHUNK_PARSE`
5. required sections missing → divergence в `SECTION_COVERAGE`
6. week brief validation failed → divergence в `ASSEMBLY_VALIDATION`
7. fallback policy forced despite partial data → divergence в `FALLBACK_POLICY`

---

## Метрики и counters

Помимо JSONL, нужны агрегируемые counters.

### Counters

- `report_workflow_started_total`
- `report_workflow_completed_total`
- `report_workflow_failed_total`
- `week_brief_fallback_total`
- `week_brief_success_total`
- `chunk_parse_invalid_json_total`
- `chunk_parse_empty_block_list_total`
- `missing_required_sections_total`
- `stub_mode_invocations_total`
- `failure_packet_emitted_total`

### Breakdown dimensions

- `report_type`
- `model`
- `provider_mode`
- `section_id`
- `reason_code`
- `fallback_mode`

---

## Требования к тестам

Нужны не только unit-тесты, но и trace assertions.

### Обязательные кейсы

#### 1. Live-mode resolution

Если `POST /api/reports/create` запускается в live mode:
- в trace должен быть `report.workflow.model_resolution`
- `stub_mode=false`
- `generation_mode=live`

#### 2. Invalid JSON chunk

Если секция вернула markdown вместо JSON list:
- должен быть `chunk_parse_result.result=degraded`
- `degraded_reason=llm_invalid_json`

#### 3. Missing required sections

Если отсутствуют required sections:
- должен быть `report.workflow.chunk_matrix`
- `required_sections_missing` непустой
- должен быть `week_brief.fallback_decision`

#### 4. Fallback with reason codes

Если `fallback_mode=true`:
- `reason_codes` обязателен
- `primary_reason_code` обязателен

#### 5. Failure packet emission

Если weekly failed или degraded:
- должен автоматически появиться `report.failure_packet`

---

## CLI / thin harness для расследования

Нужен один thin tool, который умеет собирать trace по `report_id` или `trace_id`.

### Интерфейс

```bash
python -m tools.trace_report --report-id <id>
python -m tools.trace_report --trace-id <id>
python3 tools/trace_report.py --report-id <id>
```

### README / usage snippet

`tools/trace_report.py` — thin investigation CLI для быстрого GRACE-style разбора одного weekly/day/report trace.

Примеры:

```bash
python3 tools/trace_report.py --report-id 8d9f... \
  --log-path logs/report.jsonl

python3 tools/trace_report.py --trace-id 1b2c... \
  --log-path logs/report.jsonl
```

CLI собирает данные из `logs/report.jsonl` и БД, затем печатает:
- request info,
- model resolution,
- chunk matrix,
- chunk parse results,
- fallback decision,
- failure packet,
- final response summary.

Это даёт быстрый путь понять, был ли `live/stub` режим, какая модель реально резолвилась, какие секции деградировали и почему включился fallback.

### Что должен печатать

1. request info
2. model resolution
3. section matrix
4. chunk parse results
5. fallback decision
6. failure packet
7. final response summary

### Польза

Это даст быстрый GRACE-style investigation path без ручного поиска по нескольким источникам.

---

## Изменения в коде: минимальный rollout

### Этап 1 — самый быстрый выигрыш

1. Добавить `logs/report.jsonl`.
2. Прокинуть routing для:
   - `report.workflow.*`
   - `week_brief.*`
   - `report.failure_packet`
3. Добавить в critical events поле `result`.
4. Добавить `report.workflow.model_resolution`.
5. Добавить `report.workflow.chunk_parse_result`.
6. Добавить `report.workflow.chunk_matrix`.
7. Добавить `week_brief.fallback_decision`.
8. Добавить `report.failure_packet`.

### Этап 2 — нормализованные причины

1. Ввести enum reason codes.
2. Привести все fallback/degrade paths к этим code-ам.
3. Добавить `primary_reason_code` и `reason_codes[]`.

### Этап 3 — trace tooling

1. Сделать `tools.trace_report`.
2. Добавить trace assertions в тесты.
3. Добавить summary-команды для CI / debug-run.

---

## Минимальные acceptance criteria

### A. По одному `report_id` можно за 1–2 минуты понять:
- live или stub mode,
- какая модель реально использовалась,
- какие секции ожидались,
- какие секции реально пришли,
- какой chunk первым деградировал,
- почему включился fallback,
- где вероятнее всего чинить код.

### B. Для каждого weekly fallback обязательно есть:
- `chunk_matrix`
- `fallback_decision`
- `failure_packet`

### C. Нет weekly/report сценариев, в которых fallback случился без `reason_codes`.

### D. Нет critical-path report/week событий без `result`.

---

## Рекомендуемая схема событий для day_brief

Хотя основная боль сейчас в weekly, day тоже лучше привести к той же дисциплине.

Минимум:

- `day_brief.request_received`
- `day_brief.context_ready`
- `day_brief.factors_ranked`
- `day_brief.assembly_start`
- `day_brief.fallback_decision`
- `day_brief.built`
- `api.day_brief.response_returned`

Если day строится partially from legacy feed:
- `day_brief.legacy_mapping_degraded`

---

## Финальный вывод

Чтобы по логам **сразу** понимать, что произошло, вам не нужен просто «ещё один debug print».
Нужна полноценная GRACE-совместимая диагностическая модель:

- отдельный log sink,
- обязательный trace envelope,
- нормализованные reason codes,
- chunk-level parse diagnostics,
- section matrix,
- fallback decision event,
- automatic failure packet,
- thin investigation CLI.

Это переведёт weekly/day/report из режима:

> «видим, что снова fallback, но надо ещё руками долго разбираться»

в режим:

> «за 30–60 секунд видно, где именно случился first divergence и какой следующий repair scope». 
