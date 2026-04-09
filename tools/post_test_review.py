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

from backend.app.logging_utils import LOG_DIR as ACTIVE_LOG_DIR
from tools.feed_logs.replay_last import _summarize as summarize_feed_flow
from tools.log_watch.common import extract_timestamp, load_records
from tools.rendered_artifacts import load_rendered_summaries

VERDICTS = {
    "clean": "PASS_CLEAN",
    "degraded-but-expected": "PASS_WITH_EXPECTED_DEGRADATION",
    "unexpected-degradation": "FAIL_OBSERVABILITY_GATE",
    "no-evidence-blocker": "FAIL_NO_EVIDENCE",
}

TODAY_EVENTS = {
    "feed.entry",
    "feed.debug",
    "feed.error",
    "feed.block.start",
    "feed.block.end",
    "feed.generated",
    "feed.semantic_blocks",
    "day_brief.built",
    "day_brief.fallback",
    "day_brief.validation_failed",
    "day_brief.response_returned",
}
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
                "request_id": record.get("request_id"),
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
                "request_id": record.get("request_id"),
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


def _canonical_log_paths(active_log: Path, filename: str) -> list[Path]:
    paths = [active_log]
    fallback_log = Path("/tmp/astro-project/logs") / filename
    if active_log == ACTIVE_LOG_DIR / filename and fallback_log != active_log:
        paths.append(fallback_log)
    return paths


def analyze_today(feed_log: Path, *, since_delta: timedelta, limit: int) -> FlowDigest:
    records = []
    for path in _canonical_log_paths(feed_log, "feed.jsonl"):
        records.extend(_recent_records(path, allowed_events=TODAY_EVENTS, limit=limit, since_delta=since_delta))
    records = sorted(records, key=lambda record: extract_timestamp(record) or datetime.min.replace(tzinfo=timezone.utc))[-limit:]
    counters = Counter()
    reason_codes: Counter[str] = Counter()
    alerts: list[str] = []
    sample_trace_id = None
    sample_correlation_id = None
    sample_request_id = None
    sample_report_id = None
    last_timestamp = None
    fallback_count = 0
    saw_feed_entry = False
    saw_today_success = False

    for record in records:
        sample_trace_id = sample_trace_id or record.get("trace_id")
        sample_correlation_id = sample_correlation_id or record.get("correlation_id")
        sample_request_id = sample_request_id or record.get("request_id")
        sample_report_id = sample_report_id or record.get("report_id") or record.get("resumed_report_id")
        ts = extract_timestamp(record)
        if ts is not None:
            last_timestamp = ts.isoformat()
        event = record.get("event")
        stage = record.get("stage")
        if event == "feed.entry":
            counters["today_requests_total"] += 1
            saw_feed_entry = True
        if event == "feed.debug" and stage == "auth_fallback":
            counters["today_auth_fallback_anonymous_total"] += 1
            fallback_count += 1
        if event == "day_brief.response_returned" and record.get("fallback_mode") is False:
            saw_today_success = True
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
    effective_fallback_count = 0 if saw_today_success else fallback_count
    status = _classify_status(
        has_records=bool(records),
        degradation_count=effective_fallback_count,
        expected_reason_hit=not reason_codes.keys().isdisjoint(EXPECTED_REASON_CODES),
    )

    if not records:
        alerts.append("no recent today/day brief evidence")
    elif saw_feed_entry and saw_today_success and not (sample_trace_id or sample_request_id):
        alerts.append("today evidence missing concrete trace_id/request_id")
        status = "no-evidence-blocker"

    return FlowDigest(
        flow_id="FLOW-TODAY-WEEK-TODAY",
        status=status,
        records_checked=len(records),
        last_timestamp=last_timestamp,
        sample_trace_id=sample_trace_id,
        sample_correlation_id=sample_correlation_id,
        sample_report_id=sample_report_id,
        fallback_count=effective_fallback_count,
        reason_codes=[name for name, _ in reason_codes.most_common(3)],
        alerts=alerts,
        counters=dict(counters),
        evidence=_pick_evidence(records),
    )


def analyze_week(report_log: Path, *, since_delta: timedelta, limit: int) -> FlowDigest:
    records = []
    for path in _canonical_log_paths(report_log, "report.jsonl"):
        records.extend(_recent_records(path, allowed_events=REPORT_EVENTS, limit=limit, since_delta=since_delta))
    records = sorted(records, key=lambda record: extract_timestamp(record) or datetime.min.replace(tzinfo=timezone.utc))[-limit:]
    counters = Counter()
    reason_codes: Counter[str] = Counter()
    alerts: list[str] = []
    sample_trace_id = None
    sample_correlation_id = None
    sample_request_id = None
    sample_report_id = None
    last_timestamp = None
    fallback_count = 0

    for record in records:
        sample_trace_id = sample_trace_id or record.get("trace_id")
        sample_correlation_id = sample_correlation_id or record.get("correlation_id")
        sample_request_id = sample_request_id or record.get("request_id")
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


