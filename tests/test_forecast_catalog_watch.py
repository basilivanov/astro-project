import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import tools.log_watch.forecast_catalog_watch as forecast_catalog_watch
from tools.log_watch.forecast_catalog_watch import (
    CATALOG_ALLOWED_EVENTS,
    FlowConfig,
    _analyze_flow,
    _success_predicate,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def test_analyze_flow_captures_success_and_error_details():
    now = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)
    window = timedelta(minutes=30)
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "catalog.jsonl"
        _write_jsonl(
            log_path,
            [
                {"event": "catalog.history_start", "timestamp": "2026-03-21T11:20:00+00:00"},
                {
                    "event": "catalog.history_success",
                    "timestamp": "2026-03-21T11:25:00+00:00",
                    "user_id": "user-1",
                    "report_id": "rep-1",
                    "surface": "history",
                },
                {
                    "event": "catalog.checkout_status",
                    "timestamp": "2026-03-21T11:40:00+00:00",
                    "status": "failed",
                    "checkout_session_id": "sess-1",
                    "surface": "billing",
                },
                {
                    "event": "catalog.checkout_resume_ready",
                    "timestamp": "2026-03-21T11:45:00+00:00",
                    "checkout_session_id": "sess-1",
                    "surface": "billing",
                },
            ],
        )

        config = FlowConfig(
            flow_id="FLOW-FORECAST-CATALOG",
            label="CATALOG",
            log_path=log_path,
            allowed_events=CATALOG_ALLOWED_EVENTS,
            success_predicate=_success_predicate,
        )
        status = _analyze_flow(config, now, window, 200)

        assert status.last_success_event == "catalog.checkout_resume_ready"
        assert status.success_context["checkout_session_id"] == "sess-1"
        assert status.last_error_event is None
        assert not any("last error" in alert for alert in status.alerts)
        assert not any("no success" in alert for alert in status.alerts)
        payload = status.to_dict(now, window)
        assert payload["freshness_age_minutes"] == 15
        assert payload["success_fresh"] is True
        assert payload["stale_success"] is False


def test_analyze_flow_alerts_when_no_success_events():
    now = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)
    window = timedelta(minutes=30)
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "catalog.jsonl"
        _write_jsonl(
            log_path,
            [
                {"event": "catalog.history_start", "timestamp": "2026-03-21T11:20:00+00:00"},
                {
                    "event": "catalog.checkout_status",
                    "timestamp": "2026-03-21T11:25:00+00:00",
                    "status": "failed",
                    "checkout_session_id": "sess-err",
                },
            ],
        )

        config = FlowConfig(
            flow_id="FLOW-FORECAST-CATALOG",
            label="CATALOG",
            log_path=log_path,
            allowed_events=CATALOG_ALLOWED_EVENTS,
            success_predicate=_success_predicate,
        )
        status = _analyze_flow(config, now, window, 200)

        assert status.last_success_event is None
        assert any("no success events" in alert for alert in status.alerts)


def test_analyze_flow_clears_hard_error_when_later_success_exists():
    now = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)
    window = timedelta(minutes=30)
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "catalog.jsonl"
        _write_jsonl(
            log_path,
            [
                {
                    "event": "catalog.error",
                    "timestamp": "2026-03-21T11:40:00+00:00",
                    "surface": "checkout",
                    "error": "provider timeout",
                },
                {
                    "event": "catalog.history_success",
                    "timestamp": "2026-03-21T11:45:00+00:00",
                    "user_id": "user-2",
                    "report_id": "rep-2",
                    "surface": "report_detail",
                },
            ],
        )

        config = FlowConfig(
            flow_id="FLOW-FORECAST-CATALOG",
            label="CATALOG",
            log_path=log_path,
            allowed_events=CATALOG_ALLOWED_EVENTS,
            success_predicate=_success_predicate,
        )
        status = _analyze_flow(config, now, window, 200)

        assert status.last_error_event == "catalog.error"
        assert status.last_success_event == "catalog.history_success"
        assert not any("last error" in alert for alert in status.alerts)


