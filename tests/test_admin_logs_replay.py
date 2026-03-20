import json
import subprocess
import tempfile
from pathlib import Path


def test_admin_logs_replay_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "admin.jsonl"
        log_path.write_text(
            "\n".join(
                [
                    json.dumps({"event": "admin.queue", "report_id": "r-1", "report_type": "natal_master", "stage": "initialized", "pending": 3, "running": 0, "error": 0}),
                    json.dumps({"event": "admin.section_regenerate", "report_id": "r-1", "section_id": "core_signature", "stage": "queued"}),
                    json.dumps({"event": "admin.error", "report_id": "r-1", "section_id": "core_signature", "stage": "fallback_applied", "fallback": True}),
                    json.dumps({"event": "admin.entitlement_grant", "report_id": "r-1", "report_type": "natal_master", "action": "created", "entitlement_id": "ent-1"}),
                ]
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            ["python3", "tools/admin_logs/replay_last.py", str(log_path), "50"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        assert payload["report_id"] == "r-1"
        assert payload["report_type"] == "natal_master"
        assert payload["queue"]["pending"] == 3
        assert "core_signature" in payload["sections"]
        assert payload["fallback"] == ["core_signature"]
        assert payload["entitlement_actions"][0]["action"] == "created"
