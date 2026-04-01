from __future__ import annotations

import json
from pathlib import Path
from datetime import timedelta

from tools.post_test_review import analyze_today, analyze_week
from tools.post_test_review import build_output


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


def test_post_test_review_includes_rendered_summaries_without_overriding_log_verdict(tmp_path: Path) -> None:
    feed_log = tmp_path / "feed.jsonl"
    report_log = tmp_path / "report.jsonl"
    feed_log.write_text("", encoding="utf-8")
    report_log.write_text("", encoding="utf-8")

    today = analyze_today(feed_log, since_delta=timedelta(days=1), limit=20)
    week = analyze_week(report_log, since_delta=timedelta(days=1), limit=20)
    payload = build_output(
        profile="today-week",
        since="1440m",
        feed_log=feed_log,
        report_log=report_log,
        today=today,
        week=week,
        rendered_summaries=[
            {
                "flow_id": "FLOW-TODAY-PREMIUM",
                "surface": "today",
                "scenario_id": "today_rendered_wave1_site_web",
                "pass_mode": {"key": "site_web", "channel": "web", "path": "/"},
                "status": "passed",
                "assertion_class": "rendered_hygiene",
                "artifact_refs": ["dom://today-verdict"],
                "details": {"route": "/"},
                "recorded_at": "2026-04-02T09:00:00+00:00",
            }
        ],
    )

    assert payload["verdict"] == "FAIL_NO_EVIDENCE"
    today_flow = payload["flows"][0]
    assert today_flow["rendered_summaries"][0]["scenario_id"] == "today_rendered_wave1_site_web"
    assert "rendered summaries present without canonical logs" in today_flow["alerts"]


def test_post_test_review_keeps_multiple_pass_modes_additive(tmp_path: Path) -> None:
    feed_log = tmp_path / "feed.jsonl"
    report_log = tmp_path / "report.jsonl"
    feed_log.write_text("", encoding="utf-8")
    report_log.write_text("", encoding="utf-8")

    payload = build_output(
        profile="today-week",
        since="1440m",
        feed_log=feed_log,
        report_log=report_log,
        today=analyze_today(feed_log, since_delta=timedelta(days=1), limit=20),
        week=analyze_week(report_log, since_delta=timedelta(days=1), limit=20),
        rendered_summaries=[
            {
                "flow_id": "FLOW-TODAY-PREMIUM",
                "surface": "today",
                "scenario_id": "today_rendered_wave1_site_web",
                "pass_mode": {"key": "site_web", "channel": "web", "path": "/"},
                "status": "passed",
                "assertion_class": "rendered_hygiene",
                "artifact_refs": ["dom://today-verdict"],
                "details": {"route": "/"},
                "recorded_at": "2026-04-02T09:00:00+00:00",
            },
            {
                "flow_id": "FLOW-TODAY-PREMIUM",
                "surface": "today",
                "scenario_id": "today_rendered_wave1_telegram_webapp",
                "pass_mode": {"key": "telegram_webapp", "channel": "telegram", "path": "webapp"},
                "status": "passed",
                "assertion_class": "rendered_harness",
                "artifact_refs": ["telegram://webapp"],
                "details": {"parity": {"parity_status": "pilot_same_assertion_surface"}},
                "recorded_at": "2026-04-02T09:01:00+00:00",
            },
        ],
    )

    today_flow = payload["flows"][0]
    assert payload["verdict"] == "FAIL_NO_EVIDENCE"
    assert [item["pass_mode"]["key"] for item in today_flow["rendered_summaries"]] == ["site_web", "telegram_webapp"]


