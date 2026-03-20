import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
            self.assertEqual(admin_status.alerts, [])
            self.assertEqual(admin_status.last_success_event, "admin.entry")

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


if __name__ == "__main__":
    unittest.main()
