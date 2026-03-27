#!/usr/bin/env python3
"""Billing & credits watcher."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:  # pragma: no cover - runtime import flexibility
    from tools.log_watch.common import (
        exit_code_from_status,
        extract_timestamp,
        fallback_timestamp,
        format_dt,
        load_records,
        parse_datetime_arg,
        emit_output,
    )
except ModuleNotFoundError:  # pragma: no cover
    from common import (  # type: ignore
        exit_code_from_status,
        extract_timestamp,
        fallback_timestamp,
        format_dt,
        load_records,
        parse_datetime_arg,
        emit_output,
    )


FLOW_ID = "FLOW-BILLING"
FLOW_LABEL = "Billing & Credits"
DEFAULT_LOG_PATH = Path("logs/billing.jsonl")
BILLING_PREFIXES = ("billing.", "catalog.checkout_", "catalog.bridge_resume_")
SUCCESS_EVENTS = {"billing.success"}
ERROR_EVENTS = {
    "billing.create_failed",
    "billing.webhook_unhandled_event",
    "billing.webhook_bad_checkout_session_uuid",
    "billing.webhook_bad_user_uuid",
    "billing.webhook_bad_uuid",
    "billing.webhook_no_user",
    "billing.webhook_user_not_found",
}
WARNING_EVENTS = {
    "billing.config_missing",
    "billing.report_unlock_missing_report_type",
}


@dataclass
class BillingStatus:
    latest_event: dict[str, Any] | None = None
    last_success_event: dict[str, Any] | None = None
    last_error_event: dict[str, Any] | None = None
    alerts: list[str] = None  # type: ignore[assignment]
    status: str = "ok"

    def __post_init__(self) -> None:
        if self.alerts is None:
            self.alerts = []


def _record_context(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "event",
        "stage",
        "surface",
        "status",
        "user_id",
        "report_id",
        "checkout_session_id",
        "correlation_id",
        "trace_id",
    )
    return {key: record.get(key) for key in keys if record.get(key) is not None}


def _analyze_records(
    records: list[dict[str, Any]],
    *,
    now: datetime,
    window: timedelta,
) -> BillingStatus:
    status = BillingStatus()
    total = len(records)
    if total == 0:
        status.alerts.append("FLOW-BILLING: no billing events found inside log window")
        status.status = "warning"
        return status

    latest_ts: datetime | None = None
    latest_index = -1
    for index, record in enumerate(records):
        event = record.get("event")
        ts = extract_timestamp(record)
        if ts is None:
            ts = fallback_timestamp(Path(record.get("__log_path__", DEFAULT_LOG_PATH)), index, total)
        if (
            latest_ts is None
            or ts > latest_ts
            or (latest_ts == ts and index > latest_index)
        ):
            latest_ts = ts
            latest_index = index
            status.latest_event = {
                "event": event,
                "timestamp": format_dt(ts),
                **_record_context(record),
            }

        if isinstance(event, str):
            if event in SUCCESS_EVENTS:
                status.last_success_event = {
                    "event": event,
                    "timestamp": format_dt(ts),
                    **_record_context(record),
                }
            elif event in ERROR_EVENTS or event.endswith(".error"):
                status.last_error_event = {
                    "event": event,
                    "timestamp": format_dt(ts),
                    **_record_context(record),
                }
            elif event in WARNING_EVENTS:
                status.alerts.append(f"FLOW-BILLING: warning event {event}")

    if status.last_error_event and (
        not status.last_success_event
        or status.last_error_event["timestamp"] >= status.last_success_event["timestamp"]
    ):
        status.alerts.append(
            "FLOW-BILLING: latest billing events include errors — investigate webhook/checkout pipeline"
        )
        status.status = "critical"

    if status.last_success_event is None:
        status.alerts.append("FLOW-BILLING: no billing.success events detected yet")
        status.status = "critical"
    else:
        last_success_at = datetime.fromisoformat(status.last_success_event["timestamp"])
        if now - last_success_at > window and status.status != "critical":
            status.alerts.append(
                f"FLOW-BILLING: last billing.success at {status.last_success_event['timestamp']} is older than {int(window.total_seconds() / 60)} minutes"
            )
            status.status = "warning"

    if status.latest_event and isinstance(status.latest_event.get("event"), str):
        event_name = status.latest_event["event"]
        if event_name in ERROR_EVENTS or event_name.endswith(".error"):
            status.alerts.append("FLOW-BILLING: most recent event is an error")
            status.status = "critical"

    return status


def _load_records(path: Path, limit: int) -> list[dict[str, Any]]:
    records = load_records(path, allowed_events=None, limit=limit, allowed_prefixes=BILLING_PREFIXES)
    for record in records:
        record["__log_path__"] = str(path)
    return records


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch billing and checkout JSONL logs for regressions")
    parser.add_argument("--billing-log", type=Path, default=DEFAULT_LOG_PATH, help="Path to billing JSONL log")
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=20,
        help="Alert if no billing.success events within this many minutes",
    )
    parser.add_argument("--limit", type=int, default=4000, help="Maximum records to scan")
    parser.add_argument("--now", type=parse_datetime_arg, default=None, help="Override current UTC ISO time")
    parser.add_argument("--json", action="store_true", help="Emit newline-delimited JSON even when writing to stdout")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional file to append JSON payloads to (use '-' for stdout)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    now = args.now or datetime.now(timezone.utc)
    window = timedelta(minutes=args.window_minutes)

    if not args.billing_log.exists():
        payload = {
            "flow_id": FLOW_ID,
            "label": FLOW_LABEL,
            "status": "error",
            "generated_at": now.isoformat(),
            "alerts": [f"{FLOW_ID}: log file not found at {args.billing_log}"],
            "block": FLOW_ID,
            "flows": [
                {
                    "flow_id": FLOW_ID,
                    "label": FLOW_LABEL,
                    "status": "error",
                    "alerts": [f"log missing: {args.billing_log}"],
                    "block": FLOW_ID,
                }
            ],
        }
        emit_output(payload, json_mode=args.json, output_path=args.output)
        return exit_code_from_status("error")

    try:
        records = _load_records(args.billing_log, args.limit)
    except OSError as exc:  # pragma: no cover - filesystem errors
        payload = {
            "flow_id": FLOW_ID,
            "label": FLOW_LABEL,
            "status": "error",
            "generated_at": now.isoformat(),
            "alerts": [f"{FLOW_ID}: unable to read {args.billing_log}: {exc}"],
            "block": FLOW_ID,
            "flows": [
                {
                    "flow_id": FLOW_ID,
                    "label": FLOW_LABEL,
                    "status": "error",
                    "alerts": [str(exc)],
                    "block": FLOW_ID,
                }
            ],
        }
        emit_output(payload, json_mode=args.json, output_path=args.output)
        return exit_code_from_status("error")

    status = _analyze_records(records, now=now, window=window)
    minutes_since_success = None
    if status.last_success_event and status.last_success_event.get("timestamp"):
        last_success_dt = datetime.fromisoformat(status.last_success_event["timestamp"])
        minutes_since_success = round((now - last_success_dt).total_seconds() / 60, 2)

    flow_entry = {
        "flow_id": FLOW_ID,
        "label": FLOW_LABEL,
        "status": status.status,
        "log_path": str(args.billing_log),
        "window_minutes": args.window_minutes,
        "latest_event": status.latest_event,
        "last_success": status.last_success_event,
        "last_error": status.last_error_event,
        "minutes_since_success": minutes_since_success,
        "alerts": status.alerts,
        "block": FLOW_ID,
    }

    payload = {
        "flow_id": FLOW_ID,
        "label": FLOW_LABEL,
        "status": status.status,
        "generated_at": now.isoformat(),
        "window_minutes": args.window_minutes,
        "limit": args.limit,
        "alerts": status.alerts,
        "block": FLOW_ID,
        "flows": [flow_entry],
    }

    emit_output(payload, json_mode=args.json, output_path=args.output)
    return exit_code_from_status(status.status)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main(sys.argv[1:]))
