from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
import logging
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from prefect_grace.tasks.codex_launcher import (
    _extract_last_stdout_event,
    _extract_thread_id,
    _format_heartbeat_message,
    _heartbeat_loop,
    _heartbeat_payload,
    launch_codex_for_packet,
)
from prefect_grace.tasks import state_store


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


def test_extract_thread_id_reads_thread_started_event(tmp_path: Path) -> None:
    stdout_path = tmp_path / "stdout.jsonl"
    stdout_path.write_text(
        json.dumps({"type": "thread.started", "thread_id": "thread-123"}) + "\n"
        + json.dumps({"type": "item.completed", "item": {"status": "completed"}})
        + "\n",
        encoding="utf-8",
    )

    assert _extract_thread_id(stdout_path) == "thread-123"


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


def test_heartbeat_loop_kills_stalled_process(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    stdout_path = run_dir / "stdout.jsonl"
    stdout_path.write_text("", encoding="utf-8")
    handler = _ListHandler()
    logger = logging.getLogger("test_prefect_grace_codex_launcher_stall")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    class _Proc:
        def __init__(self) -> None:
            self.pid = 321
            self.killed = False

        def poll(self):
            return None if not self.killed else -9

        def kill(self):
            self.killed = True

    process = _Proc()
    stop_event = threading.Event()
    fake_now = datetime(2026, 4, 15, 8, 0, 0, tzinfo=timezone.utc)

    class _FakeDateTime:
        current = fake_now

        @classmethod
        def now(cls, tz=None):
            value = cls.current
            cls.current = value + timedelta(seconds=1)
            return value

    with patch("prefect_grace.tasks.codex_launcher.datetime", _FakeDateTime):
        thread = threading.Thread(
            target=_heartbeat_loop,
            args=(process,),
            kwargs={
                "packet_id": "PKT-STALL",
                "run_dir": run_dir,
                "stdout_path": stdout_path,
                "logger": logger,
                "interval_seconds": 0.01,
                "stop_event": stop_event,
                "stall_timeout_seconds": 2.0,
            },
            daemon=True,
        )
        thread.start()
        time.sleep(0.05)
        stop_event.set()
        thread.join(timeout=1)

    assert process.killed is True
    assert any("Codex stall detected packet=PKT-STALL" in message for message in handler.messages)


def test_launch_codex_for_packet_reuses_feature_role_session_for_architect(tmp_path: Path, monkeypatch) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    state_store.STATE_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", tmp_path / "packets")
    monkeypatch.setattr(
        "prefect_grace.tasks.codex_launcher.load_agent_config",
        lambda: {
            "codex": {
                "binary": "codex1",
                "workdir": str(tmp_path),
                "shared_model": "gpt-5.4",
                "roles": {
                    "architect": {
                        "reasoning": "xhigh",
                        "sandbox": "workspace-write",
                        "approval": "never",
                        "resume_strategy": "feature_role",
                    }
                },
            }
        },
    )

    feature_id = "FEAT-RESUME"
    packet_dir = (tmp_path / "packets" / feature_id)
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "feature-brief.md").write_text("# Feature brief\n", encoding="utf-8")
    packet_path = tmp_path / "architect-packet.md"
    packet_path.write_text("# Packet\n", encoding="utf-8")

    (state_store.STATE_DIR / "features.yaml").write_text(
        yaml.safe_dump({"features": [{"feature_id": feature_id, "title": "Feature"}]}, sort_keys=False),
        encoding="utf-8",
    )
    (state_store.STATE_DIR / "packets.yaml").write_text(
        yaml.safe_dump(
            {
                "packets": [
                    {
                        "packet_id": "PKT-ARCH-1",
                        "feature_id": feature_id,
                        "wave_id": "W00",
                        "role": "architect",
                        "reasoning": "xhigh",
                        "packet_path": str(packet_path),
                    },
                    {
                        "packet_id": "PKT-ARCH-2",
                        "feature_id": feature_id,
                        "wave_id": "W01",
                        "role": "architect",
                        "reasoning": "xhigh",
                        "packet_path": str(packet_path),
                    },
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    calls: list[list[str]] = []

    def _fake_run(command, **kwargs):
        calls.append(list(command))
        stdout_path = kwargs["stdout_path"]
        last_message_path = kwargs["run_dir"] / "last-message.md"
        if "resume" in command:
            stdout_path.write_text(
                json.dumps({"type": "item.completed", "item": {"status": "completed"}}) + "\n",
                encoding="utf-8",
            )
        else:
            stdout_path.write_text(
                json.dumps({"type": "thread.started", "thread_id": "thread-architect-1"}) + "\n"
                + json.dumps({"type": "item.completed", "item": {"status": "completed"}})
                + "\n",
                encoding="utf-8",
            )
        (kwargs["stderr_path"]).write_text("", encoding="utf-8")
        last_message_path.write_text("done\n", encoding="utf-8")
        return 0

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher._run_codex_process", _fake_run)

    first = launch_codex_for_packet("PKT-ARCH-1")
    second = launch_codex_for_packet("PKT-ARCH-2")

    assert first["session_mode"] == "exec"
    assert first["thread_id"] == "thread-architect-1"
    assert second["session_mode"] == "resume"
    assert second["thread_id"] == "thread-architect-1"
    assert second["resumed_from_thread_id"] == "thread-architect-1"
    assert "resume" not in calls[0]
    assert "resume" in calls[1]
    assert "thread-architect-1" in calls[1]

    feature_state = state_store.find_record("features", "features", "feature_id", feature_id)
    assert feature_state["role_threads"]["architect"]["thread_id"] == "thread-architect-1"


def test_launch_codex_for_packet_keeps_reviewer_session_separate_and_coder_fresh(tmp_path: Path, monkeypatch) -> None:
    state_store.STATE_DIR = tmp_path / "state"
    state_store.STATE_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", tmp_path / "packets")
    monkeypatch.setattr(
        "prefect_grace.tasks.codex_launcher.load_agent_config",
        lambda: {
            "codex": {
                "binary": "codex1",
                "workdir": str(tmp_path),
                "shared_model": "gpt-5.4",
                "roles": {
                    "reviewer": {
                        "reasoning": "xhigh",
                        "sandbox": "read-only",
                        "approval": "never",
                        "resume_strategy": "feature_role",
                    },
                    "coder": {
                        "reasoning": "high",
                        "sandbox": "workspace-write",
                        "approval": "never",
                    },
                },
            }
        },
    )

    feature_id = "FEAT-ROLE-SEPARATION"
    packet_dir = (tmp_path / "packets" / feature_id)
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "feature-brief.md").write_text("# Feature brief\n", encoding="utf-8")
    packet_path = tmp_path / "packet.md"
    packet_path.write_text("# Packet\n", encoding="utf-8")

    (state_store.STATE_DIR / "features.yaml").write_text(
        yaml.safe_dump(
            {
                "features": [
                    {
                        "feature_id": feature_id,
                        "title": "Feature",
                        "role_threads": {
                            "architect": {"thread_id": "thread-architect-existing"},
                            "reviewer": {"thread_id": "thread-reviewer-existing"},
                        },
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (state_store.STATE_DIR / "packets.yaml").write_text(
        yaml.safe_dump(
            {
                "packets": [
                    {
                        "packet_id": "PKT-REV",
                        "feature_id": feature_id,
                        "wave_id": "W01",
                        "role": "reviewer",
                        "reasoning": "xhigh",
                        "packet_path": str(packet_path),
                    },
                    {
                        "packet_id": "PKT-CODER",
                        "feature_id": feature_id,
                        "wave_id": "W01",
                        "role": "coder",
                        "reasoning": "high",
                        "packet_path": str(packet_path),
                    },
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    calls: dict[str, list[str]] = {}

    def _fake_run(command, **kwargs):
        packet_id = kwargs["packet_id"]
        calls[packet_id] = list(command)
        kwargs["stdout_path"].write_text(
            json.dumps({"type": "item.completed", "item": {"status": "completed"}}) + "\n",
            encoding="utf-8",
        )
        kwargs["stderr_path"].write_text("", encoding="utf-8")
        (kwargs["run_dir"] / "last-message.md").write_text("done\n", encoding="utf-8")
        return 0

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher._run_codex_process", _fake_run)

    reviewer = launch_codex_for_packet("PKT-REV")
    coder = launch_codex_for_packet("PKT-CODER")

    assert reviewer["session_mode"] == "resume"
    assert reviewer["thread_id"] == "thread-reviewer-existing"
    assert "thread-reviewer-existing" in calls["PKT-REV"]
    assert "thread-architect-existing" not in calls["PKT-REV"]

    assert coder["session_mode"] == "exec"
    assert coder["thread_id"] is None
    assert "resume" not in calls["PKT-CODER"]
