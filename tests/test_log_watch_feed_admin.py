import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import tools.log_watch.feed_admin_watch as feed_admin_watch
from tools.log_watch.feed_admin_watch import (
    FlowConfig,
    _admin_success,
    _analyze_flow,
    _feed_success,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


class TestLogWatchFeedAdmin(unittest.TestCase):
    def test_analyze_flow_healthy(self):
        now = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)
        window = timedelta(minutes=30)
        with tempfile.TemporaryDirectory() as tmpdir:
            feed_log = Path(tmpdir) / "feed.jsonl"
            admin_log = Path(tmpdir) / "admin.jsonl"
            _write_jsonl(
                feed_log,
                [
                    {"event": "feed.entry", "stage": "request_start", "timestamp": "2026-03-20T11:45:00+00:00"},
                    {"event": "feed.debug", "stage": "request_success", "timestamp": "2026-03-20T11:50:00+00:00"},
                ],
            )
            _write_jsonl(
                admin_log,
                [
                    {"event": "admin.queue", "stage": "list", "timestamp": "2026-03-20T11:40:00+00:00"},
                    {"event": "admin.entry", "stage": "detail", "timestamp": "2026-03-20T11:55:00+00:00"},
                ],
            )

            feed_status = _analyze_flow(
                FlowConfig(
                    flow_id="FLOW-DAILY-FEED",
                    label="FEED",
                    log_path=feed_log,
                    allowed_events={"feed.entry", "feed.debug", "feed.error"},
                    error_events={"feed.error"},
                    success_predicate=_feed_success,
                ),
                now,
                window,
                200,
            )
            admin_status = _analyze_flow(
                FlowConfig(
                    flow_id="FLOW-ADMIN-OPS",
                    label="ADMIN",
                    log_path=admin_log,
                    allowed_events={
                        "admin.entry",
                        "admin.queue",
                        "admin.section_regenerate",
                        "admin.export",
                        "admin.error",
                        "admin.entitlement_grant",
                    },
                    error_events={"admin.error"},
                    success_predicate=_admin_success,
                ),
                now,
                window,
                200,
            )

            self.assertEqual(feed_status.alerts, [])
            self.assertEqual(feed_status.last_success_event, "feed.debug")
            feed_payload = feed_status.to_dict(now, window)
            self.assertEqual(feed_payload["freshness_age_minutes"], 10)
            self.assertFalse(feed_payload["stale_success"])
            self.assertTrue(feed_payload["success_fresh"])
            self.assertEqual(admin_status.alerts, [])
            self.assertEqual(admin_status.last_success_event, "admin.entry")
            admin_payload = admin_status.to_dict(now, window)
            self.assertEqual(admin_payload["freshness_age_minutes"], 5)
            self.assertFalse(admin_payload["stale_success"])

    def test_main_detects_alerts_and_sets_exit_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feed_log = Path(tmpdir) / "feed.jsonl"
            admin_log = Path(tmpdir) / "admin.jsonl"
            _write_jsonl(
                feed_log,
                [
                    {"event": "feed.debug", "stage": "request_success", "timestamp": "2026-03-20T11:00:00+00:00"},
                    {"event": "feed.error", "stage": "fallback_path", "timestamp": "2026-03-20T12:40:00+00:00"},
                ],
            )
            _write_jsonl(
                admin_log,
                [
                    {"event": "admin.queue", "stage": "list", "timestamp": "2026-03-20T12:20:00+00:00"},
                    {"event": "admin.error", "stage": "detail_missing", "timestamp": "2026-03-20T12:25:00+00:00"},
                ],
            )

            result = subprocess.run(
                [
                    "python3",
                    "tools/log_watch/feed_admin_watch.py",
                    "--feed-log",
                    str(feed_log),
                    "--admin-log",
                    str(admin_log),
                    "--window-minutes",
                    "30",
                    "--now",
                    "2026-03-20T13:00:00+00:00",
                ],
                cwd=str(Path(__file__).resolve().parents[1]),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["alerts"])  # Combined alert list
            feed_alerts = [alert for alert in payload["alerts"] if "FLOW-DAILY-FEED" in alert]
            admin_alerts = [alert for alert in payload["alerts"] if "FLOW-ADMIN-OPS" in alert]
            self.assertTrue(any("feed.error" in alert for alert in feed_alerts))
            self.assertTrue(any("no success" in alert or "older than" in alert for alert in feed_alerts))
            self.assertTrue(any("ADMIN" in alert or "FLOW-ADMIN-OPS" in alert for alert in admin_alerts))

    def test_analyze_flow_distinguishes_stale_success_from_missing_log(self):
        now = datetime(2026, 3, 20, 13, 0, tzinfo=timezone.utc)
        window = timedelta(minutes=30)
        with tempfile.TemporaryDirectory() as tmpdir:
            admin_log = Path(tmpdir) / "admin.jsonl"
            _write_jsonl(
                admin_log,
                [
                    {"event": "admin.entry", "stage": "detail", "timestamp": "2026-03-20T12:00:00+00:00"},
                ],
            )

            stale_status = _analyze_flow(
                FlowConfig(
                    flow_id="FLOW-ADMIN-OPS",
                    label="ADMIN",
                    log_path=admin_log,
                    allowed_events={"admin.entry", "admin.error"},
                    error_events={"admin.error"},
                    success_predicate=_admin_success,
                ),
                now,
                window,
                200,
            )
            missing_status = _analyze_flow(
                FlowConfig(
                    flow_id="FLOW-ADMIN-OPS",
                    label="ADMIN",
                    log_path=Path(tmpdir) / "missing-admin.jsonl",
                    allowed_events={"admin.entry", "admin.error"},
                    error_events={"admin.error"},
                    success_predicate=_admin_success,
                ),
                now,
                window,
                200,
            )

            stale_payload = stale_status.to_dict(now, window)
            self.assertEqual(stale_payload["last_success_event"], "admin.entry")
            self.assertEqual(stale_payload["freshness_age_minutes"], 60)
            self.assertTrue(stale_payload["stale_success"])
            self.assertFalse(stale_payload["success_fresh"])
            self.assertNotIn("missing_log", stale_payload)
            self.assertTrue(any("older than 30 minutes" in alert for alert in stale_status.alerts))

            missing_payload = missing_status.to_dict(now, window)
            self.assertTrue(missing_payload["missing_log"])
            self.assertIsNone(missing_payload["freshness_age_minutes"])
            self.assertIsNone(missing_payload["success_fresh"])
            self.assertFalse(missing_payload["stale_success"])

    def test_analyze_flow_reports_newer_error_after_success(self):
        now = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)
        window = timedelta(minutes=30)
        with tempfile.TemporaryDirectory() as tmpdir:
            admin_log = Path(tmpdir) / "admin.jsonl"
            _write_jsonl(
                admin_log,
                [
                    {"event": "admin.entry", "stage": "detail", "timestamp": "2026-03-20T11:45:00+00:00"},
                    {"event": "admin.error", "stage": "export_failed", "timestamp": "2026-03-20T11:50:00+00:00"},
                ],
            )

            status = _analyze_flow(
                FlowConfig(
                    flow_id="FLOW-ADMIN-OPS",
                    label="ADMIN",
                    log_path=admin_log,
                    allowed_events={"admin.entry", "admin.error"},
                    error_events={"admin.error"},
                    success_predicate=_admin_success,
                ),
                now,
                window,
                200,
            )

            payload = status.to_dict(now, window)
            self.assertEqual(payload["last_success_event"], "admin.entry")
            self.assertEqual(payload["last_error_event"], "admin.error")
            self.assertEqual(payload["last_error_stage"], "export_failed")
            self.assertTrue(any("newer than last success" in alert for alert in status.alerts))

    def test_analyze_flow_marks_unreadable_log(self):
        now = datetime(2026, 3, 20, 12, 0, tzinfo=timezone.utc)
        window = timedelta(minutes=30)
        with tempfile.TemporaryDirectory() as tmpdir:
            admin_log = Path(tmpdir) / "admin.jsonl"
            _write_jsonl(admin_log, [{"event": "admin.entry", "stage": "detail"}])

            with patch.object(feed_admin_watch, "_load_records", side_effect=OSError("permission denied")):
                status = _analyze_flow(
                    FlowConfig(
                        flow_id="FLOW-ADMIN-OPS",
                        label="ADMIN",
                        log_path=admin_log,
                        allowed_events={"admin.entry", "admin.error"},
                        error_events={"admin.error"},
                        success_predicate=_admin_success,
                    ),
                    now,
                    window,
                    200,
                )

            payload = status.to_dict(now, window)
            self.assertTrue(payload["unreadable_log"])
            self.assertIsNone(payload["freshness_age_minutes"])
            self.assertTrue(any("unable to read" in alert for alert in status.alerts))


if __name__ == "__main__":
    unittest.main()
