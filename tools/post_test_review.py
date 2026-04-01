#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.feed_logs.replay_last import _summarize as summarize_feed_flow
from tools.log_watch.common import extract_timestamp, load_records

VERDICTS = {
    "clean": "PASS_CLEAN",
    "degraded-but-expected": "PASS_WITH_EXPECTED_DEGRADATION",
    "unexpected-degradation": "FAIL_OBSERVABILITY_GATE",
    "no-evidence-blocker": "FAIL_NO_EVIDENCE",
}

TODAY_EVENTS = {"feed.entry", "feed.debug", "feed.error", "day_brief.built", "day_brief.fallback", "day_brief.validation_failed", "day_brief.response_returned"}
REPORT_EVENTS = {
    "report.workflow.run_start",
    "report.workflow.run_started",
    "report.workflow.generation_start",
    "report.workflow.generation_stats",
    "report.workflow.generation_complete",
    "report.failure_packet",
    "week_brief_built",
    "week_brief_fallback_triggered",
    "week_brief_validation_failed",
    "week_brief.response_returned",
}

EXPECTED_REASON_CODES = {
    "fallback_expected",
    "expected_degradation",
    "test_expected_fallback",
}


@dataclass
class FlowDigest:
    flow_id: str
    status: str
    records_checked: int
    last_timestamp: str | None
    sample_trace_id: str | None
    sample_correlation_id: str | None
    sample_report_id: str | None
    fallback_count: int
    reason_codes: list[str]
    alerts: list[str]
    counters: dict[str, int]
    evidence: list[dict[str, Any]]


def parse_since(value: str) -> timedelta:
    raw = value.strip().lower()
    if raw.endswith("m"):
        return timedelta(minutes=int(raw[:-1]))
    if raw.endswith("h"):
        return timedelta(hours=int(raw[:-1]))
    if raw.endswith("d"):
        return timedelta(days=int(raw[:-1]))
    raise argparse.ArgumentTypeError("--since must look like 90m, 6h, or 2d")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _recent_records(path: Path, *, allowed_events: set[str], limit: int, since_delta: timedelta) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    now = _now()
    threshold = now - since_delta
    records = load_records(path, allowed_events, limit)
    recent: list[dict[str, Any]] = []
    for record in records:
        ts = extract_timestamp(record)
        if ts is None:
            continue
        if ts >= threshold:
            recent.append(record)
    return recent