def _rendered_gate_summary_map(rendered_summaries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        "FLOW-TODAY-WEEK-TODAY": [],
        "FLOW-TODAY-WEEK-WEEK": [],
        "FLOW-READ-SURFACE": [],
    }
    for item in rendered_summaries:
        flow_id = str(item.get("flow_id") or "")
        surface = str(item.get("surface") or "").lower()
        if flow_id == "FLOW-TODAY-PREMIUM" or surface == "today":
            grouped["FLOW-TODAY-WEEK-TODAY"].append(item)
        elif flow_id == "FLOW-WEEK-BRIEF" or surface == "week":
            grouped["FLOW-TODAY-WEEK-WEEK"].append(item)
        elif flow_id == "FLOW-READ-SURFACE" or surface == "read":
            grouped["FLOW-READ-SURFACE"].append(item)
    return grouped


def _rendered_presence_summary(rendered: list[dict[str, Any]]) -> dict[str, Any]:
    pass_modes: list[str] = []
    assertion_classes: list[str] = []
    statuses: list[str] = []
    parity_statuses: list[str] = []
    parity_notes: list[str] = []
    invariant_groups: list[str] = []
    site_web_present = False
    telegram_webapp_present = False
    both_present = False

    for item in rendered:
        pass_mode = item.get("pass_mode") or {}
        if not isinstance(pass_mode, dict):
            pass_mode = {}
        key = str(pass_mode.get("key") or "unknown")
        pass_modes.append(key)
        if key == "site_web":
            site_web_present = True
        elif key == "telegram_webapp":
            telegram_webapp_present = True
        elif key == "both":
            both_present = True
            site_web_present = True
            telegram_webapp_present = True

        assertion_class = item.get("assertion_class")
        if assertion_class:
            assertion_classes.append(str(assertion_class))

        status = item.get("status")
        if status:
            statuses.append(str(status))

        details = item.get("details") or {}
        if isinstance(details, dict):
            parity = details.get("parity") or {}
            if isinstance(parity, dict) and parity.get("parity_status"):
                parity_statuses.append(str(parity.get("parity_status")))
                for note in parity.get("notes") or []:
                    parity_notes.append(str(note))
                for group in parity.get("invariant_groups") or []:
                    invariant_groups.append(str(group))

    return {
        "summary_count": len(rendered),
        "pass_modes": sorted(set(pass_modes)),
        "site_web_present": site_web_present,
        "telegram_webapp_present": telegram_webapp_present,
        "both_present": both_present,
        "parity_present": bool(parity_statuses),
        "parity_statuses": sorted(set(parity_statuses)),
        "parity_notes": sorted(set(parity_notes)),
        "invariant_groups": sorted(set(invariant_groups)),
        "assertion_classes": sorted(set(assertion_classes)),
        "statuses": sorted(set(statuses)),
    }


