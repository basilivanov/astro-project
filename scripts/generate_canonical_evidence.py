#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.logging_utils import LOG_DIR, configure_structlog, log_catalog_event, log_grace_event

FLOW_ORDER = ("today", "week", "admin", "catalog")
FLOW_SET = set(FLOW_ORDER)


@dataclass(frozen=True)
class EvidenceRecord:
    flow: str
    event: str
    log_path: Path
    trace_id: str
    request_id: str
    correlation_id: str
    report_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        payload = {
            "flow": self.flow,
            "event": self.event,
            "log_path": str(self.log_path),
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
        }
        if self.report_id:
            payload["report_id"] = self.report_id
        return payload


def _stable_ids(flow: str) -> dict[str, str]:
    nonce = uuid.uuid4().hex[:12]
    return {
        "trace_id": f"canonical-{flow}-trace-{nonce}",
        "request_id": f"canonical-{flow}-request-{nonce}",
        "correlation_id": f"canonical-{flow}-correlation-{nonce}",
        "report_id": f"canonical-{flow}-report-{nonce}",
    }


def _emit_grace_event(event: str, *, flow: str, block: str, **fields: object) -> None:
    log_grace_event(
        "info",
        event,
        module="M-OPS-AUTOMATION",
        fn="generate_canonical_evidence",
        block=block,
        canonical_evidence=True,
        canonical_flow=flow,
        evidence_producer="scripts/generate_canonical_evidence.py",
        **fields,
    )


def emit_today() -> list[EvidenceRecord]:
    ids = _stable_ids("today")
    base_fields = {
        **ids,
        "path": "/api/feed/today",
        "auth_mode": "telegram",
        "user_id": "canonical-evidence-user",
        "telegram_id": "canonical-evidence-telegram",
        "cache_scope": "canonical-evidence-today",
        "personalization_level": "personalized_v2",
        "prompt_path": "personalized_daily_v2",
    }
    _emit_grace_event(
        "feed.entry",
        flow="today",
        block="TODAY_REQUEST_START",
        stage="request_start",
        **base_fields,
    )
    _emit_grace_event(
        "feed.debug",
        flow="today",
        block="TODAY_REQUEST_SUCCESS",
        stage="request_success",
        fallback_mode=False,
        **base_fields,
    )
    _emit_grace_event(
        "day_brief.response_returned",
        flow="today",
        block="TODAY_RESPONSE_RETURNED",
        fallback_mode=False,
        factor_count=5,
        text_layer_status={
            "work": {"description": "complete", "why": "complete"},
            "love": {"description": "complete", "why": "complete"},
            "energy": {"description": "complete", "why": "complete"},
        },
        text_layer_reason_codes={},
        **base_fields,
    )
    return [
        EvidenceRecord(
            flow="today",
            event="day_brief.response_returned",
            log_path=LOG_DIR / "feed.jsonl",
            trace_id=ids["trace_id"],
            request_id=ids["request_id"],
            correlation_id=ids["correlation_id"],
        )
    ]


def emit_week() -> list[EvidenceRecord]:
    ids = _stable_ids("week")
    fields = {
        **ids,
        "workflow": "canonical_week_brief",
        "report_type": "weekly_forecast",
        "week_brief_fallback_mode": False,
        "chunk_parse_degraded": False,
        "factor_count": 5,
        "week_brief_confidence_bucket": "high",
    }
    _emit_grace_event(
        "report.workflow.generation_start",
        flow="week",
        block="WEEK_GENERATION_START",
        **fields,
    )
    _emit_grace_event(
        "week_brief_built",
        flow="week",
        block="WEEK_BRIEF_BUILT",
        **fields,
    )
    _emit_grace_event(
        "week_brief.response_returned",
        flow="week",
        block="WEEK_RESPONSE_RETURNED",
        **fields,
    )
    return [
        EvidenceRecord(
            flow="week",
            event="week_brief.response_returned",
            log_path=LOG_DIR / "report.jsonl",
            trace_id=ids["trace_id"],
            request_id=ids["request_id"],
            correlation_id=ids["correlation_id"],
            report_id=ids["report_id"],
        )
    ]


def emit_admin() -> list[EvidenceRecord]:
    ids = _stable_ids("admin")
    _emit_grace_event(
        "admin.entry",
        flow="admin",
        block="ADMIN_SECTION_DETAIL",
        stage="section_detail",
        admin_user_id="canonical-evidence-admin",
        section_id="canonical-evidence-section",
        **ids,
    )
    return [
        EvidenceRecord(
            flow="admin",
            event="admin.entry",
            log_path=LOG_DIR / "admin.jsonl",
            trace_id=ids["trace_id"],
            request_id=ids["request_id"],
            correlation_id=ids["correlation_id"],
            report_id=ids["report_id"],
        )
    ]


def emit_catalog() -> list[EvidenceRecord]:
    ids = _stable_ids("catalog")
    log_catalog_event(
        "catalog.history_success",
        correlation_id=ids["correlation_id"],
        trace_id=ids["trace_id"],
        correlation_source="canonical_evidence_generation",
        request_id=ids["request_id"],
        canonical_evidence=True,
        canonical_flow="catalog",
        evidence_producer="scripts/generate_canonical_evidence.py",
        user_id="canonical-evidence-user",
        user_telegram_id="canonical-evidence-telegram",
        report_id=ids["report_id"],
        report_type="natal_master",
        surface="history",
        status="success",
    )
    return [
        EvidenceRecord(
            flow="catalog",
            event="catalog.history_success",
            log_path=LOG_DIR / "catalog.jsonl",
            trace_id=ids["trace_id"],
            request_id=ids["request_id"],
            correlation_id=ids["correlation_id"],
            report_id=ids["report_id"],
        )
    ]


EMITTERS: dict[str, Callable[[], list[EvidenceRecord]]] = {
    "today": emit_today,
    "week": emit_week,
    "admin": emit_admin,
    "catalog": emit_catalog,
}


def parse_flows(value: str) -> list[str]:
    raw_flows = [item.strip().lower() for item in value.split(",") if item.strip()]
    unknown = sorted(set(raw_flows) - FLOW_SET)
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown flow(s): {', '.join(unknown)}")
    seen: set[str] = set()
    flows = [flow for flow in raw_flows if not (flow in seen or seen.add(flow))]
    return flows or list(FLOW_ORDER)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit fresh canonical Today, Week, Admin, and Catalog dev/test evidence through backend logging contracts."
    )
    parser.add_argument(
        "--flows",
        type=parse_flows,
        default=list(FLOW_ORDER),
        help="Comma-separated flows to emit: today,week,admin,catalog. Defaults to all.",
    )
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=30,
        help="Review freshness window this evidence is intended to satisfy.",
    )
    args = parser.parse_args(argv)
    if args.window_minutes <= 0:
        parser.error("--window-minutes must be > 0")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    configure_structlog()
    emitted: list[EvidenceRecord] = []
    for flow in args.flows:
        emitted.extend(EMITTERS[flow]())

    payload = {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_minutes": args.window_minutes,
        "log_dir": str(LOG_DIR),
        "flows": [record.to_dict() for record in emitted],
        "review_commands": [
            "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md",
            "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md",
            "python3 tools/log_watch/feed_admin_watch.py --feed-log logs/feed.jsonl --admin-log logs/admin.jsonl --window-minutes 30 --limit 200",
            "python3 tools/log_watch/forecast_catalog_watch.py --catalog-log logs/catalog.jsonl --window-minutes 30 --limit 200",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
