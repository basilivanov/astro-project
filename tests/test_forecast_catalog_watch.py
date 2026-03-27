import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
        assert status.last_error_event == "catalog.checkout_status"
        assert any("last error" in alert for alert in status.alerts)
        assert not any("no success" in alert for alert in status.alerts)


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
