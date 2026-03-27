#!/usr/bin/env python3
"""Diagnostic & LLM health watcher."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

try:  # pragma: no cover - runtime import flexibility
    from tools.log_watch.common import (
        compute_percentiles,
        emit_output,
        ensure_positive,
        exit_code_from_status,
        extract_timestamp,
        load_records,
        parse_datetime_arg,
    )
except ModuleNotFoundError:  # pragma: no cover
    from common import (  # type: ignore
        compute_percentiles,
        emit_output,
        ensure_positive,
        exit_code_from_status,
        extract_timestamp,
        load_records,
        parse_datetime_arg,
    )

FLOW_ID = "FLOW-DIAGNOSTIC"
FLOW_LABEL = "Diagnostics & LLM"
DEFAULT_LOG = Path("logs/diagnostic.jsonl")
DIAGNOSTIC_PREFIXES = ("diagnostic.", "llm.cli.")
SUCCESS_EVENTS = {"diagnostic.report", "diagnostic.llm", "diagnostic.natal"}
ERROR_SUFFIX = ".error"
WARNING_EVENTS = {"diagnostic.engine.warning", "diagnostic.llm.slow"}
DEFAULT_SLO_MS = 60000
HARD_LIMIT_MS = 120000


@dataclass
class DiagnosticWindow:
    records: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    alerts: list[str] = field(default_factory=list)
    latest_event: dict[str, Any] | None = None
    last_success: dict[str, Any] | None = None
    last_error: dict[str, Any] | None = None
    recent_latencies: list[float] = field(default_factory=list)

    def add_alert(self, message: str, severity: str) -> None:
        self.alerts.append(message)
        order = ("ok", "warning", "critical", "error")
        if order.index(severity) > order.index(self.status):
            self.status = severity


def _summarize_record(record: dict[str, Any], ts: datetime | None) -> dict[str, Any]:
    keys = ("event", "diagnostic_id", "block", "surface", "correlation_id", "trace_id")
    payload = {key: record.get(key) for key in keys if record.get(key) is not None}
    payload["timestamp"] = ts.astimezone(timezone.utc).isoformat() if ts else None
    return payload


def _analyze(records: list[dict[str, Any]], now: datetime, window: timedelta) -> DiagnosticWindow:
    window_state = DiagnosticWindow(records=records)
    if not records:
        window_state.add_alert(f"{FLOW_ID}: no diagnostic events in window", "warning")
        return window_state

    for record in records:
        ts = extract_timestamp(record) or datetime.fromtimestamp(record.get("_meta_ts", now.timestamp()), tz=timezone.utc)
        event = record.get("event")
        latency = record.get("latency_ms")
        if isinstance(latency, (int, float)):
            window_state.recent_latencies.append(float(latency))
        if event and isinstance(event, str):
            if window_state.latest_event is None or (ts and ts > datetime.fromisoformat(window_state.latest_event["timestamp"])):
                window_state.latest_event = _summarize_record(record, ts)
            if event in SUCCESS_EVENTS:
                window_state.last_success = _summarize_record(record, ts)
            elif event.endswith(ERROR_SUFFIX):
                window_state.last_error = _summarize_record(record, ts)
            elif event in WARNING_EVENTS:
                window_state.add_alert(f"{FLOW_ID}: warning event {event}", "warning")

    if window_state.last_error and (
        not window_state.last_success
        or window_state.last_error.get("timestamp") >= window_state.last_success.get("timestamp")
    ):
        window_state.add_alert(f"{FLOW_ID}: latest error event {window_state.last_error.get('event')} detected", "critical")

    if window_state.last_success is None:
        window_state.add_alert(f"{FLOW_ID}: no diagnostic success events found", "critical")
    else:
        last_success_dt = datetime.fromisoformat(window_state.last_success["timestamp"]) if window_state.last_success.get("timestamp") else None
        if last_success_dt and now - last_success_dt > window:
            window_state.add_alert(f"{FLOW_ID}: last success older than window", "warning")

    percentiles = compute_percentiles(window_state.recent_latencies)
    if percentiles:
        p95 = percentiles.get("p95")
        if p95 and p95 > HARD_LIMIT_MS:
            window_state.add_alert(f"{FLOW_ID}: p95 latency {p95}ms exceeds hard limit {HARD_LIMIT_MS}ms", "critical")
        elif p95 and p95 > DEFAULT_SLO_MS:
            window_state.add_alert(f"{FLOW_ID}: p95 latency {p95}ms exceeds SLO {DEFAULT_SLO_MS}ms", "warning")

    return window_state


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch diagnostic JSONL logs for regressions")
    parser.add_argument("--diagnostic-log", type=Path, default=DEFAULT_LOG, help="Path to diagnostic JSONL log")
    parser.add_argument("--window-minutes", type=int, default=30, help="Sliding window size in minutes")
    parser.add_argument("--limit", type=int, default=2000, help="Maximum records to inspect")
    parser.add_argument("--surface", action="append", dest="surfaces", default=[], help="Optional surface filters (repeatable)")
    parser.add_argument("--json", action="store_true", help="Emit JSON payloads")
    parser.add_argument("--output", type=str, default=None, help="Optional file to append JSON payloads to (use '-' for stdout)")
    parser.add_argument("--now", type=parse_datetime_arg, default=None, help="Override current UTC time")
    args = parser.parse_args(argv)
    args.window_minutes = ensure_positive(args.window_minutes, name="--window-minutes", parser=parser)
    args.limit = ensure_positive(args.limit, name="--limit", parser=parser)
    return args


def _filter_records(records: list[dict[str, Any]], surfaces: List[str]) -> list[dict[str, Any]]:
    if not surfaces:
        return records
    normalized = {surface.lower() for surface in surfaces}
    filtered = []
    for record in records:
        surface = record.get("surface")
        if isinstance(surface, str) and surface.lower() in normalized:
            filtered.append(record)
    return filtered


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    now = args.now or datetime.now(timezone.utc)
    window = timedelta(minutes=args.window_minutes)

    if not args.diagnostic_log.exists():
        payload = {
            "flow_id": FLOW_ID,
            "label": FLOW_LABEL,
            "status": "error",
            "generated_at": now.isoformat(),
            "alerts": [f"{FLOW_ID}: log file not found at {args.diagnostic_log}"],
            "block": FLOW_ID,
            "flows": [
                {
                    "flow_id": FLOW_ID,
                    "label": FLOW_LABEL,
                    "status": "error",
                    "log_path": str(args.diagnostic_log),
                    "alerts": ["log missing"],
                    "block": FLOW_ID,
                }
            ],
        }
        emit_output(payload, json_mode=args.json, output_path=args.output)
        return exit_code_from_status("error")

    try:
        records = load_records(args.diagnostic_log, allowed_events=None, limit=args.limit, allowed_prefixes=DIAGNOSTIC_PREFIXES)
    except OSError as exc:
        payload = {
            "flow_id": FLOW_ID,
            "label": FLOW_LABEL,
            "status": "error",
            "generated_at": now.isoformat(),
            "alerts": [f"{FLOW_ID}: unable to read log: {exc}"],
            "block": FLOW_ID,
        }
        emit_output(payload, json_mode=args.json, output_path=args.output)
        return exit_code_from_status("error")

    for record in records:
        ts = extract_timestamp(record)
        if ts is None:
            record["_meta_ts"] = now.timestamp()
    filtered = _filter_records(records, args.surfaces)
    status = _analyze(filtered, now, window)

    payload = {
        "flow_id": FLOW_ID,
        "label": FLOW_LABEL,
        "status": status.status,
        "generated_at": now.isoformat(),
        "window_minutes": args.window_minutes,
        "limit": args.limit,
        "alerts": status.alerts,
        "block": FLOW_ID,
        "flows": [
            {
                "flow_id": FLOW_ID,
                "label": FLOW_LABEL,
                "status": status.status,
                "log_path": str(args.diagnostic_log),
                "window_minutes": args.window_minutes,
                "latest_event": status.latest_event,
                "last_success": status.last_success,
                "last_error": status.last_error,
                "latency_percentiles": compute_percentiles(status.recent_latencies),
                "alerts": status.alerts,
                "block": FLOW_ID,
            }
        ],
    }
    emit_output(payload, json_mode=args.json, output_path=args.output)
    return exit_code_from_status(status.status)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    import sys

    raise SystemExit(main(sys.argv[1:]))
