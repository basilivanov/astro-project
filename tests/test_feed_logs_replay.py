import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestFeedLogsReplay(unittest.TestCase):
    def test_replay_last_summarizes_latest_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "feed.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"event": "feed.entry", "stage": "request_start", "path": "/api/feed/today", "has_auth_header": True}),
                        json.dumps({"event": "feed.debug", "stage": "auth_fallback", "path": "/api/feed/today", "auth_mode": "fallback_anonymous", "reason": "telegram_auth_invalid"}),
                        json.dumps({"event": "feed.entry", "stage": "facts_start", "timezone": "Europe/Moscow", "location": "Sochi"}),
                        json.dumps({"event": "feed.debug", "stage": "facts_built", "cache_scope": "scope-1", "personalization_level": "profile_light", "fallback_mode": True, "prompt_path": "personalized_daily_v2"}),
                        json.dumps({"event": "feed.error", "stage": "fallback_path", "cache_scope": "scope-1", "fallback_reason": "endpoint_error"}),
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                ["python3", str(Path(__file__).resolve().parents[1] / "tools" / "feed_logs" / "replay_last.py"), str(log_path)],
                cwd=str(Path(__file__).resolve().parents[1]),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["personalization_level"], "profile_light")
            self.assertEqual(payload["prompt_path"], "personalized_daily_v2")
            self.assertTrue(payload["fallback"])
            self.assertEqual(payload["fallback_reason"], "endpoint_error")


if __name__ == "__main__":
    unittest.main()
