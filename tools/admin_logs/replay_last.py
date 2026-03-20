#!/usr/bin/env python3
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ADMIN_EVENTS = {
    "admin.entry",
    "admin.queue",
    "admin.section_regenerate",
    "admin.export",
    "admin.error",
    "admin.entitlement_grant",
}


def _coerce_record(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("event") not in ADMIN_EVENTS:
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
        key = str(record.get("report_id") or record.get("target_report_id") or f"idx-{index}")
        grouped[key].append(record)
    if not grouped:
        return []
    latest_key = next(reversed(grouped))
    return grouped[latest_key]


def _summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "report_id": None,
        "report_type": None,
        "events": [],
        "sections": [],
        "queue": {"pending": None, "running": None, "error": None},
        "fallback": [],
        "entitlement_actions": [],
    }
    sections: list[str] = []
    fallback: list[str] = []
    entitlement_actions: list[dict[str, Any]] = []
    for record in records:
        summary["report_id"] = summary["report_id"] or record.get("report_id") or record.get("target_report_id")
        summary["report_type"] = summary["report_type"] or record.get("report_type")
        stage = record.get("stage") or record.get("event")
        summary["events"].append(stage)
        if record.get("section_id") and record["section_id"] not in sections:
            sections.append(str(record["section_id"]))
        if record.get("fallback") or stage in {"fallback_content", "fallback_applied"}:
            fallback.append(str(record.get("section_id") or stage))
        for key in ("pending", "running", "error"):
            if record.get(key) is not None:
                summary["queue"][key] = record.get(key)
        if record.get("event") == "admin.entitlement_grant":
            entitlement_actions.append({
                "action": record.get("action"),
                "report_type": record.get("report_type"),
                "entitlement_id": record.get("entitlement_id"),
                "status": record.get("status"),
            })
    summary["sections"] = sections
    summary["fallback"] = fallback
    summary["entitlement_actions"] = entitlement_actions
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
        print(json.dumps({"status": "no_admin_logs", "path": str(path)}, ensure_ascii=False))
        return 0
    print(json.dumps(_summarize(flow), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
