#!/usr/bin/env python3
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def _coerce_record(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    event = data.get("event")
    if event not in {"feed.entry", "feed.debug", "feed.error"}:
        return None
    return data


def _load_records(path: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = _coerce_record(line)
            if record is not None:
                records.append(record)
    return records[-limit:]


def _group_latest_flow(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, record in enumerate(records):
        key = str(record.get("cache_scope") or record.get("path") or f"idx-{index}")
        grouped[key].append(record)
    if not grouped:
        return []
    latest_key = next(reversed(grouped))
    return grouped[latest_key]


def _summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "events": [record.get("stage") or record.get("event") for record in records],
        "auth": None,
        "personalization_level": None,
        "prompt_path": None,
        "fallback": False,
        "fallback_reason": None,
        "cache_hit": False,
        "cache_scope": None,
        "location": None,
        "timezone": None,
    }
    for record in records:
        stage = record.get("stage")
        if record.get("auth_mode") and summary["auth"] is None:
            summary["auth"] = record.get("auth_mode")
        if record.get("personalization_level"):
            summary["personalization_level"] = record.get("personalization_level")
        if record.get("prompt_path"):
            summary["prompt_path"] = record.get("prompt_path")
        if record.get("cache_scope"):
            summary["cache_scope"] = record.get("cache_scope")
        if record.get("location"):
            summary["location"] = record.get("location")
        if record.get("timezone"):
            summary["timezone"] = record.get("timezone")
        if stage == "facts_cache_hit":
            summary["cache_hit"] = True
        if record.get("fallback_mode") or record.get("event") == "feed.error" or stage == "auth_fallback":
            summary["fallback"] = True
        if record.get("fallback_reason"):
            summary["fallback_reason"] = record.get("fallback_reason")
        elif stage == "auth_fallback":
            summary["fallback_reason"] = record.get("reason")
    return summary


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: replay_last.py <jsonl-log-file> [limit]", file=sys.stderr)
        return 2
    path = Path(argv[1])
    limit = int(argv[2]) if len(argv) > 2 else 200
    if not path.exists():
        print(f"Log file not found: {path}", file=sys.stderr)
        return 2
    records = _load_records(path, limit)
    flow = _group_latest_flow(records)
    if not flow:
        print(json.dumps({"status": "no_feed_logs", "path": str(path)}, ensure_ascii=False))
        return 0
    print(json.dumps(_summarize(flow), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
