from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from prefect_grace.tasks.codex_launcher import (
    _extract_last_stdout_event,
    _format_heartbeat_message,
    _heartbeat_loop,
    _heartbeat_payload,
)


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(self.format(record))


def test_extract_last_stdout_event_reads_latest_jsonl_event(tmp_path: Path) -> None:
    stdout_path = tmp_path / "stdout.jsonl"
    stdout_path.write_text(
        "not-json\n"
        + json.dumps({"type": "item.started", "item": {"status": "in_progress"}})
        + "\n"
        + json.dumps({"type": "item.completed", "item": {"status": "completed"}})
        + "\n",
        encoding="utf-8",
    )

    event = _extract_last_stdout_event(stdout_path)

    assert event == {"event_type": "item.completed", "status": "completed"}


def test_format_heartbeat_message_contains_run_paths(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    stdout_path = run_dir / "stdout.jsonl"
    stdout_path.write_text(json.dumps({"type": "item.completed", "item": {"status": "completed"}}) + "\n", encoding="utf-8")
    process = SimpleNamespace(pid=12345)

    payload = _heartbeat_payload(run_dir=run_dir, stdout_path=stdout_path, process=process)
    message = _format_heartbeat_message("PKT-1", payload)

    assert "PKT-1" in message
    assert str(run_dir) in message
    assert str(stdout_path) in message
    assert "item.completed/completed" in message


def test_heartbeat_loop_logs_progress_until_stop(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    stdout_path = run_dir / "stdout.jsonl"
    stdout_path.write_text(json.dumps({"type": "item.started", "item": {"status": "in_progress"}}) + "\n", encoding="utf-8")
    handler = _ListHandler()
    logger = logging.getLogger("test_prefect_grace_codex_launcher")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    process = SimpleNamespace(pid=999, poll=lambda: None)
    stop_event = threading.Event()

    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(process,),
        kwargs={
            "packet_id": "PKT-2",
            "run_dir": run_dir,
            "stdout_path": stdout_path,
            "logger": logger,
            "interval_seconds": 0.01,
            "stop_event": stop_event,
        },
        daemon=True,
    )
    thread.start()
    time.sleep(0.05)
    stop_event.set()
    thread.join(timeout=1)

    assert any("Codex heartbeat packet=PKT-2" in message for message in handler.messages)
