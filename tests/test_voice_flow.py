from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


ROOT = Path(__file__).resolve().parents[2]
BOT_APP_DIR = ROOT / "bot" / "app"
BOT_APP_AVAILABLE = (BOT_APP_DIR / "main.py").exists() and (BOT_APP_DIR / "stt.py").exists()


class _FakeWhisperModel:
    def __init__(self, model_name: str, device: str = "cpu", compute_type: str = "int8") -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type

    def transcribe(self, path: str, language: str = "ru", beam_size: int = 5):
        return [], {"path": path, "language": language, "beam_size": beam_size}


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bot_main_module(monkeypatch: pytest.MonkeyPatch):
    if not BOT_APP_AVAILABLE:
        pytest.skip("bot/app voice modules are not present in this backend test image")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:pass@localhost:5432/astro_test",
    )
    monkeypatch.setenv("BOT_ADMIN_IDS", "42")

    fake_api = types.ModuleType("app.api")

    async def _start_bot_server(_bot):
        return None

    fake_api.start_bot_server = _start_bot_server
    monkeypatch.setitem(sys.modules, "app.api", fake_api)

    fake_stt = types.ModuleType("app.stt")
    fake_stt.transcribe_audio = lambda path: "stub transcript"
    monkeypatch.setitem(sys.modules, "app.stt", fake_stt)

    fake_app_pkg = types.ModuleType("app")
    fake_app_pkg.__path__ = [str(BOT_APP_DIR)]
    fake_app_pkg.api = fake_api
    fake_app_pkg.stt = fake_stt
    monkeypatch.setitem(sys.modules, "app", fake_app_pkg)
    sys.modules.pop("bot_test_voice_flow_main", None)

    return _load_module("bot_test_voice_flow_main", BOT_APP_DIR / "main.py")


def _build_voice_message(*, telegram_id: int = 42, file_id: str = "voice-file-1"):
    message = SimpleNamespace()
    message.from_user = SimpleNamespace(id=telegram_id)
    message.voice = SimpleNamespace(file_id=file_id)
    message.answer = AsyncMock()
    message.message_id = 777
    return message


def test_voice_update_runs_stt_answers_and_emits_telemetry(
    bot_main_module,
    monkeypatch: pytest.MonkeyPatch,
):
    message = _build_voice_message()
    local_path = Path("/tmp/test-voice-flow.ogg")
    task_id = uuid.uuid4()
    created_tasks: list[dict[str, object]] = []
    telemetry: list[tuple[str, dict[str, object]]] = []

    async def fake_download_voice(_message):
        return local_path

    async def fake_create_agent_task(**kwargs):
        created_tasks.append(kwargs)
        telemetry.append(
            (
                "bot.voice.task_created",
                {
                    "telegram_id": kwargs["telegram_id"],
                    "source": kwargs["source"],
                    "voice_file_id": kwargs["voice_file_id"],
                    "transcript": kwargs["transcript"],
                },
            )
        )
        return SimpleNamespace(id=task_id, summary="Разобранный summary")

    async def fake_to_thread(fn, *args, **kwargs):
        telemetry.append(("bot.voice.stt_started", {"path": str(args[0]) if args else ""}))
        result = fn(*args, **kwargs)
        telemetry.append(("bot.voice.stt_completed", {"transcript": result}))
        return result

    def fake_logger_info(event, **kwargs):
        telemetry.append((event, kwargs))

    monkeypatch.setattr(bot_main_module, "is_admin_user", lambda telegram_id: True)
    monkeypatch.setattr(bot_main_module, "download_voice", fake_download_voice)
    monkeypatch.setattr(bot_main_module, "create_agent_task", fake_create_agent_task)
    monkeypatch.setattr(bot_main_module.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(bot_main_module, "transcribe_audio", lambda path: "  сделай   сводку  по рынку  ")
    monkeypatch.setattr(bot_main_module.logger, "info", fake_logger_info)
    monkeypatch.setattr(Path, "unlink", lambda self: None)

    asyncio.run(bot_main_module.voice_task_handler(message))

    assert created_tasks == [
        {
            "telegram_id": 42,
            "source": "voice",
            "transcript": "сделай сводку по рынку",
            "voice_file_id": "voice-file-1",
        }
    ]
    assert message.answer.await_args_list[0].args == ("Принял голос. Распознаю...",)
    result_call = message.answer.await_args_list[1]
    assert "Распознал задачу" in result_call.args[0]
    assert "Разобранный summary" in result_call.args[0]
    assert telemetry[0][0] == "bot.voice.stt_started"
    assert telemetry[1] == (
        "bot.voice.stt_completed",
        {"transcript": "  сделай   сводку  по рынку  "},
    )
    assert telemetry[2] == (
        "bot.voice.task_created",
        {
            "telegram_id": 42,
            "source": "voice",
            "voice_file_id": "voice-file-1",
            "transcript": "сделай сводку по рынку",
        },
    )
