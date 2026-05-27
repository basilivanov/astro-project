from __future__ import annotations

import importlib
import inspect
from pathlib import Path

from prefect_grace.tasks import codex_launcher


HELPER_MODULES = (
    "command_builder",
    "process_runner",
    "progress_tracker",
    "prompt_builder",
    "resume_policy",
    "session_manager",
)


def test_codex_launcher_facade_stays_below_packet_limit() -> None:
    source_path = Path(inspect.getsourcefile(codex_launcher) or "")
    assert source_path.name == "codex_launcher.py"
    assert len(source_path.read_text(encoding="utf-8").splitlines()) < 500


def test_codex_launcher_helper_modules_are_importable() -> None:
    for module_name in HELPER_MODULES:
        module = importlib.import_module(f"prefect_grace.tasks.codex_launcher_helpers.{module_name}")
        assert module.__name__.endswith(module_name)


def test_codex_launcher_facade_preserves_legacy_imports() -> None:
    expected = (
        "CodexLaunchResult",
        "CodexProcessResult",
        "build_packet_prompt",
        "role_prompt_for",
        "launch_codex_for_packet",
        "_build_exec_command",
        "_build_resume_command",
        "_extract_thread_id",
        "_extract_stdout_progress",
        "_heartbeat_loop",
        "_run_codex_process",
    )
    for name in expected:
        assert hasattr(codex_launcher, name)
