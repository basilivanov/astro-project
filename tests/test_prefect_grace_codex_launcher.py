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
    CodexProcessResult,
    _extract_stdout_progress,
    _extract_last_stdout_event,
    _run_progress_class,
    _extract_thread_id,
    _format_heartbeat_message,
    _heartbeat_loop,
    _heartbeat_payload,
    build_packet_prompt,
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


def test_run_progress_class_detects_startup_only(tmp_path: Path) -> None:
    stdout_path = tmp_path / "stdout.jsonl"
    stdout_path.write_text(
        json.dumps({"type": "thread.started", "thread_id": "thread-123"}) + "\n"
        + json.dumps({"type": "turn.started"})
        + "\n",
        encoding="utf-8",
    )

    assert _run_progress_class(stdout_path) == "startup_only"


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
    assert "item.completed/completed/unknown" in message


def test_extract_stdout_progress_ignores_noise_and_detects_final_marker(tmp_path: Path) -> None:
    stdout_path = tmp_path / "stdout.jsonl"
    stdout_path.write_text(
        json.dumps({"type": "item.updated", "item": {"id": "todo-1", "type": "todo_list", "status": "in_progress"}})
        + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "id": "cmd-1",
                    "type": "command_execution",
                    "status": "completed",
                    "aggregated_output": "noise only",
                },
            }
        )
        + "\n"
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "id": "msg-1",
                    "type": "agent_message",
                    "text": "FINAL_PACKET_DECISION_JSON\n{}\nEND_FINAL_PACKET_DECISION_JSON",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    progress = _extract_stdout_progress(stdout_path)

    assert progress["event_type"] == "item.completed"
    assert progress["item_type"] == "agent_message"
    assert progress["semantic_reason"] == "item.completed:agent_message"
    assert progress["final_marker"] == "END_FINAL_PACKET_DECISION_JSON"
    assert progress["final_signature"] is not None


