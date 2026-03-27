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


ROOT = Path(__file__).resolve().parent.parent
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
    sys.modules.pop("test_bot_app_main", None)

    return _load_module("test_bot_app_main", BOT_APP_DIR / "main.py")


@pytest.fixture
def stt_module(monkeypatch: pytest.MonkeyPatch):
    if not BOT_APP_AVAILABLE:
        pytest.skip("bot/app STT module is not present in this backend test image")
    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        types.SimpleNamespace(WhisperModel=_FakeWhisperModel),
    )
    sys.modules.pop("test_bot_app_stt", None)
    return _load_module("test_bot_app_stt", BOT_APP_DIR / "stt.py")


def _build_voice_message(*, telegram_id: int = 42, file_id: str = "voice-file-1"):
    message = SimpleNamespace()
    message.from_user = SimpleNamespace(id=telegram_id)
    message.voice = SimpleNamespace(file_id=file_id)
    message.answer = AsyncMock()
    message.message_id = 777
    return message


def test_voice_handler_creates_voice_task_with_normalized_transcript(
    bot_main_module,
    monkeypatch: pytest.MonkeyPatch,
):
    message = _build_voice_message()
    local_path = Path("/tmp/test-voice.ogg")
    task_id = uuid.uuid4()
    created_tasks: list[dict[str, object]] = []

    async def fake_download_voice(_message):
        return local_path

    async def fake_create_agent_task(**kwargs):
        created_tasks.append(kwargs)
        return SimpleNamespace(id=task_id, summary="Нормализованный summary")

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(bot_main_module, "is_admin_user", lambda telegram_id: True)
    monkeypatch.setattr(bot_main_module, "download_voice", fake_download_voice)
    monkeypatch.setattr(bot_main_module, "create_agent_task", fake_create_agent_task)
    monkeypatch.setattr(bot_main_module.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(bot_main_module, "transcribe_audio", lambda path: "  привет   мир  ")
    monkeypatch.setattr(Path, "unlink", lambda self: None)

    asyncio.run(bot_main_module.voice_task_handler(message))

    assert created_tasks == [
        {
            "telegram_id": 42,
            "source": "voice",
            "transcript": "привет мир",
            "voice_file_id": "voice-file-1",
        }
    ]
    assert message.answer.await_count == 2
    prompt_call = message.answer.await_args_list[0]
    assert prompt_call.args == ("Принял голос. Распознаю...",)
    result_call = message.answer.await_args_list[1]
    assert "Распознал задачу" in result_call.args[0]
    assert "Нормализованный summary" in result_call.args[0]
    assert result_call.kwargs["reply_markup"].inline_keyboard[0][0].callback_data == f"task_confirm:{task_id}"
    assert result_call.kwargs["reply_markup"].inline_keyboard[1][0].callback_data == f"task_clarify:{task_id}"


def test_voice_handler_rejects_empty_transcript_after_normalization(
    bot_main_module,
    monkeypatch: pytest.MonkeyPatch,
):
    message = _build_voice_message()
    local_path = Path("/tmp/test-empty-voice.ogg")
    create_task = AsyncMock()

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(bot_main_module, "is_admin_user", lambda telegram_id: True)
    monkeypatch.setattr(bot_main_module, "download_voice", AsyncMock(return_value=local_path))
    monkeypatch.setattr(bot_main_module.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(bot_main_module, "transcribe_audio", lambda path: "   \n\t  ")
    monkeypatch.setattr(bot_main_module, "create_agent_task", create_task)
    monkeypatch.setattr(Path, "unlink", lambda self: None)

    asyncio.run(bot_main_module.voice_task_handler(message))

    create_task.assert_not_called()
    assert message.answer.await_args_list[0].args == ("Принял голос. Распознаю...",)
    assert message.answer.await_args_list[1].args == ("Текст не распознан. Попробуй еще раз.",)


def test_transcribe_audio_joins_segments_and_falls_back_on_invalid_beam_size(
    stt_module,
    monkeypatch: pytest.MonkeyPatch,
):
    class Segment:
        def __init__(self, text: str) -> None:
            self.text = text

    class FakeModel:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, int]] = []

        def transcribe(self, path: str, language: str = "ru", beam_size: int = 5):
            self.calls.append((path, language, beam_size))
            return [Segment(" Привет"), Segment("мир "), Segment("")], {"language": language}

    fake_model = FakeModel()
    monkeypatch.setattr(stt_module, "_load_model", lambda: fake_model)
    monkeypatch.setenv("WHISPER_LANGUAGE", "ru")
    monkeypatch.setenv("WHISPER_BEAM_SIZE", "bad-int")

    transcript = stt_module.transcribe_audio("/tmp/audio.ogg")

    assert transcript == "Привет мир"
    assert fake_model.calls == [("/tmp/audio.ogg", "ru", 5)]


def test_transcribe_audio_caches_model_instance(stt_module, monkeypatch: pytest.MonkeyPatch):
    load_calls: list[tuple[str, str, str]] = []

    class CachedModel:
        def transcribe(self, path: str, language: str = "ru", beam_size: int = 5):
            return [], {}

    def fake_whisper_model(model_name: str, device: str = "cpu", compute_type: str = "int8"):
        load_calls.append((model_name, device, compute_type))
        return CachedModel()

    monkeypatch.setattr(stt_module, "WhisperModel", fake_whisper_model)
    monkeypatch.setenv("WHISPER_MODEL", "tiny")
    monkeypatch.setenv("WHISPER_DEVICE", "cpu")
    monkeypatch.setenv("WHISPER_COMPUTE_TYPE", "int8")
    stt_module._MODEL = None

    first = stt_module._load_model()
    second = stt_module._load_model()

    assert first is second
    assert load_calls == [("tiny", "cpu", "int8")]
