"""Shared helpers for log watcher scripts."""

from __future__ import annotations

import argparse
import json
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

STATUS_EXIT_CODES = {
    "ok": 0,
    "warning": 1,
    "critical": 2,
    "error": 3,
    "invalid": 4,
}

TIMESTAMP_KEYS = (
    "timestamp",
    "@timestamp",
    "ts",
    "time",
    "event_ts",
    "event_time",
    "logged_at",
)


def parse_datetime_arg(value: str) -> datetime:
    """Parse an ISO datetime argument for CLI overrides."""

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - surfaced via argparse
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


def extract_timestamp(record: dict[str, Any]) -> datetime | None:
    """Return the first well-formed timestamp from the record."""

    for key in TIMESTAMP_KEYS:
        if key in record:
            ts = _coerce_timestamp(record[key])
            if ts is not None:
                if ts.tzinfo is None:
                    return ts.replace(tzinfo=timezone.utc)
                return ts.astimezone(timezone.utc)
    return None


def format_dt(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def load_records(
    path: Path,
    allowed_events: set[str] | None,
    limit: int,
    allowed_prefixes: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Load up to ``limit`` JSON records filtered by event sets or prefixes."""

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
            if not isinstance(data, dict):
                continue
            event = data.get("event")
            if allowed_events and event not in allowed_events:
                continue
            if allowed_prefixes and (not isinstance(event, str) or not any(event.startswith(prefix) for prefix in allowed_prefixes)):
                continue
            records.append(data)
    return list(records)


def fallback_timestamp(path: Path, index: int, total: int) -> datetime:
    base = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return base - timedelta(microseconds=(total - index))


def summarize_alerts(alerts: Iterable[str]) -> str:
    return "; ".join(alerts)


def exit_code_from_status(status: str) -> int:
    return STATUS_EXIT_CODES.get(status, 1)


def emit_output(payload: dict[str, Any], *, json_mode: bool, output_path: str | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2 if not json_mode else None)
    if output_path and output_path != "-":
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return
    if output_path == "-" or json_mode:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(text)


def percentile(samples: Sequence[float], pct: float) -> float | None:
    if not samples:
        return None
    if pct <= 0:
        return float(sorted(samples)[0])
    if pct >= 100:
        return float(sorted(samples)[-1])
    ordered = sorted(samples)
    index = (pct / 100) * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def compute_percentiles(samples: Sequence[float], pct_map: Mapping[str, float] | None = None) -> dict[str, float]:
    pct_map = pct_map or {
        "p50": 50,
        "p90": 90,
        "p95": 95,
        "p99": 99,
    }
    results: dict[str, float] = {}
    if not samples:
        return results
    for name, pct in pct_map.items():
        value = percentile(samples, pct)
        if value is not None:
            results[name] = round(value, 2)
    return results


def ensure_positive(value: int, *, name: str, parser: argparse.ArgumentParser) -> int:
    if value <= 0:
        parser.error(f"{name} must be > 0")
    return value