def test_cli_outputs_summary_and_exit_code():
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "catalog.jsonl"
        _write_jsonl(
            log_path,
            [
                {
                    "event": "catalog.history_success",
                    "timestamp": "2026-03-21T10:00:00+00:00",
                    "user_id": "user-42",
                }
            ],
        )

        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)
        result = subprocess.run(
            [
                "python3",
                "tools/log_watch/forecast_catalog_watch.py",
                "--catalog-log",
                str(log_path),
                "--window-minutes",
                "30",
                "--now",
                "2026-03-21T12:30:00+00:00",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["alerts"]
        flow = payload["flows"][0]
        assert flow["flow_id"] == "FLOW-FORECAST-CATALOG"
        assert flow["last_success_event"] == "catalog.history_success"
        assert flow["freshness_age_minutes"] == 150
        assert flow["stale_success"] is True


def test_analyze_flow_distinguishes_stale_success_from_missing_log():
    now = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)
    window = timedelta(minutes=30)
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "catalog.jsonl"
        _write_jsonl(
            log_path,
            [
                {
                    "event": "catalog.history_success",
                    "timestamp": "2026-03-21T11:00:00+00:00",
                    "user_id": "user-stale",
                    "report_id": "rep-stale",
                }
            ],
        )

        stale_status = _analyze_flow(
            FlowConfig(
                flow_id="FLOW-FORECAST-CATALOG",
                label="CATALOG",
                log_path=log_path,
                allowed_events=CATALOG_ALLOWED_EVENTS,
                success_predicate=_success_predicate,
            ),
            now,
            window,
            200,
        )
        missing_status = _analyze_flow(
            FlowConfig(
                flow_id="FLOW-FORECAST-CATALOG",
                label="CATALOG",
                log_path=Path(tmpdir) / "missing-catalog.jsonl",
                allowed_events=CATALOG_ALLOWED_EVENTS,
                success_predicate=_success_predicate,
            ),
            now,
            window,
            200,
        )

        stale_payload = stale_status.to_dict(now, window)
        assert stale_payload["last_success_event"] == "catalog.history_success"
        assert stale_payload["freshness_age_minutes"] == 60
        assert stale_payload["success_fresh"] is False
        assert stale_payload["stale_success"] is True
        assert "missing_log" not in stale_payload
        assert any("older than 30 minutes" in alert for alert in stale_status.alerts)

        missing_payload = missing_status.to_dict(now, window)
        assert missing_payload["missing_log"] is True
        assert missing_payload["freshness_age_minutes"] is None
        assert missing_payload["success_fresh"] is None
        assert missing_payload["stale_success"] is False


def test_analyze_flow_reports_newer_error_after_success_with_context():
    now = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)
    window = timedelta(minutes=30)
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "catalog.jsonl"
        _write_jsonl(
            log_path,
            [
                {
                    "event": "catalog.history_success",
                    "timestamp": "2026-03-21T11:40:00+00:00",
                    "user_id": "user-3",
                    "report_id": "rep-3",
                },
                {
                    "event": "catalog.error",
                    "timestamp": "2026-03-21T11:45:00+00:00",
                    "surface": "checkout",
                    "checkout_session_id": "sess-error",
                    "error": "provider timeout",
                },
            ],
        )

        status = _analyze_flow(
            FlowConfig(
                flow_id="FLOW-FORECAST-CATALOG",
                label="CATALOG",
                log_path=log_path,
                allowed_events=CATALOG_ALLOWED_EVENTS,
                success_predicate=_success_predicate,
            ),
            now,
            window,
            200,
        )

        payload = status.to_dict(now, window)
        assert payload["last_success_event"] == "catalog.history_success"
        assert payload["last_error_event"] == "catalog.error"
        assert payload["last_error_context"]["checkout_session_id"] == "sess-error"
        assert any("last error catalog.error" in alert for alert in status.alerts)


def test_analyze_flow_marks_unreadable_log():
    now = datetime(2026, 3, 21, 12, 0, tzinfo=timezone.utc)
    window = timedelta(minutes=30)
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "catalog.jsonl"
        _write_jsonl(log_path, [{"event": "catalog.history_success"}])

        with patch.object(forecast_catalog_watch, "load_records", side_effect=OSError("permission denied")):
            status = _analyze_flow(
                FlowConfig(
                    flow_id="FLOW-FORECAST-CATALOG",
                    label="CATALOG",
                    log_path=log_path,
                    allowed_events=CATALOG_ALLOWED_EVENTS,
                    success_predicate=_success_predicate,
                ),
                now,
                window,
                200,
            )

        payload = status.to_dict(now, window)
        assert payload["unreadable_log"] is True
        assert payload["freshness_age_minutes"] is None
        assert any("unable to read" in alert for alert in status.alerts)
