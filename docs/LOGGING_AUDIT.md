# LOGGING AUDIT

Обновлено под текущий `backend/app/logging_utils.py` и `backend/app/middleware/correlation.py`.

## Executive summary

- Backend использует единый `structlog` пайплайн из `backend/app/logging_utils.py:1` с JSONL-маршрутизацией по шести потокам: `feed.jsonl`, `admin.jsonl`, `catalog.jsonl`, `billing.jsonl`, `scheduler.jsonl`, `diagnostic.jsonl`.
- Корреляция уже стандартизована: `correlation_id`, `trace_id`, `correlation_source` хранятся в `contextvars`, автоматически подмешиваются в payload и выставляются HTTP middleware.
- Для HTTP запросов `CorrelationIdMiddleware` принимает `x-correlation-id` или fallback `x-request-id`, санитизирует вход, генерирует новый `trace_id` на каждый запрос и возвращает оба заголовка в response.
- Для фоновых задач доступны `bind_correlation_ids(...)`, `correlation_scope(...)` и `with_correlation_context(...)`; это закрывает прежний пробел между web-request и cron/scheduler job logging.
- Каталог/биллинг helpers уже работают поверх общего correlation API: `catalog_event_fields(...)`, `log_catalog_event(...)`, `log_grace_event(...)` и смежные helpers прокидывают correlation metadata в корень JSON события.
- Основной remaining gap теперь не в `logging_utils`, а в полноте покрытия документации/runbooks/watchers и в дисциплине использования новых helpers всеми background entrypoint'ами.

## Scope

Проверены:

- `backend/app/logging_utils.py:1`
- `backend/app/middleware/correlation.py:1`
- `backend/app/catalog_logging.py:1`
- `backend/app/main.py:1`
- `backend/app/services/access_control.py:88`
- `backend/app/services/billing.py:65`
- `backend/app/services/feed_service.py:59`
- `backend/app/services/notification.py:40`
- `backend/app/services/one_off_entitlements.py:77`
- `backend/app/services/personalized_daily.py:61`
- `backend/app/services/referral_service.py:57`
- `backend/app/services/report_workflow.py:128`
- `tests/test_logging_utils_grace.py:1`

## Backend structured logging inventory

| Slice | Files | Current state | Audit note |
| --- | --- | --- | --- |
| Core config | `backend/app/logging_utils.py:1` | `configure_structlog()` включает `merge_contextvars`, timestamper, level, stack info и `feed_admin_sink`; запись JSONL идёт через `JSONL_ROUTES`. | Актуально; старое описание `feed_admin_sink whitelist` устарело — теперь маршрутизация централизована через `JSONL_ROUTES`. |
| Correlation context | `backend/app/logging_utils.py:61` | Есть `get_correlation_ids`, `set_correlation_ids`, `resolve_correlation_context`, `with_correlation_context`, `bind_correlation_ids`, `correlation_scope`. | Актуально и достаточно для HTTP + background jobs. |
| HTTP middleware | `backend/app/middleware/correlation.py:1` | `CorrelationIdMiddleware` читает `x-correlation-id`/`x-request-id`, валидирует header, логирует sanitization в `diagnostic.correlation_middleware`, выставляет response headers. | Это уже реализованная часть, а не план. |
| GRACE runtime events | `backend/app/logging_utils.py:249` | `build_grace_log_payload()` и `log_grace_event()` автоматически подмешивают `correlation_id`, `trace_id`, `correlation_source` из contextvars либо explicit args. | Актуально; тест покрывает context inheritance. |
| Catalog/Billing events | `backend/app/catalog_logging.py:1`, `backend/app/logging_utils.py:296` | `catalog_event_fields()` собирает доменные поля и correlation metadata; billing/catalog checkout события маршрутизируются по prefix rules. | Актуально; `checkout_token_hash` нормализован backend-side через `hash_identifier()`. |
| Scheduler/notifications | `backend/app/logging_utils.py:48`, `backend/app/services/notification.py:40`, `backend/app/services/personalized_daily.py:61` | `scheduler.*`, `daily.*`, `notification.*`, `notify.*` теперь пишутся в `logs/scheduler.jsonl`. | Старый audit-пункт про “ещё не пишутся” устарел. |
| Diagnostic/CLI | `backend/app/logging_utils.py:49` | `diagnostic.*` и `llm.cli.*` идут в `logs/diagnostic.jsonl`. | Полезно для middleware/watcher troubleshooting. |

## Current JSONL routing

Текущее правило маршрутизации определено в `backend/app/logging_utils.py:51`:

- `feed.jsonl` — фиксированный набор `feed.*` событий
- `admin.jsonl` — фиксированный набор `admin.*` событий
- `catalog.jsonl` — фиксированный набор `catalog.*` catalog-state событий
- `billing.jsonl` — prefix-маршрутизация для `billing.*`, `catalog.checkout_*`, `catalog.bridge_resume_*`
- `scheduler.jsonl` — prefix-маршрутизация для `scheduler.*`, `daily.*`, `notification.*`, `notify.*`
- `diagnostic.jsonl` — prefix-маршрутизация для `diagnostic.*`, `llm.cli.*`

