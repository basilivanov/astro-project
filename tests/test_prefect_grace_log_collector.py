"""Tests for bounded GRACE log collector."""

from __future__ import annotations

import json

from prefect_grace.platform.log_collector import LogCollector


def test_log_collector_writes_jsonl(tmp_path):
    """Collector appends one JSON object per line."""
    collector = LogCollector(artifact_root=tmp_path, packet_id="PACKET-1")

    assert collector.collect({"event": "one"}) is True
    assert collector.collect({"event": "two"}) is True

    rows = [json.loads(line) for line in collector.path.read_text(encoding="utf-8").splitlines()]
    assert rows == [{"event": "one"}, {"event": "two"}]
    assert collector.event_count == 2
    assert collector.flush() is True


def test_log_collector_enforces_event_limit(tmp_path):
    """Collector drops events beyond the configured bound."""
    collector = LogCollector(artifact_root=tmp_path, packet_id="PACKET-1", max_events=2)

    assert collector.collect({"event": "one"}) is True
    assert collector.collect({"event": "two"}) is True
    assert collector.collect({"event": "three"}) is False

    rows = collector.path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    assert collector.event_count == 2
    assert collector.dropped_count == 1


def test_log_collector_is_fail_safe_for_bad_artifact_root(tmp_path):
    """Filesystem write failures are captured and do not raise."""
    bad_root = tmp_path / "not-a-directory"
    bad_root.write_text("file blocks directory creation", encoding="utf-8")
    collector = LogCollector(artifact_root=bad_root, packet_id="PACKET-1")

    assert collector.collect({"event": "one"}) is False
    assert collector.failures