def test_post_test_review_exposes_rendered_presence_and_verdict_notes(tmp_path: Path) -> None:
    feed_log = tmp_path / "feed.jsonl"
    report_log = tmp_path / "report.jsonl"
    _write_jsonl(
        feed_log,
        [
            {"timestamp": "2026-04-01T10:00:00+00:00", "event": "feed.entry", "trace_id": "trace-1", "correlation_id": "corr-1"},
            {"timestamp": "2026-04-01T10:00:10+00:00", "event": "day_brief.response_returned", "fallback_mode": False, "factor_count": 4, "trace_id": "trace-1", "correlation_id": "corr-1"},
        ],
    )
    report_log.write_text("", encoding="utf-8")

    payload = build_output(
        profile="today-week",
        since="1440m",
        feed_log=feed_log,
        report_log=report_log,
        today=analyze_today(feed_log, since_delta=timedelta(days=1), limit=20),
        week=analyze_week(report_log, since_delta=timedelta(days=1), limit=20),
        rendered_summaries=[
            {
                "flow_id": "FLOW-TODAY-PREMIUM",
                "surface": "today",
                "scenario_id": "today_rendered_wave1_site_web",
                "pass_mode": {"key": "site_web", "channel": "web", "path": "/"},
                "status": "passed",
                "assertion_class": "rendered_hygiene",
                "artifact_refs": ["dom://today-verdict"],
                "details": {"route": "/"},
                "recorded_at": "2026-04-02T09:00:00+00:00",
            },
            {
                "flow_id": "FLOW-TODAY-PREMIUM",
                "surface": "today",
                "scenario_id": "today_rendered_wave1_telegram_webapp",
                "pass_mode": {"key": "telegram_webapp", "channel": "telegram", "path": "webapp"},
                "status": "passed",
                "assertion_class": "rendered_harness",
                "artifact_refs": ["telegram://webapp"],
                "details": {"parity": {"parity_status": "pilot_same_assertion_surface", "notes": ["Today pilot keeps same assertions across site/web and telegram"], "invariant_groups": ["today.verdict"]}},
                "recorded_at": "2026-04-02T09:01:00+00:00",
            },
            {
                "flow_id": "FLOW-TODAY-PREMIUM",
                "surface": "today",
                "scenario_id": "today_rendered_wave1_both",
                "pass_mode": {"key": "both", "channel": "multi", "path": "site_web+telegram_webapp"},
                "status": "passed",
                "assertion_class": "rendered_parity",
                "artifact_refs": ["dom://today-verdict", "telegram://webapp"],
                "details": {"parity": {"parity_status": "pilot_dom_model_invariants", "notes": ["Today both/pass pilot materializes shared DOM/UI-model invariants"], "invariant_groups": ["today.verdict", "today.score_details"]}},
                "recorded_at": "2026-04-02T09:02:00+00:00",
            },
        ],
    )

    today_flow = payload["flows"][0]
    assert payload["verdict"] == "FAIL_NO_EVIDENCE"
    assert today_flow["rendered_presence"] == {
        "summary_count": 3,
        "pass_modes": ["both", "site_web", "telegram_webapp"],
        "site_web_present": True,
        "telegram_webapp_present": True,
        "both_present": True,
        "parity_present": True,
        "parity_statuses": ["pilot_dom_model_invariants", "pilot_same_assertion_surface"],
        "parity_notes": [
            "Today both/pass pilot materializes shared DOM/UI-model invariants",
            "Today pilot keeps same assertions across site/web and telegram",
        ],
        "invariant_groups": ["today.score_details", "today.verdict"],
        "assertion_classes": ["rendered_harness", "rendered_hygiene", "rendered_parity"],
        "statuses": ["passed"],
    }
    assert "rendered evidence is additive and does not replace canonical logs/traces" in today_flow["rendered_verdict_notes"]
    assert "canonical evidence clean; rendered evidence attached as supporting slice" in today_flow["rendered_verdict_notes"]
    assert "rendered parity metadata detected" in today_flow["rendered_verdict_notes"]
    assert "rendered both/pass pilot semantics materialized without replacing wrapper verdict model" in today_flow["rendered_verdict_notes"]
