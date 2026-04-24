"""Structured logging helpers for all GRACE slices."""

# ############################################################################
# AI_HEADER: MODULE_TRACE_LOGGING
# ROLE: Own canonical trace context, structured payload shaping, and JSONL sinks.
# DEPENDENCIES: structlog, contextvars, pathlib.
# GRACE_ANCHORS: [TRACE_EVENT_CATALOG, TRACE_CONTEXT_STATE, TRACE_CONTEXT_BINDING, TRACE_ASYNC_CONTEXT, TRACE_VALUE_NORMALIZATION, TRACE_PAYLOAD_BUILDERS, TRACE_CATALOG_EVENT_LOGGING, TRACE_JSONL_ROUTING, TRACE_STRUCTLOG_CONFIG]
# ############################################################################

# START_MODULE_CONTRACT: M-TRACE-LOGGING
# purpose: Provide canonical correlation context and GRACE-aware structured logging payload helpers.
# owns:
#   - backend/app/logging_utils.py
# inputs:
#   - Correlation identifiers from FastAPI middleware, jobs, and service entrypoints
#   - Event names and module/function/block metadata from backend active-slice services
#   - Structured event dictionaries emitted by structlog processors
# outputs:
#   - Context-local correlation snapshots for downstream services
#   - Normalized GRACE log payloads carrying module, function, block, and trace identifiers
#   - JSONL event records routed to active-slice operational log files
# dependencies:
#   - structlog contextvars for request/job scoped correlation binding
#   - pathlib/os/json for JSONL route resolution and sink writes
#   - backend/app/middleware/correlation.py for FastAPI request correlation producers
# trace_obligations:
#   - Exported helpers preserve correlation_id, trace_id, correlation_source, and request_id semantics
#   - GRACE payload builders keep module/fn/block fields explicit for post-test evidence attribution
#   - JSONL routing stays event-name/prefix driven and does not introduce a new logging transport
# side_effects:
#   - Binds/unbinds structlog contextvars
#   - Appends selected events to JSONL log files
#   - Configures structlog processors once per process
# invariants:
#   - Explicit caller-supplied correlation fields win over context fields
#   - None values are omitted from normalized log payloads
#   - Routing failures must not break request or job execution
# failure_policy:
#   - JSONL append or routing failures degrade silently and must not block request/job execution
#   - Context binding helpers restore prior context on scope exit
#   - Structlog configuration remains idempotent per process
# non_goals:
#   - Redesigning the logging transport
#   - Changing catalog, billing, report, scheduler, or diagnostic event semantics
# END_MODULE_CONTRACT: M-TRACE-LOGGING

# START_MODULE_MAP: M-TRACE-LOGGING
# public_entrypoints:
#   - get_correlation_ids -> context snapshot for middleware, services, and tests
#   - set_correlation_ids -> explicit context binding for request/job producers
#   - resolve_correlation_context -> caller/context merge for downstream payload builders
#   - with_correlation_context -> scoped context override for synchronous flows
#   - bind_correlation_ids -> canonical correlation initialization for request/job entrypoints
#   - correlation_scope -> scoped bind/restore helper for jobs and tests
#   - run_with_correlation -> async helper preserving correlation across await boundaries
#   - hash_identifier -> stable identifier hashing for operational payloads
#   - build_catalog_event_payload -> normalized structured payload shaping
#   - build_grace_log_payload -> canonical module/function/block payload builder
#   - log_grace_event -> correlation-aware GRACE event emission helper
#   - catalog_event_fields -> catalog payload enrichment helper
#   - log_catalog_event -> catalog event logging helper
#   - feed_admin_sink -> JSONL sink routing processor
#   - configure_structlog -> process-level structlog bootstrap
# internal_entrypoints:
#   - _unbind_structlog_keys -> remove stale contextvars before rebinding
#   - _attach_correlation_fields -> merge ambient correlation into payloads without overriding explicit fields
#   - _async_correlation_context -> async scope wrapper around with_correlation_context
#   - _normalize_log_value -> datetime/uuid/enum normalization for payload serialization
#   - _extract_attr -> safe object attribute extraction for payload shaping
#   - _json_default -> JSON fallback serializer for JSONL sinks
#   - _append_event -> append structured events to routed JSONL files
# semantic_blocks:
#   - TRACE_EVENT_CATALOG: event-name and prefix routing declarations
#   - TRACE_CONTEXT_STATE: ContextVar state and correlation snapshot helpers
#   - TRACE_CONTEXT_BINDING: correlation bind/scope helpers for middleware and jobs
#   - TRACE_ASYNC_CONTEXT: async correlation preservation helper
#   - TRACE_VALUE_NORMALIZATION: safe identifier/hash/value normalization helpers
#   - TRACE_PAYLOAD_BUILDERS: catalog and GRACE payload shaping helpers
#   - TRACE_CATALOG_EVENT_LOGGING: catalog event envelope helpers
#   - TRACE_JSONL_ROUTING: structlog processor JSONL sink routing
#   - TRACE_STRUCTLOG_CONFIG: process-level structlog configuration
# owned_tests:
#   - tests/test_logging_utils_grace.py
#   - tests/test_catalog_logging.py
# adjacent_modules:
#   - backend/app/middleware/correlation.py
#   - backend/app/catalog_logging.py
#   - backend/app/main.py
# END_MODULE_MAP: M-TRACE-LOGGING