Практическое следствие: одно и то же доменное семейство больше не зависит от “ручного allowlist per sink”; добавление нового event-name внутри уже покрытого prefix автоматически попадает в нужный файл.

## Correlation model

### HTTP flow

- Request middleware ищет `x-correlation-id`.
- Если его нет, использует `x-request-id` как fallback.
- Если header невалиден, middleware логирует `diagnostic.correlation_middleware` и генерирует новый `correlation_id`.
- На каждый HTTP request создаётся новый `trace_id`.
- Оба значения кладутся в contextvars и возвращаются в response headers.

### Background flow

Для фоновых задач canonical API теперь такое:

- `bind_correlation_ids(source, correlation_id=None, trace_id=None)` — привязать контекст к текущему execution thread/task.
- `correlation_scope(source, ...)` — временный scope для job/операции с automatic restore предыдущего контекста.
- `with_correlation_context(...)` — lower-level context manager для явной подмены/наследования текущих id.

Рекомендация для cron/scheduler entrypoint'ов: начинать каждый логический run через `correlation_scope("scheduler")` либо `bind_correlation_ids("scheduler")`, а не выставлять поля вручную в каждом `log_grace_event(...)`.

## Catalog and billing specifics

Актуальное состояние по checkout/report logging:

- `hash_identifier(...)` в `backend/app/logging_utils.py:220` хеширует чувствительные идентификаторы c префиксом и длиной по умолчанию `sha256:<12 chars>`.
- `catalog_event_fields(...)` вытаскивает из объектов `user`, `report`, `checkout_session`, `entitlement`, `decision` нормализованные поля для события.
- `checkout_token_hash` считается на backend автоматически, если у `checkout_session` есть `resume_token`.
- `log_catalog_event(...)` и специализированные helpers из `backend/app/catalog_logging.py:1` принимают optional `correlation_id` / `trace_id` / `correlation_source`, но в типичном случае используют уже связанный runtime context.

Следствие: старая формулировка про “нужно расширить все эндпоинты генерацией correlation id из middleware” больше не соответствует коду — middleware уже существует и общий helper path готов.

## Diagnostics and sanitization

Отдельно важно зафиксировать новое поведение middleware:

- `_is_allowed_id(...)` принимает UUID либо короткий alnum идентификатор до 64 символов.
- Подозрительные входящие значения не пробрасываются дальше как есть.
- Санитизация rate-limited через `_INVALID_HEADER_LOG_INTERVAL = 60s`, чтобы не зашумлять diagnostic log.
- Событие sanitization идёт как `diagnostic.correlation_middleware`, а значит попадёт в `logs/diagnostic.jsonl`.

Это стоит использовать в runbooks при расследовании проблем с прокси/client instrumentation.

## Test coverage snapshot

- `tests/test_logging_utils_grace.py:1` проверяет context fallback, explicit override и restore semantics для `build_grace_log_payload()` / `correlation_scope()`.
- `tests/test_logging_service_api.py:1` держит regression bundle по service helpers, чтобы canonical `correlation_source` и trace propagation не деградировали в `backend/app/services/*`.
- В репозитории есть отдельные тесты для catalog logging (`tests/test_catalog_logging.py:1`), что снижает риск регресса в hash/payload нормализации.
- Backend quick profile теперь включает targeted logging bundle: `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_logging_service_api.py tests/test_logging_utils_grace.py`, плюс каноническая проверка `docker exec astro-project-backend-1 python3 scripts/pipeline.py`.

## Outdated statements to remove from older docs

Ниже перечислено, что больше не должно утверждаться в смежной документации:

- что `feed_admin_sink` нужно “расширить allowlist” для `billing.*`, `scheduler.*`, `diagnostic.*`, `llm.*`
- что scheduler/daily slices “ещё не пишутся в logs/”
- что correlation middleware только планируется
- что background jobs не имеют стандартного API для correlation binding

## Remaining follow-up

Оставшиеся задачи после обновления `logging_utils`:

1. Пройти по runbook/watcher docs и заменить старую модель allowlist на `JSONL_ROUTES`/prefix routing.
2. Явно задокументировать, какие background entrypoint'ы уже используют `correlation_scope(...)`, а какие ещё должны быть переведены.
3. При изменениях фронтенд-инструментации сверять docs с фактическими заголовками `x-correlation-id` / `x-trace-id`.
4. Держать тесты на correlation propagation рядом с middleware/helper API, а не только в общих audit notes.

## Source of truth

При расхождении документации с реализацией источником истины считать:

1. `backend/app/logging_utils.py:1`
2. `backend/app/middleware/correlation.py:1`
3. `backend/app/catalog_logging.py:1`
4. `tests/test_logging_utils_grace.py:1`
