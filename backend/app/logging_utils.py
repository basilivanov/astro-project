"""Structured logging helpers for all GRACE slices."""

from __future__ import annotations

import inspect
import json
import logging
import os
import hashlib
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, TypedDict

import structlog
from structlog.contextvars import bind_contextvars, merge_contextvars, unbind_contextvars

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = Path(os.getenv("ASTRO_LOG_DIR", PROJECT_ROOT / "logs")).resolve()

FEED_EVENTS = {
    "feed.entry",
    "feed.debug",
    "feed.error",
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

BILLING_PREFIXES = ("billing.", "catalog.checkout_", "catalog.bridge_resume_")
SCHEDULER_PREFIXES = ("scheduler.", "daily.", "notification.", "notify.")
DIAGNOSTIC_PREFIXES = ("diagnostic.", "llm.cli.")

JSONL_ROUTES: tuple[tuple[str, set[str] | None, Sequence[str] | None], ...] = (
    ("feed.jsonl", FEED_EVENTS, None),
    ("admin.jsonl", ADMIN_EVENTS, None),
    ("catalog.jsonl", CATALOG_EVENTS, None),
    ("billing.jsonl", None, BILLING_PREFIXES),
    ("scheduler.jsonl", None, SCHEDULER_PREFIXES),
    ("diagnostic.jsonl", None, DIAGNOSTIC_PREFIXES),
)


class CorrelationContext(TypedDict):
    correlation_id: Optional[str]
    trace_id: Optional[str]
    correlation_source: Optional[str]


_CORRELATION_ID_VAR: ContextVar[Optional[str]] = ContextVar("astro_correlation_id", default=None)
_TRACE_ID_VAR: ContextVar[Optional[str]] = ContextVar("astro_trace_id", default=None)
_CORRELATION_SOURCE_VAR: ContextVar[Optional[str]] = ContextVar("astro_correlation_source", default=None)
_STRUCTLOG_CORRELATION_KEYS = ("correlation_id", "trace_id", "correlation_source")


def _unbind_structlog_keys() -> None:
    for key in _STRUCTLOG_CORRELATION_KEYS:
        try:
            unbind_contextvars(key)
        except LookupError:  # pragma: no cover
            continue


def get_correlation_ids() -> CorrelationContext:
    return {
        "correlation_id": _CORRELATION_ID_VAR.get(),
        "trace_id": _TRACE_ID_VAR.get(),
        "correlation_source": _CORRELATION_SOURCE_VAR.get(),
    }


def set_correlation_ids(
    *,
    correlation_id: Optional[str],
    trace_id: Optional[str],
    correlation_source: Optional[str],
) -> CorrelationContext:
    context: CorrelationContext = {
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "correlation_source": correlation_source,
    }
    _CORRELATION_ID_VAR.set(context["correlation_id"])
    _TRACE_ID_VAR.set(context["trace_id"])
    _CORRELATION_SOURCE_VAR.set(context["correlation_source"])
    _unbind_structlog_keys()
    bind_values = {key: value for key, value in context.items() if value is not None}
    if bind_values:
        bind_contextvars(**bind_values)
    return context


def resolve_correlation_context(
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> CorrelationContext:
    current = get_correlation_ids()
    return {
        "correlation_id": correlation_id or current["correlation_id"],
        "trace_id": trace_id or current["trace_id"],
        "correlation_source": correlation_source or current["correlation_source"],
    }


def _attach_correlation_fields(
    payload: dict[str, Any],
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> dict[str, Any]:
    context = resolve_correlation_context(
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
    )
    for key, value in context.items():
        if value is not None and key not in payload:
            payload[key] = value
    return payload


@contextmanager
def with_correlation_context(
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
) -> Iterator[CorrelationContext]:
    previous = get_correlation_ids()
    next_context = resolve_correlation_context(
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=correlation_source,
    )
    set_correlation_ids(**next_context)
    try:
        yield next_context
    finally:
        set_correlation_ids(**previous)


def bind_correlation_ids(
    source: str,
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> CorrelationContext:
    correlation_id = correlation_id or str(uuid.uuid4())
    trace_id = trace_id or str(uuid.uuid4())
    return set_correlation_ids(
        correlation_id=correlation_id,
        trace_id=trace_id,
        correlation_source=source,
    )


@contextmanager
def correlation_scope(
    source: str,
    *,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Iterator[CorrelationContext]:
    previous = get_correlation_ids()
    context = bind_correlation_ids(source, correlation_id=correlation_id, trace_id=trace_id)
    try:
        yield context
    finally:
        set_correlation_ids(
            correlation_id=previous["correlation_id"],
            trace_id=previous["trace_id"],
            correlation_source=previous["correlation_source"],
        )


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


@contextmanager
def _async_correlation_context(context: CorrelationContext):
    with with_correlation_context(
        correlation_id=context.get("correlation_id"),
        trace_id=context.get("trace_id"),
        correlation_source=context.get("correlation_source"),
    ):
        yield


def hash_identifier(value: Optional[str], *, prefix: str = "sha256", length: int = 12) -> Optional[str]:
    if not value:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:length]}"


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


def build_catalog_event_payload(**fields: Any) -> dict[str, Any]:
    return {
        key: _normalize_log_value(value)
        for key, value in fields.items()
        if value is not None
    }


def build_grace_log_payload(
    *,
    module: str,
    fn: str,
    block: str,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    correlation_source: Optional[str] = None,
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
    )
    return build_catalog_event_payload(**payload)


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
            **fields,
        ),
    )


def _extract_attr(obj: Any, attr: str) -> Optional[Any]:
    return getattr(obj, attr, None) if obj is not None else None


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


def checkout_session_log_fields(checkout_session: Any, **fields: Any) -> dict[str, Any]:
    return dict(fields)


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


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _append_event(filename: str, event_dict: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / filename
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event_dict, ensure_ascii=False, default=_json_default) + "\n")


def feed_admin_sink(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event = event_dict.get("event")
    if not event:
        return event_dict
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


_CONFIGURED = False


def configure_structlog() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", key="timestamp", utc=True),
            structlog.processors.add_log_level,
            merge_contextvars,
            feed_admin_sink,
            structlog.processors.KeyValueRenderer(key_order=["timestamp", "event"]),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True