def _reason_code(record: dict[str, Any]) -> str | None:
    for key in ("primary_reason_code", "reason_code", "reason"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    reason_codes = record.get("reason_codes")
    if isinstance(reason_codes, list):
        for item in reason_codes:
            if isinstance(item, str) and item.strip():
                return item.strip()
    return None


def _pick_evidence(records: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    picked: list[dict[str, Any]] = []
    for record in reversed(records):
        event = record.get("event")
        if event in {"feed.error", "day_brief.fallback", "day_brief.validation_failed", "week_brief_fallback_triggered", "week_brief_validation_failed", "report.failure_packet"} or record.get("fallback_mode"):
            picked.append({
                "event": event,
                "timestamp": record.get("timestamp") or record.get("logged_at") or record.get("time"),
                "trace_id": record.get("trace_id"),
                "correlation_id": record.get("correlation_id"),
                "report_id": record.get("report_id") or record.get("resumed_report_id"),
                "reason": _reason_code(record),
            })
        if len(picked) >= limit:
            break
    if not picked:
        for record in reversed(records):
            picked.append({
                "event": record.get("event"),
                "timestamp": record.get("timestamp") or record.get("logged_at") or record.get("time"),
                "trace_id": record.get("trace_id"),
                "correlation_id": record.get("correlation_id"),
                "report_id": record.get("report_id") or record.get("resumed_report_id"),
                "reason": _reason_code(record),
            })
            if len(picked) >= min(limit, 2):
                break
    return list(reversed(picked))


def _classify_status(*, has_records: bool, degradation_count: int, expected_reason_hit: bool) -> str:
    if not has_records:
        return "no-evidence-blocker"
    if degradation_count <= 0:
        return "clean"
    if expected_reason_hit:
        return "degraded-but-expected"
    return "unexpected-degradation"


def analyze_today(feed_log: Path, *, since_delta: timedelta, limit: int) -> FlowDigest:
    records = _recent_records(feed_log, allowed_events=TODAY_EVENTS, limit=limit, since_delta=since_delta)
    counters = Counter()
    reason_codes: Counter[str] = Counter()
    alerts: list[str] = []
    sample_trace_id = None
    sample_correlation_id = None
    sample_report_id = None
    last_timestamp = None
    fallback_count = 0

    for record in records:
        sample_trace_id = sample_trace_id or record.get("trace_id")
        sample_correlation_id = sample_correlation_id or record.get("correlation_id")
        sample_report_id = sample_report_id or record.get("report_id") or record.get("resumed_report_id")
        ts = extract_timestamp(record)
        if ts is not None:
            last_timestamp = ts.isoformat()
        event = record.get("event")
        stage = record.get("stage")
        if event == "feed.entry":
            counters["today_requests_total"] += 1
        if event == "feed.debug" and stage == "auth_fallback":
            counters["today_auth_fallback_anonymous_total"] += 1
            fallback_count += 1
        if record.get("personalization_level") == "profile_light":
            counters["today_profile_light_total"] += 1
        if record.get("fallback_mode") is True:
            counters["today_fallback_total"] += 1
            fallback_count += 1
        if event == "day_brief.validation_failed":
            counters["today_validator_fallback_total"] += 1
            fallback_count += 1
        factor_count = record.get("factor_count")
        if isinstance(factor_count, int) and factor_count < 3:
            counters["today_low_factor_count_total"] += 1
        reason = _reason_code(record)
        if reason:
            reason_codes[reason] += 1

    if counters["today_auth_fallback_anonymous_total"] > 0:
        alerts.append("today auth fallback detected")
    if counters["today_validator_fallback_total"] > 0:
        alerts.append("today validator fallback detected")
    status = _classify_status(
        has_records=bool(records),
        degradation_count=fallback_count,
        expected_reason_hit=not reason_codes.keys().isdisjoint(EXPECTED_REASON_CODES),
    )

    if not records:
        alerts.append("no recent today/day brief evidence")

    return FlowDigest(
        flow_id="FLOW-TODAY-WEEK-TODAY",
        status=status,
        records_checked=len(records),
        last_timestamp=last_timestamp,
        sample_trace_id=sample_trace_id,
        sample_correlation_id=sample_correlation_id,
        sample_report_id=sample_report_id,
        fallback_count=fallback_count,
        reason_codes=[name for name, _ in reason_codes.most_common(3)],
        alerts=alerts,
        counters=dict(counters),
        evidence=_pick_evidence(records),
    )


def analyze_week(report_log: Path, *, since_delta: timedelta, limit: int) -> FlowDigest:
    records = _recent_records(report_log, allowed_events=REPORT_EVENTS, limit=limit, since_delta=since_delta)
    counters = Counter()
    reason_codes: Counter[str] = Counter()
    alerts: list[str] = []
    sample_trace_id = None
    sample_correlation_id = None
    sample_report_id = None
    last_timestamp = None
    fallback_count = 0

    for record in records:
        sample_trace_id = sample_trace_id or record.get("trace_id")
        sample_correlation_id = sample_correlation_id or record.get("correlation_id")
        sample_report_id = sample_report_id or record.get("report_id") or record.get("resumed_report_id")
        ts = extract_timestamp(record)
        if ts is not None:
            last_timestamp = ts.isoformat()
        event = record.get("event")
        if event in {"week_brief.response_returned", "week_brief_built", "report.workflow.generation_start"}:
            counters["week_requests_total"] += 1
        if event in {"week_brief_fallback_triggered", "week_brief_validation_failed"}:
            counters["week_fallback_total"] += 1
            fallback_count += 1
        if event == "week_brief_validation_failed":
            counters["week_validation_failed_total"] += 1
        if record.get("chunk_parse_degraded") is True:
            counters["report_chunk_parse_degraded_total"] += 1
        factor_count = record.get("factor_count")
        if isinstance(factor_count, int) and factor_count <= 1:
            counters["week_low_factor_count_total"] += 1
        confidence = record.get("week_brief_confidence_bucket") or record.get("confidence_bucket")
        if confidence == "low":
            counters["week_low_confidence_total"] += 1
        reason = _reason_code(record)
        if reason:
            reason_codes[reason] += 1

    if counters["week_validation_failed_total"] > 0:
        alerts.append("week validation failure detected")
    if counters["report_chunk_parse_degraded_total"] > 0:
        alerts.append("week/report chunk parse degraded")
    status = _classify_status(
        has_records=bool(records),
        degradation_count=fallback_count,
        expected_reason_hit=not reason_codes.keys().isdisjoint(EXPECTED_REASON_CODES),
    )

    if not records:
        alerts.append("no recent week/report evidence")

    return FlowDigest(
        flow_id="FLOW-TODAY-WEEK-WEEK",
        status=status,
        records_checked=len(records),
        last_timestamp=last_timestamp,
        sample_trace_id=sample_trace_id,
        sample_correlation_id=sample_correlation_id,
        sample_report_id=sample_report_id,
        fallback_count=fallback_count,
        reason_codes=[name for name, _ in reason_codes.most_common(3)],
        alerts=alerts,
        counters=dict(counters),
        evidence=_pick_evidence(records),
    )


def build_output(*, profile: str, since: str, feed_log: Path, report_log: Path, today: FlowDigest, week: FlowDigest) -> dict[str, Any]:
    overall = "clean"
    for flow in (today, week):
        if flow.status == "no-evidence-blocker":
            overall = "no-evidence-blocker"
            break
        if flow.status == "unexpected-degradation":
            overall = "unexpected-degradation"
            break
        if flow.status == "degraded-but-expected":
            overall = "degraded-but-expected"
    replay_summary = None
    feed_records = _recent_records(feed_log, allowed_events=TODAY_EVENTS, limit=200, since_delta=parse_since(since))
    if feed_records:
        replay_summary = summarize_feed_flow(feed_records[-20:])
    return {
        "profile": profile,
        "analysis_window": since,
        "logs_reviewed": [str(feed_log), str(report_log)],
        "flows": [today.__dict__, week.__dict__],
        "replay_summary": replay_summary,
        "verdict": VERDICTS[overall],
    }


def print_md(payload: dict[str, Any]) -> None:
    print(f"# Post-test observability gate — {payload['verdict']}")
    print()
    print(f"- profile: `{payload['profile']}`")
    print(f"- analysis_window: `{payload['analysis_window']}`")
    print(f"- logs_reviewed: {', '.join(f'`{item}`' for item in payload['logs_reviewed'])}")
    for flow in payload["flows"]:
        print()
        print(f"## {flow['flow_id']} — {flow['status']}")
        print(f"- records_checked: {flow['records_checked']}")
        print(f"- last_timestamp: `{flow['last_timestamp']}`")
        print(f"- fallback_count: {flow['fallback_count']}")
        print(f"- sample_trace_id: `{flow['sample_trace_id']}`")
        print(f"- sample_correlation_id: `{flow['sample_correlation_id']}`")
        print(f"- sample_report_id: `{flow['sample_report_id']}`")
        print(f"- reason_codes: {', '.join(flow['reason_codes']) if flow['reason_codes'] else '-'}")
        print(f"- alerts: {', '.join(flow['alerts']) if flow['alerts'] else '-'}")
        if flow.get("evidence"):
            print("- evidence_samples:")
            for evidence in flow["evidence"]:
                print(
                    "  - "
                    f"{evidence.get('event')} @ {evidence.get('timestamp')} "
                    f"trace={evidence.get('trace_id') or '-'} "
                    f"corr={evidence.get('correlation_id') or '-'} "
                    f"report={evidence.get('report_id') or '-'} "
                    f"reason={evidence.get('reason') or '-'}"
                )
    if payload.get("replay_summary"):
        print()
        print("## Latest feed replay")
        print(json.dumps(payload["replay_summary"], ensure_ascii=False, indent=2))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal post-test observability gate for Today/Week")
    parser.add_argument("--profile", choices=["today-week"], default="today-week")
    parser.add_argument("--since", type=parse_since, default=timedelta(minutes=90))
    parser.add_argument("--feed-log", type=Path, default=PROJECT_ROOT / "logs" / "feed.jsonl")
    parser.add_argument("--report-log", type=Path, default=PROJECT_ROOT / "logs" / "report.jsonl")
    parser.add_argument("--limit", type=int, default=4000)
    parser.add_argument("--report-format", choices=["json", "md"], default="json")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    today = analyze_today(args.feed_log, since_delta=args.since, limit=args.limit)
    week = analyze_week(args.report_log, since_delta=args.since, limit=args.limit)
    since_label = f"{int(args.since.total_seconds() // 60)}m"
    payload = build_output(
        profile=args.profile,
        since=since_label,
        feed_log=args.feed_log,
        report_log=args.report_log,
        today=today,
        week=week,
    )
    if args.report_format == "md":
        print_md(payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] in {"PASS_CLEAN", "PASS_WITH_EXPECTED_DEGRADATION"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
