from __future__ import annotations

import json
from pathlib import Path

from tools.post_test_review import analyze_today, analyze_week


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_post_test_review_clean_today_and_week(tmp_path: Path) -> None:
    feed = tmp_path / "feed.jsonl"
    report = tmp_path / "report.jsonl"
    _write_jsonl(
        feed,
        [
            {"timestamp": "2026-04-01T10:00:00+00:00", "event": "feed.entry", "trace_id": "trace-1", "correlation_id": "corr-1"},
            {"timestamp": "2026-04-01T10:00:10+00:00", "event": "day_brief.response_returned", "fallback_mode": False, "factor_count": 4, "trace_id": "trace-1", "correlation_id": "corr-1"},
        ],
    )
    _write_jsonl(
        report,
        [
            {"timestamp": "2026-04-01T10:05:00+00:00", "event": "week_brief.response_returned", "factor_count": 5, "trace_id": "trace-2", "correlation_id": "corr-2"},
            {"timestamp": "2026-04-01T10:05:10+00:00", "event": "week_brief_built", "week_brief_fallback_mode": False, "factor_count": 5, "trace_id": "trace-2", "correlation_id": "corr-2"},
        ],
    )

    today = analyze_today(feed, since_delta=__import__("datetime").timedelta(days=7), limit=100)
    week = analyze_week(report, since_delta=__import__("datetime").timedelta(days=7), limit=100)

    assert today.status == "clean"
    assert week.status == "clean"
    assert today.evidence
    assert week.evidence


def test_post_test_review_flags_unexpected_degradation(tmp_path: Path) -> None:
    feed = tmp_path / "feed.jsonl"
    report = tmp_path / "report.jsonl"
    _write_jsonl(
        feed,
        [
            {"timestamp": "2026-04-01T10:00:00+00:00", "event": "feed.entry", "trace_id": "trace-1", "correlation_id": "corr-1"},
            {"timestamp": "2026-04-01T10:00:10+00:00", "event": "feed.debug", "stage": "auth_fallback", "reason": "telegram_auth_invalid", "trace_id": "trace-1", "correlation_id": "corr-1"},
            {"timestamp": "2026-04-01T10:00:20+00:00", "event": "day_brief.validation_failed", "fallback_mode": True, "factor_count": 1, "trace_id": "trace-1", "correlation_id": "corr-1"},
        ],
    )
    _write_jsonl(
        report,
        [
            {"timestamp": "2026-04-01T10:05:00+00:00", "event": "week_brief_validation_failed", "trace_id": "trace-2", "correlation_id": "corr-2"},
        ],
    )

    today = analyze_today(feed, since_delta=__import__("datetime").timedelta(days=7), limit=100)
    week = analyze_week(report, since_delta=__import__("datetime").timedelta(days=7), limit=100)

    assert today.status == "unexpected-degradation"
    assert week.status == "unexpected-degradation"


def test_post_test_review_marks_expected_degradation_and_report_id(tmp_path: Path) -> None:
    report = tmp_path / "report.jsonl"
    _write_jsonl(
        report,
        [
            {
                "timestamp": "2026-04-01T10:05:00+00:00",
                "event": "week_brief_fallback_triggered",
                "trace_id": "trace-2",
                "correlation_id": "corr-2",
                "report_id": "report-2",
                "reason_codes": ["expected_degradation"],
            },
            {
                "timestamp": "2026-04-01T10:05:10+00:00",
                "event": "week_brief_built",
                "week_brief_fallback_mode": True,
                "trace_id": "trace-2",
                "correlation_id": "corr-2",
                "report_id": "report-2",
                "reason_code": "expected_degradation",
            },
        ],
    )

    week = analyze_week(report, since_delta=__import__("datetime").timedelta(days=7), limit=100)

    assert week.status == "degraded-but-expected"
    assert week.sample_report_id == "report-2"
    assert any(item.get("report_id") == "report-2" for item in week.evidence)


def test_post_test_review_marks_no_evidence_blocker(tmp_path: Path) -> None:
    today = analyze_today(tmp_path / "missing-feed.jsonl", since_delta=__import__("datetime").timedelta(days=7), limit=100)
    week = analyze_week(tmp_path / "missing-report.jsonl", since_delta=__import__("datetime").timedelta(days=7), limit=100)

    assert today.status == "no-evidence-blocker"
    assert week.status == "no-evidence-blocker"
