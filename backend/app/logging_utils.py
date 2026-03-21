"""Structured logging helpers for feed/admin/catalog flows."""

from __future__ import annotations

import json
import logging
import os
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = Path(os.getenv("ASTRO_LOG_DIR", PROJECT_ROOT / "logs")).resolve()
FEED_EVENTS = {"feed.entry", "feed.debug", "feed.error"}
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


def hash_identifier(value: Optional[str], *, prefix: str = "sha256", length: int = 12) -> Optional[str]:
    """Return a truncated hash for sensitive identifiers (resume tokens, etc.)."""
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


def _extract_attr(obj: Any, attr: str) -> Optional[Any]:
    if obj is None:
        return None
    return getattr(obj, attr, None)


def catalog_event_fields(
    *,
    user: Any | None = None,
    report: Any | None = None,
    checkout_session: Any | None = None,
    entitlement: Any | None = None,
    decision: Any | None = None,
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

    return build_catalog_event_payload(**payload)


def checkout_session_log_fields(checkout_session: Any, **fields: Any) -> dict[str, Any]:
    """Pre-populate catalog logging fields for checkout sessions."""
    return dict(fields)


def log_catalog_event(
    event: str,
    *,
    user: Any | None = None,
    report: Any | None = None,
    checkout_session: Any | None = None,
    entitlement: Any | None = None,
    decision: Any | None = None,
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
        if event in FEED_EVENTS:
            _append_event("feed.jsonl", event_dict)
        elif event in ADMIN_EVENTS:
            _append_event("admin.jsonl", event_dict)
        elif event in CATALOG_EVENTS:
            _append_event("catalog.jsonl", event_dict)
    except Exception:  # pragma: no cover - logging should never raise
        pass
    return event_dict


_CONFIGURED = False


def configure_structlog() -> None:
    global _CONFIGURED
    if _CONFIGURED:  # pragma: no cover - idempotent guard
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", key="timestamp", utc=True),
            structlog.processors.add_log_level,
            feed_admin_sink,
            structlog.processors.KeyValueRenderer(key_order=["timestamp", "event"]),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True
