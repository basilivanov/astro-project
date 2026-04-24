from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str], *, log_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ASTRO_LOG_DIR"] = str(log_dir)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _last_jsonl_record(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    return rows[-1]


def test_generate_canonical_evidence_emits_all_flow_logs(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"

    result = _run(
        [
            "python3",
            "scripts/generate_canonical_evidence.py",
            "--flows",
            "today,week,admin,catalog",
            "--window-minutes",
            "30",
        ],
        log_dir=log_dir,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert {flow["flow"] for flow in payload["flows"]} == {"today", "week", "admin", "catalog"}
    assert "tools/post_test_review.py --profile today-week" in "\n".join(payload["review_commands"])

    feed_record = _last_jsonl_record(log_dir / "feed.jsonl")
    assert feed_record["event"] == "day_brief.response_returned"
    assert feed_record["canonical_evidence"] is True
    assert feed_record["fallback_mode"] is False
    assert feed_record["trace_id"]
    assert feed_record["request_id"]
    assert feed_record["correlation_id"]

    report_record = _last_jsonl_record(log_dir / "report.jsonl")
    assert report_record["event"] == "week_brief.response_returned"
    assert report_record["chunk_parse_degraded"] is False
    assert report_record["report_id"]

    admin_record = _last_jsonl_record(log_dir / "admin.jsonl")
    assert admin_record["event"] == "admin.entry"
    assert admin_record["stage"] == "section_detail"
    assert admin_record["request_id"]

    catalog_record = _last_jsonl_record(log_dir / "catalog.jsonl")
    assert catalog_record["event"] == "catalog.history_success"
    assert catalog_record["surface"] == "history"
    assert catalog_record["status"] == "success"
    assert catalog_record["report_id"]


def test_generated_evidence_satisfies_review_and_watchers(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    generate = _run(["python3", "scripts/generate_canonical_evidence.py"], log_dir=log_dir)
    assert generate.returncode == 0, generate.stderr

    today_week = _run(
        [
            "python3",
            "tools/post_test_review.py",
            "--profile",
            "today-week",
            "--since",
            "30m",
            "--feed-log",
            str(log_dir / "feed.jsonl"),
            "--report-log",
            str(log_dir / "report.jsonl"),
        ],
        log_dir=log_dir,
    )
    assert today_week.returncode == 0, today_week.stdout + today_week.stderr
    today_week_payload = json.loads(today_week.stdout)
    assert today_week_payload["verdict"] == "PASS_CLEAN"

    read_only = _run(
        [
            "python3",
            "tools/post_test_review.py",
            "--profile",
            "read-only",
            "--since",
            "30m",
            "--feed-log",
            str(log_dir / "feed.jsonl"),
            "--report-log",
            str(log_dir / "report.jsonl"),
        ],
        log_dir=log_dir,
    )
    assert read_only.returncode == 0, read_only.stdout + read_only.stderr
    assert json.loads(read_only.stdout)["verdict"] in {"PASS_CLEAN", "PASS_WITH_EXPECTED_DEGRADATION"}

    feed_admin = _run(
        [
            "python3",
            "tools/log_watch/feed_admin_watch.py",
            "--feed-log",
            str(log_dir / "feed.jsonl"),
            "--admin-log",
            str(log_dir / "admin.jsonl"),
            "--window-minutes",
            "30",
            "--limit",
            "200",
        ],
        log_dir=log_dir,
    )
    assert feed_admin.returncode == 0, feed_admin.stdout + feed_admin.stderr
    feed_admin_payload = json.loads(feed_admin.stdout)
    assert feed_admin_payload["alerts"] == []
    assert {flow["flow_id"] for flow in feed_admin_payload["flows"]} == {"FLOW-DAILY-FEED", "FLOW-ADMIN-OPS"}

    catalog = _run(
        [
            "python3",
            "tools/log_watch/forecast_catalog_watch.py",
            "--catalog-log",
            str(log_dir / "catalog.jsonl"),
            "--window-minutes",
            "30",
            "--limit",
            "200",
        ],
        log_dir=log_dir,
    )
    assert catalog.returncode == 0, catalog.stdout + catalog.stderr
    catalog_payload = json.loads(catalog.stdout)
    assert catalog_payload["alerts"] == []
    assert catalog_payload["flows"][0]["flow_id"] == "FLOW-FORECAST-CATALOG"


def test_missing_evidence_still_fails_strict_review_and_watchers(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    empty_feed = log_dir / "feed.jsonl"
    empty_report = log_dir / "report.jsonl"
    empty_feed.write_text("", encoding="utf-8")
    empty_report.write_text("", encoding="utf-8")

    today_week = _run(
        [
            "python3",
            "tools/post_test_review.py",
            "--profile",
            "today-week",
            "--since",
            "30m",
            "--feed-log",
            str(empty_feed),
            "--report-log",
            str(empty_report),
        ],
        log_dir=log_dir,
    )
    assert today_week.returncode == 1
    assert json.loads(today_week.stdout)["verdict"] == "FAIL_NO_EVIDENCE"

    feed_admin = _run(
        [
            "python3",
            "tools/log_watch/feed_admin_watch.py",
            "--feed-log",
            str(log_dir / "missing-feed.jsonl"),
            "--admin-log",
            str(log_dir / "missing-admin.jsonl"),
            "--window-minutes",
            "30",
        ],
        log_dir=log_dir,
    )
    assert feed_admin.returncode == 1
    assert json.loads(feed_admin.stdout)["alerts"]

    catalog = _run(
        [
            "python3",
            "tools/log_watch/forecast_catalog_watch.py",
            "--catalog-log",
            str(log_dir / "missing-catalog.jsonl"),
            "--window-minutes",
            "30",
        ],
        log_dir=log_dir,
    )
    assert catalog.returncode == 1
    assert json.loads(catalog.stdout)["flows"][0]["missing_log"] is True