def test_launch_codex_for_packet_retries_startup_stall_with_fresh_exec(monkeypatch, tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.md"
    packet_path.write_text("# Packet\nArchitect packet body", encoding="utf-8")
    feature_id = "FEAT-STARTUP-STALL"

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", tmp_path / "packets")
    monkeypatch.setattr(
        "prefect_grace.tasks.codex_launcher.load_agent_config",
        lambda: {
            "codex": {
                "binary": "codex",
                "shared_model": "gpt-5.4",
                "workdir": "/opt/astro-project",
                "roles": {"architect": {"reasoning": "xhigh", "sandbox": "danger-full-access", "approval": "never", "resume_strategy": "feature_role", "max_auto_resume_attempts": 2}},
            }
        },
    )
    packets_path = tmp_path / "packets.yaml"
    packets_path.write_text(
        yaml.safe_dump(
            {
                "packets": [
                    {
                        "packet_id": "PKT-STARTUP-STALL",
                        "feature_id": feature_id,
                        "wave_id": "W00",
                        "role": "architect",
                        "reasoning": "xhigh",
                        "packet_path": str(packet_path),
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.find_record", lambda *args, **kwargs: yaml.safe_load(packets_path.read_text())["packets"][0])
    monkeypatch.setattr("prefect_grace.tasks.state_store.find_record", lambda *args, **kwargs: yaml.safe_load(packets_path.read_text())["packets"][0])
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.update_record", lambda *args, **kwargs: None)

    calls: list[list[str]] = []

    def _fake_run(command, **kwargs):
        calls.append(list(command))
        stdout_path = kwargs["stdout_path"]
        stderr_path = kwargs["stderr_path"]
        last_message_path = kwargs["run_dir"] / "last-message.md"
        if len(calls) == 1:
            stdout_path.write_text(
                json.dumps({"type": "thread.started", "thread_id": "thread-startup-stall"}) + "\n"
                + json.dumps({"type": "turn.started"})
                + "\n",
                encoding="utf-8",
            )
            stderr_path.write_text("Codex stall detected after 300.0 idle seconds.\n", encoding="utf-8")
            return CodexProcessResult(returncode=-9, termination_reason="stall_killed")
        stdout_path.write_text(
            json.dumps({"type": "item.completed", "item": {"status": "completed"}}) + "\n",
            encoding="utf-8",
        )
        stderr_path.write_text("", encoding="utf-8")
        last_message_path.write_text("done\n", encoding="utf-8")
        return CodexProcessResult(returncode=0, termination_reason="completed")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher._run_codex_process", _fake_run)

    result = launch_codex_for_packet("PKT-STARTUP-STALL")

    assert result["returncode"] == 0
    assert result["attempt_count"] == 2
    assert result["attempts"][0]["termination_reason"] == "stall_killed"
    assert "resume" not in calls[0]
    assert "resume" not in calls[1]


def test_build_packet_prompt_compacts_large_context_for_planner(monkeypatch, tmp_path: Path) -> None:
    feature_dir = tmp_path / "packets" / "FEAT-1"
    feature_dir.mkdir(parents=True)
    (feature_dir / "feature-brief.md").write_text("# Brief\n" + ("- line\n" * 2000), encoding="utf-8")
    (feature_dir / "wave-plan.md").write_text("# Wave\n" + ("- wave\n" * 2000), encoding="utf-8")
    packet_path = tmp_path / "packet.md"
    packet_path.write_text("# Packet\nPlanner packet body", encoding="utf-8")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", tmp_path / "packets")
    monkeypatch.setattr(
        "prefect_grace.tasks.codex_launcher.find_record",
        lambda *args, **kwargs: {"feature_id": "FEAT-1"},
    )

    packet = {
        "packet_id": "PKT-1",
        "feature_id": "FEAT-1",
        "wave_id": "W00",
        "role": "planner",
        "packet_path": str(packet_path),
        "dependencies": [],
    }
    prompt = build_packet_prompt(packet, "Planner role prompt")

    assert len(prompt) < 30000
    assert prompt.count("- line") < 2000
    assert prompt.count("- wave") < 2000


def test_heartbeat_loop_kills_when_only_stdout_noise_grows(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    stdout_path = run_dir / "stdout.jsonl"
    stdout_path.write_text("", encoding="utf-8")
    handler = _ListHandler()
    logger = logging.getLogger("test_prefect_grace_codex_launcher_noise")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    class _Proc:
        def __init__(self) -> None:
            self.pid = 322
            self.killed = False

        def poll(self):
            return None if not self.killed else -9

        def kill(self):
            self.killed = True

    process = _Proc()
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(process,),
        kwargs={
            "packet_id": "PKT-NOISE",
            "run_dir": run_dir,
            "stdout_path": stdout_path,
            "logger": logger,
            "interval_seconds": 0.01,
            "stop_event": stop_event,
            "stall_timeout_seconds": 0.03,
        },
        daemon=True,
    )
    thread.start()
    for index in range(4):
        stdout_path.write_text(
            stdout_path.read_text(encoding="utf-8")
            + json.dumps(
                {
                    "type": "item.updated",
                    "item": {"id": f"todo-{index}", "type": "todo_list", "status": "in_progress"},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        time.sleep(0.01)
    thread.join(timeout=1)
    stop_event.set()

    assert process.killed is True
    assert any("Codex stall detected packet=PKT-NOISE" in message for message in handler.messages)


def test_heartbeat_loop_collects_final_output_and_kills_hung_process(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    stdout_path = run_dir / "stdout.jsonl"
    stdout_path.write_text("", encoding="utf-8")
    last_message_path = run_dir / "last-message.md"
    last_message_path.write_text(
        "FINAL_GRACE_WAVE_PLAN_JSON\n{}\nEND_FINAL_GRACE_WAVE_PLAN_JSON\n",
        encoding="utf-8",
    )
    handler = _ListHandler()
    logger = logging.getLogger("test_prefect_grace_codex_launcher_final")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    class _Proc:
        def __init__(self) -> None:
            self.pid = 323
            self.killed = False

        def poll(self):
            return None if not self.killed else -9

        def kill(self):
            self.killed = True

    process = _Proc()
    stop_event = threading.Event()
    stall_state = {"detected": False, "idle_seconds": 0.0, "final_output_collected": False}
    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(process,),
        kwargs={
            "packet_id": "PKT-FINAL",
            "run_dir": run_dir,
            "stdout_path": stdout_path,
            "last_message_path": last_message_path,
            "logger": logger,
            "interval_seconds": 0.01,
            "stop_event": stop_event,
            "stall_state": stall_state,
            "stall_timeout_seconds": 1.0,
            "final_output_grace_seconds": 0.02,
        },
        daemon=True,
    )
    thread.start()
    time.sleep(0.08)
    thread.join(timeout=1)
    stop_event.set()

    assert process.killed is True
    assert stall_state["final_output_collected"] is True
    assert stall_state["final_marker"] == "END_FINAL_GRACE_WAVE_PLAN_JSON"
    assert any("Codex final output collected packet=PKT-FINAL" in message for message in handler.messages)


def test_heartbeat_loop_kills_hung_process_after_turn_completed(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    stdout_path = run_dir / "stdout.jsonl"
    stdout_path.write_text(
        json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "id": "msg-1",
                    "type": "agent_message",
                    "text": "Plain final message without strict marker",
                },
            }
        )
        + "\n"
        + json.dumps({"type": "turn.completed", "usage": {"output_tokens": 3}})
        + "\n",
        encoding="utf-8",
    )
    handler = _ListHandler()
    logger = logging.getLogger("test_prefect_grace_codex_launcher_post_turn")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    class _Proc:
        def __init__(self) -> None:
            self.pid = 324
            self.killed = False

        def poll(self):
            return None if not self.killed else -9

        def kill(self):
            self.killed = True

    process = _Proc()
    stop_event = threading.Event()
    stall_state = {"detected": False, "idle_seconds": 0.0, "final_output_collected": False, "post_turn_completion_collected": False}
    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(process,),
        kwargs={
            "packet_id": "PKT-POST-TURN",
            "run_dir": run_dir,
            "stdout_path": stdout_path,
            "logger": logger,
            "interval_seconds": 0.01,
            "stop_event": stop_event,
            "stall_state": stall_state,
            "stall_timeout_seconds": 1.0,
            "final_output_grace_seconds": 10.0,
            "post_turn_completion_grace_seconds": 0.02,
        },
        daemon=True,
    )
    thread.start()
    time.sleep(0.08)
    thread.join(timeout=1)
    stop_event.set()

    assert process.killed is True


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


def test_launch_codex_for_packet_reuses_feature_role_session_for_planner(tmp_path: Path, monkeypatch) -> None:
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
                    "planner": {
                        "reasoning": "xhigh",
                        "sandbox": "workspace-write",
                        "approval": "never",
                        "resume_strategy": "feature_role",
                    }
                },
            }
        },
    )

    feature_id = "FEAT-PLANNER-RESUME"
    packet_dir = tmp_path / "packets" / feature_id
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "feature-brief.md").write_text("# Feature brief\n", encoding="utf-8")
    packet_path = tmp_path / "planner-packet.md"
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
                        "packet_id": "PKT-PLAN-1",
                        "feature_id": feature_id,
                        "wave_id": "W00",
                        "role": "planner",
                        "reasoning": "xhigh",
                        "packet_path": str(packet_path),
                    },
                    {
                        "packet_id": "PKT-PLAN-2",
                        "feature_id": feature_id,
                        "wave_id": "W00",
                        "role": "planner",
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
                json.dumps({"type": "thread.started", "thread_id": "thread-planner-1"}) + "\n"
                + json.dumps({"type": "item.completed", "item": {"status": "completed"}})
                + "\n",
                encoding="utf-8",
            )
        kwargs["stderr_path"].write_text("", encoding="utf-8")
        last_message_path.write_text("done\n", encoding="utf-8")
        return 0

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher._run_codex_process", _fake_run)

    first = launch_codex_for_packet("PKT-PLAN-1")
    second = launch_codex_for_packet("PKT-PLAN-2")

    assert first["session_mode"] == "exec"
    assert first["thread_id"] == "thread-planner-1"
    assert second["session_mode"] == "resume"
    assert second["thread_id"] == "thread-planner-1"
    assert second["resumed_from_thread_id"] == "thread-planner-1"
    assert "resume" not in calls[0]
    assert "resume" in calls[1]
    assert "thread-planner-1" in calls[1]

    feature_state = state_store.find_record("features", "features", "feature_id", feature_id)
    assert feature_state["role_threads"]["planner"]["thread_id"] == "thread-planner-1"


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