from __future__ import annotations

import inspect
import json
import logging
import os
import hashlib
import uuid
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, TypedDict

import structlog
from structlog.contextvars import bind_contextvars, merge_contextvars, unbind_contextvars

# START_BLOCK: TRACE_EVENT_CATALOG
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = Path(os.getenv("ASTRO_LOG_DIR", PROJECT_ROOT / "logs")).resolve()

FEED_EVENTS = {
    "feed.entry",
    "feed.debug",
    "feed.error",
    "feed.block.start",
    "feed.block.end",
    "feed.generated",
    "feed.semantic_blocks",
    "day_brief.built",
    "day_brief.fallback",
    "day_brief.validation_failed",
    "day_brief.response_returned",
}
ADMIN_EVENTS = {
    "admin.entry",
    "admin.queue",
    "admin.section_regenerate",
    "admin.export",
    "admin.error",
    "admin.entitlement_grant",
}
CATALOG_EVENTS = {
    "catalog.history_start",
    "catalog.history_success",
    "catalog.checkout_start",
    "catalog.checkout_decision",
    "catalog.checkout_payment_created",
    "catalog.checkout_success",
    "catalog.checkout_denied",
    "catalog.checkout_resume_ready",
    "catalog.bridge_resume_start",
    "catalog.bridge_resume_success",
    "catalog.checkout_status",
    "catalog.error",
}
REPORT_EVENTS = {
    "report.failure_packet",
    "week_brief_built",
    "week_brief_fallback_triggered",
    "week_brief_validation_failed",
    "week_brief.response_returned",
}

BILLING_PREFIXES = ("billing.", "catalog.checkout_", "catalog.bridge_resume_")
REPORT_PREFIXES = ("report.workflow.",)
SCHEDULER_PREFIXES = ("scheduler.", "daily.", "notification.", "notify.")
DIAGNOSTIC_PREFIXES = ("diagnostic.", "llm.cli.")

JSONL_ROUTES: tuple[tuple[str, set[str] | None, Sequence[str] | None], ...] = (
    ("feed.jsonl", FEED_EVENTS, None),
    ("admin.jsonl", ADMIN_EVENTS, None),
    ("catalog.jsonl", CATALOG_EVENTS, None),
    ("report.jsonl", REPORT_EVENTS, REPORT_PREFIXES),
    ("billing.jsonl", None, BILLING_PREFIXES),
    ("scheduler.jsonl", None, SCHEDULER_PREFIXES),
    ("diagnostic.jsonl", None, DIAGNOSTIC_PREFIXES),
)
# END_BLOCK: TRACE_EVENT_CATALOG


# START_BLOCK: TRACE_CONTEXT_STATE
class CorrelationContext(TypedDict):
    correlation_id: Optional[str]
    trace_id: Optional[str]
    correlation_source: Optional[str]
    request_id: Optional[str]


_CORRELATION_ID_VAR: ContextVar[Optional[str]] = ContextVar("astro_correlation_id", default=None)
_TRACE_ID_VAR: ContextVar[Optional[str]] = ContextVar("astro_trace_id", default=None)
_CORRELATION_SOURCE_VAR: ContextVar[Optional[str]] = ContextVar("astro_correlation_source", default=None)
_REQUEST_ID_VAR: ContextVar[Optional[str]] = ContextVar("astro_request_id", default=None)
_STRUCTLOG_CORRELATION_KEYS = ("correlation_id", "trace_id", "correlation_source", "request_id")


# START_CONTRACT: FN-UNBIND-STRUCTLOG-CORRELATION-KEYS
def _unbind_structlog_keys() -> None:
    for key in _STRUCTLOG_CORRELATION_KEYS:
        try:
            unbind_contextvars(key)
        except LookupError:  # pragma: no cover
            continue
