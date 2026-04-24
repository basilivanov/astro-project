#!/usr/bin/env python3
"""FLOW-FORECAST-CATALOG log watcher."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

try:  # pragma: no cover - runtime import flexibility
    from tools.log_watch.common import extract_timestamp, format_dt, freshness_fields, load_records, parse_datetime_arg
except ModuleNotFoundError:  # pragma: no cover - fallback for direct invocation
    from common import extract_timestamp, format_dt, freshness_fields, load_records, parse_datetime_arg  # type: ignore

CATALOG_ALLOWED_EVENTS: set[str] = {
    "catalog.history_start",
    "catalog.history_success",
    "catalog.checkout_start",
    "catalog.checkout_decision",
    "catalog.checkout_denied",
    "catalog.checkout_success",
    "catalog.checkout_payment_created",
    "catalog.checkout_status",
    "catalog.checkout_resume_ready",
    "catalog.bridge_resume_start",
    "catalog.bridge_resume_success",
    "catalog.error",
}

SUCCESS_EVENTS: set[str] = {
    "catalog.history_success",
    "catalog.checkout_success",
    "catalog.checkout_resume_ready",
    "catalog.bridge_resume_success",
}

ERROR_EVENTS: set[str] = {
    "catalog.error",
}


def _success_predicate(record: dict[str, Any]) -> bool:
    event = record.get("event")
    return isinstance(event, str) and event in SUCCESS_EVENTS


def _is_error_event(record: dict[str, Any]) -> bool:
    event = record.get("event")
    if not isinstance(event, str):
        return False
    return event in ERROR_EVENTS


def _record_surface(record: dict[str, Any]) -> str | None:
    surface = record.get("surface")
    if isinstance(surface, str):
        return surface
    event = record.get("event")
    if not isinstance(event, str):
        return None
    if "history" in event:
        return "history"
    if "checkout" in event:
        return "checkout"
    if "bridge" in event:
        return "bridge"
    return None


def _success_context(record: dict[str, Any]) -> dict[str, Any]:
    keys = ["user_id", "report_id", "checkout_session_id", "surface", "decision_allowed", "status"]
    return {key: record[key] for key in keys if key in record}


def _error_context(record: dict[str, Any]) -> dict[str, Any]:
    keys = ["user_id", "report_id", "checkout_session_id", "surface", "status", "error", "reason"]
    return {key: record[key] for key in keys if key in record}


@dataclass
class FlowConfig:
    flow_id: str
    label: str
    log_path: Path
    allowed_events: set[str]
    success_predicate: Callable[[dict[str, Any]], bool]


@dataclass
class FlowStatus:
    flow_id: str
    label: str
    log_path: str
    records_checked: int = 0
    latest_event: str | None = None
    latest_surface: str | None = None
    latest_status: str | None = None
    latest_timestamp: datetime | None = None
    last_success_at: datetime | None = None
    last_success_event: str | None = None
    success_context: dict[str, Any] | None = None
    last_error_at: datetime | None = None
    last_error_event: str | None = None
    last_error_surface: str | None = None
    last_error_context: dict[str, Any] | None = None
    alerts: list[str] = field(default_factory=list)
    missing_log: bool = False
    unreadable_log: bool = False

    def to_dict(self, now: datetime, window: timedelta) -> dict[str, Any]:
        payload = {
            "flow_id": self.flow_id,
            "label": self.label,
            "log_path": self.log_path,
            "records_checked": self.records_checked,
            "latest_event": self.latest_event,
            "latest_surface": self.latest_surface,
            "latest_status": self.latest_status,
            "latest_timestamp": format_dt(self.latest_timestamp),
            "last_success_at": format_dt(self.last_success_at),
            "last_success_event": self.last_success_event,
            **freshness_fields(now, self.last_success_at, window),
            "alerts": list(self.alerts),
        }
        if self.success_context:
            payload["success_context"] = self.success_context
        if self.last_error_at:
            payload["last_error_at"] = format_dt(self.last_error_at)
            payload["last_error_event"] = self.last_error_event
            payload["last_error_surface"] = self.last_error_surface
            if self.last_error_context:
                payload["last_error_context"] = self.last_error_context
        if self.missing_log:
            payload["missing_log"] = True
        if self.unreadable_log:
            payload["unreadable_log"] = True
        return payload


def _summarize_context(context: dict[str, Any] | None) -> str:
    if not context:
        return "n/a"
    parts = []
    for key in ("user_id", "report_id", "checkout_session_id", "surface", "status", "error", "reason"):
        if key in context:
            parts.append(f"{key}={context[key]}")
    return ", ".join(parts) if parts else "n/a"


def _analyze_flow(config: FlowConfig, now: datetime, window: timedelta, limit: int) -> FlowStatus:
    status = FlowStatus(flow_id=config.flow_id, label=config.label, log_path=str(config.log_path))
    if not config.log_path.exists():
        status.missing_log = True
        status.alerts.append(f"{config.flow_id}: log file not found at {config.log_path}")
        return status
    try:
        records = load_records(config.log_path, config.allowed_events, limit)
    except OSError as exc:
        status.unreadable_log = True
        status.alerts.append(f"{config.flow_id}: unable to read {config.log_path}: {exc}")
        return status

    status.records_checked = len(records)
    if not records:
        status.alerts.append(f"{config.flow_id}: no catalog events found in {config.log_path}")
        return status

    fallback_base = datetime.fromtimestamp(config.log_path.stat().st_mtime, tz=timezone.utc)
    total = len(records)
    latest_index = -1
    for index, record in enumerate(records):
        event = record.get("event") if isinstance(record.get("event"), str) else None
        ts = extract_timestamp(record)
        if ts is None:
            ts = fallback_base - timedelta(microseconds=(total - index))
        if (
            status.latest_timestamp is None
            or ts > status.latest_timestamp
            or (status.latest_timestamp == ts and index > latest_index)
        ):
            status.latest_timestamp = ts
            status.latest_event = event
            status.latest_surface = _record_surface(record)
            status.latest_status = record.get("status") if isinstance(record.get("status"), str) else None
            latest_index = index

        if config.success_predicate(record):
            status.last_success_at = ts
            status.last_success_event = event
            status.success_context = _success_context(record)
        if _is_error_event(record):
            status.last_error_at = ts
            status.last_error_event = event
            status.last_error_surface = _record_surface(record)
            status.last_error_context = _error_context(record)

    if status.last_error_at is not None and (
        status.last_success_at is None or status.last_error_at > status.last_success_at
    ):
        status.alerts.append(
            f"{config.flow_id}: last error {status.last_error_event} at {status.last_error_at.isoformat()} "
            f"(surface={status.last_error_surface or 'n/a'}) details: {_summarize_context(status.last_error_context)}"
        )

    if status.last_success_at is None:
        status.alerts.append(
            f"{config.flow_id}: no success events detected within the last {status.records_checked} records"
        )
    elif now - status.last_success_at > window:
        status.alerts.append(
            f"{config.flow_id}: last success at {status.last_success_at.isoformat()} is older than {int(window.total_seconds() / 60)} minutes"
        )

    return status


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch catalog logs for FLOW-FORECAST-CATALOG regressions")
    parser.add_argument("--catalog-log", required=True, type=Path, help="Path to catalog JSONL log file")
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=30,
        help="Alert if no success events occur within this many minutes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=2000,
        help="Maximum number of records to scan",
    )
    parser.add_argument(
        "--now",
        type=parse_datetime_arg,
        default=None,
        help="Override current time (UTC ISO) for testing",
    )
    args = parser.parse_args(argv)
    if args.window_minutes <= 0:
        parser.error("--window-minutes must be > 0")
    if args.limit <= 0:
        parser.error("--limit must be > 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    now = args.now or datetime.now(timezone.utc)
    window = timedelta(minutes=args.window_minutes)
    config = FlowConfig(
        flow_id="FLOW-FORECAST-CATALOG",
        label="CATALOG",
        log_path=args.catalog_log,
        allowed_events=CATALOG_ALLOWED_EVENTS,
        success_predicate=_success_predicate,
    )
    status = _analyze_flow(config, now, window, args.limit)
    summary = {
        "generated_at": now.isoformat(),
        "window_minutes": args.window_minutes,
        "limit": args.limit,
        "flows": [status.to_dict(now, window)],
        "alerts": list(status.alerts),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if status.alerts else 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