def _rendered_verdict_notes(*, flow_status: str, rendered_presence: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if rendered_presence.get("summary_count", 0) == 0:
        return notes

    notes.append("rendered evidence is additive and does not replace canonical logs/traces")
    if flow_status == "no-evidence-blocker":
        notes.append("rendered evidence present but canonical source-of-truth evidence missing")
    elif flow_status == "clean":
        notes.append("canonical evidence clean; rendered evidence attached as supporting slice")
    elif flow_status == "degraded-but-expected":
        notes.append("canonical evidence shows expected degradation; rendered evidence attached as supporting slice")
    elif flow_status == "unexpected-degradation":
        notes.append("canonical evidence shows unexpected degradation; rendered evidence attached for context only")

    if rendered_presence.get("parity_present"):
        notes.append("rendered parity metadata detected")
    if rendered_presence.get("both_present"):
        notes.append("rendered both/pass pilot semantics materialized without replacing wrapper verdict model")
    return notes


def _augment_flow_with_rendered(flow: FlowDigest, rendered: list[dict[str, Any]]) -> dict[str, Any]:
    payload = dict(flow.__dict__)
    payload["rendered_summaries"] = rendered
    rendered_presence = _rendered_presence_summary(rendered)
    payload["rendered_presence"] = rendered_presence
    payload["rendered_verdict_notes"] = _rendered_verdict_notes(flow_status=flow.status, rendered_presence=rendered_presence)
    if rendered and flow.status == "no-evidence-blocker":
        payload["alerts"] = [*flow.alerts, "rendered summaries present without canonical logs"]
    return payload


def build_output(*, profile: str, since: str, feed_log: Path, report_log: Path, today: FlowDigest, week: FlowDigest, rendered_summaries: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rendered_index = _rendered_gate_summary_map(rendered_summaries or [])
    flows: list[dict[str, Any]] = []
    overall = "clean"

    if profile == "read-only":
        read_rendered = rendered_index["FLOW-READ-SURFACE"]
        read_presence = _rendered_presence_summary(read_rendered)
        read_status = "clean"
        if read_presence.get("summary_count", 0) == 0:
            read_status = "no-evidence-blocker"
        elif not read_presence.get("site_web_present"):
            read_status = "no-evidence-blocker"
        elif "fallback_expected" in read_presence.get("assertion_classes", []) and "rendered_hygiene" not in read_presence.get("assertion_classes", []):
            read_status = "degraded-but-expected"

        read_flow = {
            "flow_id": "FLOW-READ-SURFACE",
            "status": read_status,
            "records_checked": read_presence.get("summary_count", 0),
            "last_timestamp": max((item.get("recorded_at") for item in read_rendered), default=None),
            "fallback_count": sum(1 for item in read_rendered if item.get("assertion_class") == "fallback_expected"),
            "sample_trace_id": None,
            "sample_correlation_id": None,
            "sample_report_id": None,
            "reason_codes": sorted(set(str((item.get("details") or {}).get("fallbackReason")) for item in read_rendered if (item.get("details") or {}).get("fallbackReason"))),
            "alerts": [] if read_presence.get("summary_count", 0) else ["no rendered read evidence materialized"],
            "counters": {
                "rendered_site_web_total": sum(1 for item in read_rendered if ((item.get("pass_mode") or {}).get("key") == "site_web")),
                "rendered_fallback_expected_total": sum(1 for item in read_rendered if item.get("assertion_class") == "fallback_expected"),
            },
            "evidence": [
                {
                    "event": item.get("scenario_id"),
                    "timestamp": item.get("recorded_at"),
                    "trace_id": None,
                    "correlation_id": None,
                    "report_id": (item.get("details") or {}).get("route"),
                    "reason": (item.get("details") or {}).get("fallbackReason"),
                }
                for item in read_rendered[-3:]
            ],
        }
        flows = [_augment_flow_with_rendered(FlowDigest(**read_flow), read_rendered)]
        overall = read_status
        replay_summary = None
    else:
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
        flows = [
            _augment_flow_with_rendered(today, rendered_index["FLOW-TODAY-WEEK-TODAY"]),
            _augment_flow_with_rendered(week, rendered_index["FLOW-TODAY-WEEK-WEEK"]),
        ]

    return {
        "profile": profile,
        "analysis_window": since,
        "logs_reviewed": [str(feed_log), str(report_log)],
        "flows": flows,
        "rendered_summary_count": len(rendered_summaries or []),
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
        if flow.get("rendered_presence"):
            rendered_presence = flow["rendered_presence"]
            print(
                "- rendered_presence: "
                f"count={rendered_presence.get('summary_count', 0)} "
                f"pass_modes={','.join(rendered_presence.get('pass_modes', [])) or '-'} "
                f"site_web={rendered_presence.get('site_web_present')} "
                f"telegram_webapp={rendered_presence.get('telegram_webapp_present')} "
                f"parity_present={rendered_presence.get('parity_present')}"
            )
            print(
                "- rendered_statuses: "
                f"{', '.join(rendered_presence.get('statuses', [])) if rendered_presence.get('statuses') else '-'}"
            )
            print(
                "- rendered_assertion_classes: "
                f"{', '.join(rendered_presence.get('assertion_classes', [])) if rendered_presence.get('assertion_classes') else '-'}"
            )
            print(
                "- rendered_parity_statuses: "
                f"{', '.join(rendered_presence.get('parity_statuses', [])) if rendered_presence.get('parity_statuses') else '-'}"
            )
        if flow.get("rendered_verdict_notes"):
            print(f"- rendered_verdict_notes: {', '.join(flow['rendered_verdict_notes'])}")
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
    parser = argparse.ArgumentParser(description="Minimal post-test observability gate for Today/Week/Read")
    parser.add_argument("--profile", choices=["today-week", "read-only"], default="today-week")
    parser.add_argument("--since", type=parse_since, default=timedelta(minutes=90))
    parser.add_argument("--feed-log", type=Path, default=ACTIVE_LOG_DIR / "feed.jsonl")
    parser.add_argument("--report-log", type=Path, default=ACTIVE_LOG_DIR / "report.jsonl")
    parser.add_argument("--rendered-dir", type=Path, default=PROJECT_ROOT / "test-results" / "rendered-gate")
    parser.add_argument("--limit", type=int, default=4000)
    parser.add_argument("--report-format", choices=["json", "md"], default="json")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    today = analyze_today(args.feed_log, since_delta=args.since, limit=args.limit)
    week = analyze_week(args.report_log, since_delta=args.since, limit=args.limit)
    rendered_summaries = load_rendered_summaries(args.rendered_dir)
    since_label = f"{int(args.since.total_seconds() // 60)}m"
    payload = build_output(
        profile=args.profile,
        since=since_label,
        feed_log=args.feed_log,
        report_log=args.report_log,
        today=today,
        week=week,
        rendered_summaries=rendered_summaries,
    )
    if args.report_format == "md":
        print_md(payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] in {"PASS_CLEAN", "PASS_WITH_EXPECTED_DEGRADATION"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