def test_launch_codex_for_packet_retries_fresh_after_startup_only_stall(tmp_path: Path, monkeypatch) -> None:
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
                        "max_auto_resume_attempts": 1,
                    }
                },
            }
        },
    )

    feature_id = "FEAT-AUTO-RESUME"
    packet_dir = tmp_path / "packets" / feature_id
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
                        "packet_id": "PKT-AUTO-RESUME",
                        "feature_id": feature_id,
                        "wave_id": "W00",
                        "role": "architect",
                        "reasoning": "xhigh",
                        "packet_path": str(packet_path),
                    }
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
        stderr_path = kwargs["stderr_path"]
        last_message_path = kwargs["run_dir"] / "last-message.md"
        if len(calls) > 1:
            stdout_path.write_text(
                json.dumps({"type": "thread.started", "thread_id": "thread-fresh-retry"}) + "\n"
                + json.dumps({"type": "item.completed", "item": {"status": "completed"}})
                + "\n",
                encoding="utf-8",
            )
            stderr_path.write_text("", encoding="utf-8")
            last_message_path.write_text("done\n", encoding="utf-8")
            return CodexProcessResult(returncode=0, termination_reason="completed")
        stdout_path.write_text(
            json.dumps({"type": "thread.started", "thread_id": "thread-auto-resume"}) + "\n",
            encoding="utf-8",
        )
        stderr_path.write_text("Codex stall detected after 600.0 idle seconds.\n", encoding="utf-8")
        return CodexProcessResult(returncode=-9, termination_reason="stall_killed")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher._run_codex_process", _fake_run)

    result = launch_codex_for_packet("PKT-AUTO-RESUME")

    assert result["returncode"] == 0
    assert result["session_mode"] == "exec"
    assert result["resumed_from_thread_id"] is None
    assert result["thread_id"] == "thread-fresh-retry"
    assert result["attempt_count"] == 2
    assert result["attempts"][0]["termination_reason"] == "stall_killed"
    assert result["attempts"][1]["session_mode"] == "exec"
    assert "resume" not in calls[0]
    assert "resume" not in calls[1]