# END_CONTRACT: FN-UNBIND-STRUCTLOG-CORRELATION-KEYS


# START_CONTRACT: FN-GET-CORRELATION-IDS
def get_correlation_ids() -> CorrelationContext:
    return {
        "correlation_id": _CORRELATION_ID_VAR.get(),
        "trace_id": _TRACE_ID_VAR.get(),
        "correlation_source": _CORRELATION_SOURCE_VAR.get(),
        "request_id": _REQUEST_ID_VAR.get(),
    }
# END_CONTRACT: FN-GET-CORRELATION-IDS


# START_CONTRACT: FN-SET-CORRELATION-IDS
def set_correlation_ids(
    *,
    correlation_id: Optional[str],
    trace_id: Optional[str],
    correlation_source: Optional[str],
    request_id: Optional[str] = None,
) -> CorrelationContext:
    context: CorrelationContext = {
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "correlation_source": correlation_source,
        "request_id": request_id,
    }
    _CORRELATION_ID_VAR.set(context["correlation_id"])
    _TRACE_ID_VAR.set(context["trace_id"])
    _CORRELATION_SOURCE_VAR.set(context["correlation_source"])
    _REQUEST_ID_VAR.set(context["request_id"])
    _unbind_structlog_keys()
    bind_values = {key: value for key, value in context.items() if value is not None}
    if bind_values:
        bind_contextvars(**bind_values)
    return context
# END_CONTRACT: FN-SET-CORRELATION-IDS


# START_CONTRACT: FN-RESOLVE-CORRELATION-CONTEXT
def resolve_correlation_context(
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    request_id: Optional[str] = None,
) -> CorrelationContext:
    current = get_correlation_ids()
    return {
        "correlation_id": correlation_id or current["correlation_id"],
        "trace_id": trace_id or current["trace_id"],
        "correlation_source": correlation_source or current["correlation_source"],
        "request_id": request_id or current["request_id"],
    }
# END_CONTRACT: FN-RESOLVE-CORRELATION-CONTEXT


