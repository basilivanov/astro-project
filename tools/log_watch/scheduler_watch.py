#!/usr/bin/env python3
"""Scheduler log watcher for cron-style jobs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:  # pragma: no cover - runtime flexibility for PYTHONPATH
    from tools.log_watch.common import (
        emit_output,
        exit_code_from_status,
        extract_timestamp,
        fallback_timestamp,
        format_dt,
        load_records,
        parse_datetime_arg,
        summarize_landmarks,
    )
except ModuleNotFoundError:  # pragma: no cover - direct invocation fallback
    from common import (  # type: ignore
        emit_output,
        exit_code_from_status,
        extract_timestamp,
        fallback_timestamp,
        format_dt,
        load_records,
        parse_datetime_arg,
        summarize_landmarks,
    )

FLOW_SET_ID = "FLOW-SCHEDULER"
FLOW_LABEL = "Scheduler & Notifications"

JOB_EVENTS = {
    "scheduler.job_start",
    "scheduler.job_success",
    "scheduler.job_error",
    "scheduler.start",
    "scheduler.birthday_check.start",
    "scheduler.birthday_notify",
    "scheduler.birthday_check.error",
    "scheduler.sub_check.start",
    "scheduler.sub_expired",
    "scheduler.sub_check.error",
}
RESERVED_FIELDS = {
    "event",
    "timestamp",
    "@timestamp",
    "level",
    "job_name",
    "job_run_id",
    "duration_ms",
    "module",
    "fn",
    "block",
    "correlation_id",
    "trace_id",
    "request_id",
}
STATUS_ORDER = ("ok", "warning", "critical", "error", "invalid")


def _worse(current: str, candidate: str) -> str:
    if STATUS_ORDER.index(candidate) > STATUS_ORDER.index(current):
        return candidate
    return current


def _extract_metrics(record: dict[str, Any]) -> dict[str, Any] | None:
    metrics = {
        key: value
        for key, value in record.items()
        if key not in RESERVED_FIELDS and not key.startswith("_")
    }
    return metrics or None


@dataclass
class JobStatus:
    job_name: str
    log_path: str
    records_checked: int = 0
    latest_event: str | None = None
    latest_timestamp: datetime | None = None
    latest_run_id: str | None = None
    last_success_at: datetime | None = None
    last_success_run_id: str | None = None
    last_success_duration_ms: int | None = None
    last_success_metrics: dict[str, Any] | None = None
    last_error_at: datetime | None = None
    last_error_run_id: str | None = None
    last_error_message: str | None = None
    last_error_metrics: dict[str, Any] | None = None
    landmarks: list[dict[str, Any]] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    status: str = "ok"
    missing_log: bool = False

    def add_alert(self, message: str, severity: str) -> None:
        self.alerts.append(message)
        self.status = _worse(self.status, severity)

    def record_latest(self, event: str | None, ts: datetime, run_id: str | None) -> None:
        if self.latest_timestamp is None or ts >= self.latest_timestamp:
            self.latest_timestamp = ts
            self.latest_event = event
            self.latest_run_id = run_id

    def record_success(self, record: dict[str, Any], ts: datetime) -> None:
        self.last_success_at = ts
        self.last_success_run_id = record.get("job_run_id")
        duration = record.get("duration_ms")
        if isinstance(duration, (int, float)):
            self.last_success_duration_ms = int(duration)
        elif isinstance(duration, str):
            try:
                self.last_success_duration_ms = int(float(duration))
            except ValueError:
                self.last_success_duration_ms = None
        self.last_success_metrics = _extract_metrics(record)

    def record_error(self, record: dict[str, Any], ts: datetime) -> None:
        self.last_error_at = ts
        self.last_error_run_id = record.get("job_run_id")
        error_message = record.get("error")
        if isinstance(error_message, str):
            self.last_error_message = error_message
        self.last_error_metrics = _extract_metrics(record)

    def finalize(self, now: datetime, window: timedelta) -> None:
        if self.missing_log:
            self.add_alert(f"{self.job_name}: log file missing at {self.log_path}", "error")
            return
        if self.records_checked == 0:
            self.add_alert(
                f"{self.job_name}: no scheduler events found in {self.log_path}",
                "warning",
            )
            return
        if self.last_error_at and (
            self.last_success_at is None or self.last_error_at >= self.last_success_at
        ):
            when = format_dt(self.last_error_at)
            self.add_alert(
                f"{self.job_name}: latest job error at {when or 'n/a'}",
                "critical",
            )
        if self.last_success_at is None:
            self.add_alert(f"{self.job_name}: no successful runs recorded", "warning")
        else:
            if now - self.last_success_at > window:
                self.add_alert(
                    f"{self.job_name}: last success at {self.last_success_at.isoformat()} exceeds {int(window.total_seconds() / 60)}m window",
                    "warning",
                )

    def _latest_payload(self) -> dict[str, Any] | None:
        if self.latest_timestamp is None and self.latest_event is None:
            return None
        return {
            "event": self.latest_event,
            "timestamp": format_dt(self.latest_timestamp),
            "job_run_id": self.latest_run_id,
        }

    def _success_payload(self) -> dict[str, Any] | None:
        if self.last_success_at is None:
            return None
        payload: dict[str, Any] = {
            "timestamp": format_dt(self.last_success_at),
            "job_run_id": self.last_success_run_id,
        }
        if self.last_success_duration_ms is not None:
            payload["duration_ms"] = self.last_success_duration_ms
        if self.last_success_metrics:
            payload["metrics"] = self.last_success_metrics
        return payload

    def _error_payload(self) -> dict[str, Any] | None:
        if self.last_error_at is None:
            return None
        payload: dict[str, Any] = {
            "timestamp": format_dt(self.last_error_at),
            "job_run_id": self.last_error_run_id,
            "message": self.last_error_message,
        }
        if self.last_error_metrics:
            payload["metrics"] = self.last_error_metrics
        return payload

    def minutes_since_success(self, now: datetime) -> float | None:
        if self.last_success_at is None:
            return None
        return round((now - self.last_success_at).total_seconds() / 60, 2)

    def minutes_since_error(self, now: datetime) -> float | None:
        if self.last_error_at is None:
            return None
        return round((now - self.last_error_at).total_seconds() / 60, 2)

    def to_dict(self, now: datetime) -> dict[str, Any]:
        payload = {
            "job_name": self.job_name,
            "log_path": self.log_path,
            "records_checked": self.records_checked,
            "latest_event": self.latest_event,
            "latest_run_id": self.latest_run_id,
            "latest_timestamp": format_dt(self.latest_timestamp),
            "last_success_at": format_dt(self.last_success_at),
            "last_success_run_id": self.last_success_run_id,
            "last_success_duration_ms": self.last_success_duration_ms,
            "last_error_at": format_dt(self.last_error_at),
            "last_error_run_id": self.last_error_run_id,
            "last_error_message": self.last_error_message,
            "alerts": list(self.alerts),
            "status": self.status,
            "minutes_since_success": self.minutes_since_success(now),
            "landmarks": self.landmarks,
        }
        error_minutes = self.minutes_since_error(now)
        if error_minutes is not None:
            payload["minutes_since_error"] = error_minutes
        if self.last_success_metrics:
            payload["success_metrics"] = self.last_success_metrics
        if self.last_error_metrics:
            payload["error_metrics"] = self.last_error_metrics
        return payload

    def to_flow_entry(self, now: datetime, window_minutes: int) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "flow_id": self.job_name,
            "label": self.job_name.replace("FLOW-", "").replace("_", " ") or self.job_name,
            "status": self.status,
            "log_path": self.log_path,
            "window_minutes": window_minutes,
            "block": self.job_name,
            "landmarks": self.landmarks,
            "alerts": list(self.alerts),
            "latest_event": self._latest_payload(),
            "last_success": self._success_payload(),
            "last_error": self._error_payload(),
            "minutes_since_success": self.minutes_since_success(now),
        }
        error_minutes = self.minutes_since_error(now)
        if error_minutes is not None:
            entry["minutes_since_error"] = error_minutes
        return entry


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch scheduler JSONL logs for cron jobs")
    parser.add_argument("--scheduler-log", required=True, type=Path, help="Path to scheduler JSONL log file")
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=60,
        help="Alert if no success events occur within this many minutes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=4000,
        help="Maximum number of records to scan",
    )
    parser.add_argument(
        "--job",
        action="append",
        dest="jobs",
        required=True,
        help="Job/flow identifier to monitor (repeatable)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit compact JSON output",
    )
    parser.add_argument(
        "--output",
        dest="output",
        default=None,
        help="Path to append JSON output (use '-' for stdout)",
    )
    parser.add_argument(
        "--json-output",
        dest="output",
        help="Alias for --output to match gracectl docs",
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
    normalized_jobs = []
    for job in args.jobs:
        job_name = str(job).strip()
        if not job_name:
            parser.error("--job values must be non-empty")
        normalized_jobs.append(job_name)
    args.jobs = normalized_jobs
    return args


def _missing_log_statuses(jobs: list[str], log_path: Path) -> list[JobStatus]:
    statuses: list[JobStatus] = []
    for job in jobs:
        status = JobStatus(job_name=job, log_path=str(log_path), missing_log=True)
        status.add_alert(f"{job}: log file not found at {log_path}", "error")
        statuses.append(status)
    return statuses


def _analyze_records(
    *,
    path: Path,
    records: list[dict[str, Any]],
    jobs: list[str],
    now: datetime,
    window: timedelta,
) -> list[JobStatus]:
    statuses = {job: JobStatus(job_name=job, log_path=str(path)) for job in jobs}
    total = len(records)
    fallback_base = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    for index, record in enumerate(records):
        event = record.get("event")
        job_name = record.get("job_name")
        if not isinstance(job_name, str) or job_name not in statuses:
            continue
        status = statuses[job_name]
        status.records_checked += 1
        ts = extract_timestamp(record)
        if ts is None:
            ts = fallback_timestamp(path, index, total)
        status.record_latest(event if isinstance(event, str) else None, ts, record.get("job_run_id"))
        status.landmarks = summarize_landmarks([*status.landmarks, record], limit=5)
        if event == "scheduler.job_success":
            status.record_success(record, ts)
        elif event in {"scheduler.job_error", "scheduler.birthday_check.error", "scheduler.sub_check.error"}:
            status.record_error(record, ts)
        elif event in {"scheduler.sub_expired", "scheduler.birthday_notify"}:
            status.record_success(record, ts)
    for status in statuses.values():
        status.finalize(now, window)
    return list(statuses.values())


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    now = args.now or datetime.now(timezone.utc)
    window = timedelta(minutes=args.window_minutes)

    if not args.scheduler_log.exists():
        statuses = _missing_log_statuses(args.jobs, args.scheduler_log)
        flows = [status.to_flow_entry(now, args.window_minutes) for status in statuses]
        payload = {
            "flow_id": FLOW_SET_ID,
            "label": FLOW_LABEL,
            "generated_at": now.isoformat(),
            "scheduler_log": str(args.scheduler_log),
            "window_minutes": args.window_minutes,
            "limit": args.limit,
            "alerts": [alert for status in statuses for alert in status.alerts],
            "status": "error",
            "flows": flows,
            "jobs": [status.to_dict(now) for status in statuses],
            "block": FLOW_SET_ID,
        }
        emit_output(payload, json_mode=args.json, output_path=args.output)
        return exit_code_from_status("error")

    try:
        records = load_records(args.scheduler_log, JOB_EVENTS, args.limit)
    except OSError as exc:
        statuses = _missing_log_statuses(args.jobs, args.scheduler_log)
        for status in statuses:
            status.alerts.clear()
            status.add_alert(f"{status.job_name}: unable to read log: {exc}", "error")
        flows = [status.to_flow_entry(now, args.window_minutes) for status in statuses]
        payload = {
            "flow_id": FLOW_SET_ID,
            "label": FLOW_LABEL,
            "generated_at": now.isoformat(),
            "scheduler_log": str(args.scheduler_log),
            "window_minutes": args.window_minutes,
            "limit": args.limit,
            "alerts": [alert for status in statuses for alert in status.alerts],
            "status": "error",
            "flows": flows,
            "jobs": [status.to_dict(now) for status in statuses],
            "block": FLOW_SET_ID,
        }
        emit_output(payload, json_mode=args.json, output_path=args.output)
        return exit_code_from_status("error")

    statuses = _analyze_records(
        path=args.scheduler_log,
        records=records,
        jobs=args.jobs,
        now=now,
        window=window,
    )
    flows = [status.to_flow_entry(now, args.window_minutes) for status in statuses]
    alerts = [alert for status in statuses for alert in status.alerts]
    overall_status = "ok"
    for status in statuses:
        overall_status = _worse(overall_status, status.status)
    payload = {
        "flow_id": FLOW_SET_ID,
        "label": FLOW_LABEL,
        "generated_at": now.isoformat(),
        "scheduler_log": str(args.scheduler_log),
        "window_minutes": args.window_minutes,
        "limit": args.limit,
        "alerts": alerts,
        "status": overall_status,
        "flows": flows,
        "jobs": [status.to_dict(now) for status in statuses],
        "block": FLOW_SET_ID,
    }
    emit_output(payload, json_mode=args.json, output_path=args.output)
    return exit_code_from_status(overall_status)


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
