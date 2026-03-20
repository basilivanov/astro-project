"""Structured logging helpers for feed/admin flows."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