# START_CONTRACT: FN-ATTACH-CORRELATION-FIELDS
def _attach_correlation_fields(
    payload: dict[str, Any],
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    context = resolve_correlation_context(
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        request_id=request_id,
    )
    for key, value in context.items():
        if value is not None and key not in payload:
            payload[key] = value
    return payload
# END_CONTRACT: FN-ATTACH-CORRELATION-FIELDS
# END_BLOCK: TRACE_CONTEXT_STATE


# START_BLOCK: TRACE_CONTEXT_BINDING
# START_CONTRACT: FN-WITH-CORRELATION-CONTEXT
@contextmanager
def with_correlation_context(
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Iterator[CorrelationContext]:
    previous = get_correlation_ids()
    next_context = resolve_correlation_context(
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        request_id=request_id,
    )
    set_correlation_ids(**next_context)
    try:
        yield next_context
    finally:
        set_correlation_ids(**previous)
# END_CONTRACT: FN-WITH-CORRELATION-CONTEXT


# START_CONTRACT: FN-BIND-CORRELATION-IDS
def bind_correlation_ids(
    source: str,
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> CorrelationContext:
    correlation_id = correlation_id or str(uuid.uuid4())
    trace_id = trace_id or str(uuid.uuid4())
    request_id = request_id or trace_id
    return set_correlation_ids(
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=source,
        request_id=request_id,
    )
# END_CONTRACT: FN-BIND-CORRELATION-IDS


# START_CONTRACT: FN-CORRELATION-SCOPE
@contextmanager
def correlation_scope(
    source: str,
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Iterator[CorrelationContext]:
    previous = get_correlation_ids()
    context = bind_correlation_ids(source, correlation_id=correlation_id, trace_id=trace_id, request_id=request_id)
    try:
        yield context
    finally:
        set_correlation_ids(
            correlation_id=previous["correlation_id"],
            trace_id=previous["trace_id"],
            correlation_source=previous["correlation_source"],
            request_id=previous["request_id"],
        )
# END_CONTRACT: FN-CORRELATION-SCOPE
# END_BLOCK: TRACE_CONTEXT_BINDING


# START_BLOCK: TRACE_ASYNC_CONTEXT
# START_CONTRACT: FN-RUN-WITH-CORRELATION
async def run_with_correlation(
    func,
    correlation_context: CorrelationContext | None,
    *args: Any,
    **kwargs: Any,
):
    context = correlation_context or get_correlation_ids()
    async with _async_correlation_context(context):
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
# END_CONTRACT: FN-RUN-WITH-CORRELATION


# START_CONTRACT: FN-ASYNC-CORRELATION-CONTEXT
@asynccontextmanager
async def _async_correlation_context(context: CorrelationContext):
    with with_correlation_context(
        correlation_id=context.get("correlation_id"),
        trace_id=context.get("trace_id"),
        correlation_source=context.get("correlation_source"),
        request_id=context.get("request_id"),
    ):
        yield
# END_CONTRACT: FN-ASYNC-CORRELATION-CONTEXT
# END_BLOCK: TRACE_ASYNC_CONTEXT


# START_BLOCK: TRACE_VALUE_NORMALIZATION
# START_CONTRACT: FN-HASH-IDENTIFIER
def hash_identifier(value: Optional[str], *, prefix: str = "sha256", length: int = 12) -> Optional[str]:
    if not value:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:length]}"
# END_CONTRACT: FN-HASH-IDENTIFIER


# START_CONTRACT: FN-NORMALIZE-LOG-VALUE
def _normalize_log_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()
    if hasattr(value, "value"):
        return getattr(value, "value")
    return value
# END_CONTRACT: FN-NORMALIZE-LOG-VALUE
# END_BLOCK: TRACE_VALUE_NORMALIZATION


# START_BLOCK: TRACE_PAYLOAD_BUILDERS
# START_CONTRACT: FN-BUILD-CATALOG-EVENT-PAYLOAD
def build_catalog_event_payload(**fields: Any) -> dict[str, Any]:
    return {
        key: _normalize_log_value(value)
        for key, value in fields.items()
        if value is not None
    }
# END_CONTRACT: FN-BUILD-CATALOG-EVENT-PAYLOAD


# START_CONTRACT: FN-BUILD-GRACE-LOG-PAYLOAD
def build_grace_log_payload(
    *,
    module: str,
    fn: str,
    block: str,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    request_id: Optional[str] = None,
    **fields: Any,
) -> dict[str, Any]:
    payload = {
        "module": module,
        "fn": fn,
        "block": block,
        **fields,
    }
    payload = _attach_correlation_fields(
        payload,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
        request_id=request_id,
    )
    return build_catalog_event_payload(**payload)
# END_CONTRACT: FN-BUILD-GRACE-LOG-PAYLOAD


# START_CONTRACT: FN-LOG-GRACE-EVENT
def log_grace_event(
    level: str,
    event: str,
    *,
    module: str,
    fn: str,
    block: str,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    request_id: Optional[str] = None,
    **fields: Any,
) -> None:
    log_fn = getattr(structlog.get_logger(), level)
    log_fn(
        event,
        **build_grace_log_payload(
            module=module,
            fn=fn,
            block=block,
            correlation_id=correlation_id,
            trace_id=trace_id,
            correlation_source=correlation_source,
            request_id=request_id,
            **fields,
        ),
    )
# END_CONTRACT: FN-LOG-GRACE-EVENT
# END_BLOCK: TRACE_PAYLOAD_BUILDERS


# START_BLOCK: TRACE_CATALOG_EVENT_LOGGING
# START_CONTRACT: FN-EXTRACT-ATTR
def _extract_attr(obj: Any, attr: str) -> Optional[Any]:
    return getattr(obj, attr, None) if obj is not None else None
# END_CONTRACT: FN-EXTRACT-ATTR


# START_CONTRACT: FN-CATALOG-EVENT-FIELDS
def catalog_event_fields(
    *,
    user: Any | None = None,
    report: Any | None = None,
    checkout_session: Any | None = None,
    entitlement: Any | None = None,
    decision: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = dict(fields)

    def set_field(key: str, value: Any) -> None:
        if value is None or key in payload:
            return
        payload[key] = value

    if user is not None:
        set_field("user_id", _extract_attr(user, "id"))
        set_field("user_telegram_id", _extract_attr(user, "telegram_id"))

    if report is not None:
        set_field("report_id", _extract_attr(report, "id"))
        set_field("report_type", _extract_attr(report, "report_type"))
        set_field("report_status", _extract_attr(report, "status"))
        set_field("entitlement_id", _extract_attr(report, "entitlement_id"))
        set_field("checkout_session_id", _extract_attr(report, "checkout_session_id"))

    if entitlement is not None:
        set_field("entitlement_id", _extract_attr(entitlement, "id"))

    if checkout_session is not None:
        set_field("checkout_session_id", _extract_attr(checkout_session, "id"))
        set_field("checkout_session_status", _extract_attr(checkout_session, "status"))
        set_field("checkout_session_provider", _extract_attr(checkout_session, "provider"))
        set_field("checkout_session_kind", _extract_attr(checkout_session, "billing_kind"))
        set_field("checkout_product_code", _extract_attr(checkout_session, "product_code"))
        set_field("checkout_report_type", _extract_attr(checkout_session, "report_type"))
        resume_token = _extract_attr(checkout_session, "resume_token")
        if resume_token and "checkout_token_hash" not in payload:
            set_field("checkout_token_hash", hash_identifier(str(resume_token)))
        set_field("entitlement_id", _extract_attr(checkout_session, "entitlement_id"))
        set_field("user_id", _extract_attr(checkout_session, "user_id"))

    if decision is not None:
        set_field("decision_allowed", _extract_attr(decision, "allowed"))
        set_field("granted_via", _extract_attr(decision, "granted_via"))
        set_field("entitlement_id", _extract_attr(decision, "entitlement_id"))
        set_field("remaining_unlocks", _extract_attr(decision, "remaining_unlocks"))
        set_field("decision_reason", _extract_attr(decision, "reason_code"))

    payload = _attach_correlation_fields(
        payload,
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
    )
    return build_catalog_event_payload(**payload)
# END_CONTRACT: FN-CATALOG-EVENT-FIELDS


# START_CONTRACT: FN-CHECKOUT-SESSION-LOG-FIELDS
def checkout_session_log_fields(checkout_session: Any, **fields: Any) -> dict[str, Any]:
    return dict(fields)
# END_CONTRACT: FN-CHECKOUT-SESSION-LOG-FIELDS


# START_CONTRACT: FN-LOG-CATALOG-EVENT
def log_catalog_event(
    event: str,
    *,
    user: Any | None = None,
    report: Any | None = None,
    checkout_session: Any | None = None,
    entitlement: Any | None = None,
    decision: Any | None = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
    **fields: Any,
) -> None:
    structlog.get_logger().info(
        event,
        **catalog_event_fields(
            user=user,
            report=report,
            checkout_session=checkout_session,
            entitlement=entitlement,
            decision=decision,
            correlation_id=correlation_id,
            trace_id=trace_id,
            correlation_source=correlation_source,
            **fields,
        ),
    )
# END_CONTRACT: FN-LOG-CATALOG-EVENT
# END_BLOCK: TRACE_CATALOG_EVENT_LOGGING


# START_BLOCK: TRACE_JSONL_ROUTING
# START_CONTRACT: FN-JSON-DEFAULT
def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()
    return str(value)
# END_CONTRACT: FN-JSON-DEFAULT


# START_CONTRACT: FN-APPEND-EVENT
def _append_event(filename: str, event_dict: dict[str, Any]) -> None:
    log_dir = LOG_DIR
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        if not os.access(log_dir, os.W_OK):
            raise PermissionError(f"log dir is not writable: {log_dir}")
    except OSError:
        fallback_dir = Path("/tmp/astro-project/logs")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        log_dir = fallback_dir
    path = log_dir / filename
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event_dict, ensure_ascii=False, default=_json_default) + "\n")
# END_CONTRACT: FN-APPEND-EVENT


# START_CONTRACT: FN-FEED-ADMIN-SINK
def feed_admin_sink(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event = event_dict.get("event")
    if not event:
        return event_dict
    event_dict = _attach_correlation_fields(event_dict)
    try:
        for filename, event_set, prefixes in JSONL_ROUTES:
            if event_set and event in event_set:
                _append_event(filename, event_dict)
                break
            if prefixes and isinstance(event, str) and any(event.startswith(prefix) for prefix in prefixes):
                _append_event(filename, event_dict)
                break
    except Exception:  # pragma: no cover
        pass
    return event_dict
# END_CONTRACT: FN-FEED-ADMIN-SINK
# END_BLOCK: TRACE_JSONL_ROUTING


# START_BLOCK: TRACE_STRUCTLOG_CONFIG
_CONFIGURED = False


# START_CONTRACT: FN-CONFIGURE-STRUCTLOG
def configure_structlog() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    shared_processors = [
        structlog.processors.TimeStamper(fmt="iso", key="timestamp", utc=True),
        structlog.processors.add_log_level,
        merge_contextvars,
        feed_admin_sink,
    ]
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.KeyValueRenderer(key_order=["timestamp", "event"]),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True
# END_CONTRACT: FN-CONFIGURE-STRUCTLOG
# END_BLOCK: TRACE_STRUCTLOG_CONFIG
