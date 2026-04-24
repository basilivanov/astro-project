#!/usr/bin/env python3
"""Feed/Admin log watcher with flow-level alerts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

try:  # pragma: no cover - runtime import flexibility
    from tools.log_watch.common import freshness_fields
except ModuleNotFoundError:  # pragma: no cover - fallback for direct invocation
    from common import freshness_fields  # type: ignore


TIMESTAMP_KEYS = (
    "timestamp",
    "@timestamp",
    "ts",
    "time",
    "event_ts",
    "event_time",
    "logged_at",
)


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - argparse surfaces this
        raise argparse.ArgumentTypeError(f"Invalid ISO datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _coerce_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.fromtimestamp(float(candidate), tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                return None
    return None


def _extract_timestamp(record: dict[str, Any]) -> datetime | None:
    for key in TIMESTAMP_KEYS:
        if key in record:
            ts = _coerce_timestamp(record[key])
            if ts is not None:
                if ts.tzinfo is None:
                    return ts.replace(tzinfo=timezone.utc)
                return ts.astimezone(timezone.utc)
    return None


def _format_dt(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


@dataclass
class FlowConfig:
    flow_id: str
    label: str
    log_path: Path
    allowed_events: set[str]
    error_events: set[str]
    success_predicate: Callable[[dict[str, Any]], bool]


@dataclass
class FlowStatus:
    flow_id: str
    label: str
    log_path: str
    records_checked: int = 0
    latest_event: str | None = None
    latest_stage: str | None = None
    latest_timestamp: datetime | None = None
    last_success_at: datetime | None = None
    last_success_event: str | None = None
    last_error_at: datetime | None = None
    last_error_event: str | None = None
    last_error_stage: str | None = None
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
            "latest_stage": self.latest_stage,
            "latest_timestamp": _format_dt(self.latest_timestamp),
            "last_success_at": _format_dt(self.last_success_at),
            "last_success_event": self.last_success_event,
            **freshness_fields(now, self.last_success_at, window),
            "alerts": list(self.alerts),
        }
        if self.last_error_at:
            payload["last_error_at"] = _format_dt(self.last_error_at)
            payload["last_error_event"] = self.last_error_event
            payload["last_error_stage"] = self.last_error_stage
        if self.missing_log:
            payload["missing_log"] = True
        if self.unreadable_log:
            payload["unreadable_log"] = True
        return payload


def _load_records(path: Path, allowed_events: set[str], limit: int) -> list[dict[str, Any]]:
    records: deque[dict[str, Any]] = deque(maxlen=limit)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and (not allowed_events or data.get("event") in allowed_events):
                records.append(data)
    return list(records)


def _analyze_flow(config: FlowConfig, now: datetime, window: timedelta, limit: int) -> FlowStatus:
    status = FlowStatus(flow_id=config.flow_id, label=config.label, log_path=str(config.log_path))
    if not config.log_path.exists():
        status.missing_log = True
        status.alerts.append(f"{config.flow_id}: log file not found at {config.log_path}")
        return status

    try:
        records = _load_records(config.log_path, config.allowed_events, limit)
    except OSError as exc:
        status.unreadable_log = True
        status.alerts.append(f"{config.flow_id}: unable to read {config.log_path}: {exc}")
        return status

    status.records_checked = len(records)
    if not records:
        status.alerts.append(f"{config.flow_id}: no structured {config.label} events found in {config.log_path}")
        return status

    fallback_base = datetime.fromtimestamp(config.log_path.stat().st_mtime, tz=timezone.utc)
    total = len(records)
    latest_index = -1

    for index, record in enumerate(records):
        event = str(record.get("event")) if record.get("event") else None
        ts = _extract_timestamp(record)
        if ts is None:
            # Preserve ordering by offsetting from file mtime backwards per record.
            ts = fallback_base - timedelta(microseconds=(total - index))
        if (
            status.latest_timestamp is None
            or ts > status.latest_timestamp
            or (status.latest_timestamp == ts and index > latest_index)
        ):
            status.latest_timestamp = ts
            status.latest_event = event
            status.latest_stage = record.get("stage") if isinstance(record.get("stage"), str) else None
            latest_index = index
        if config.success_predicate(record):
            status.last_success_at = ts
            status.last_success_event = event
        if event in config.error_events:
            status.last_error_at = ts
            status.last_error_event = event
            status.last_error_stage = record.get("stage") if isinstance(record.get("stage"), str) else None

    if status.last_error_at is not None and (
        status.last_success_at is None or status.last_error_at > status.last_success_at
    ):
        stage = status.last_error_stage or "n/a"
        status.alerts.append(
            f"{config.flow_id}: last error {status.last_error_event} at {status.last_error_at.isoformat()} "
            f"(stage={stage}) is newer than last success"
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


def _feed_success(record: dict[str, Any]) -> bool:
    return record.get("event") == "feed.debug" and record.get("stage") == "request_success"


def _admin_success(record: dict[str, Any]) -> bool:
    if record.get("event") != "admin.entry":
        return False
    stage = record.get("stage")
    return stage in {"detail", "section_detail"}


def _build_flow_configs(args: argparse.Namespace) -> list[FlowConfig]:
    return [
        FlowConfig(
            flow_id="FLOW-DAILY-FEED",
            label="FEED",
            log_path=args.feed_log,
            allowed_events={"feed.entry", "feed.debug", "feed.error"},
            error_events={"feed.error"},
            success_predicate=_feed_success,
        ),
        FlowConfig(
            flow_id="FLOW-ADMIN-OPS",
            label="ADMIN",
            log_path=args.admin_log,
            allowed_events={
                "admin.entry",
                "admin.queue",
                "admin.section_regenerate",
                "admin.export",
                "admin.error",
                "admin.entitlement_grant",
            },
            error_events={"admin.error"},
            success_predicate=_admin_success,
        ),
    ]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch FEED and ADMIN structured logs for regressions")
    parser.add_argument("--feed-log", required=True, type=Path, help="Path to feed JSONL log file")
    parser.add_argument("--admin-log", required=True, type=Path, help="Path to admin JSONL log file")
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=30,
        help="Alert if no success events are found within this many minutes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=2000,
        help="Maximum number of recent records to consider per log",
    )
    parser.add_argument(
        "--now",
        type=_parse_datetime,
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
    configs = _build_flow_configs(args)
    statuses: list[FlowStatus] = []
    alerts: list[str] = []
    for config in configs:
        status = _analyze_flow(config, now, window, args.limit)
        statuses.append(status)
        alerts.extend(status.alerts)

    summary = {
        "generated_at": now.isoformat(),
        "window_minutes": args.window_minutes,
        "limit": args.limit,
        "flows": [status.to_dict(now, window) for status in statuses],
        "alerts": alerts,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
