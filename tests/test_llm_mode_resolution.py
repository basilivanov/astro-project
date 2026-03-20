import os
import unittest
import sys

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.llm.mode import resolve_llm_mode


class DummyPayload:
    def __init__(self, llm_mode=None):
        self.llm_mode = llm_mode


class TestLLMModeResolution(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_default_stub_when_env_missing(self) -> None:
        if "DEFAULT_LLM_MODE" in os.environ:
            del os.environ["DEFAULT_LLM_MODE"]
        if "LLM_SMOKE" in os.environ:
            del os.environ["LLM_SMOKE"]
        payload = DummyPayload()
        self.assertEqual(resolve_llm_mode(payload), "stub")

    def test_default_openrouter_when_llm_smoke_set(self) -> None:
        if "DEFAULT_LLM_MODE" in os.environ:
            del os.environ["DEFAULT_LLM_MODE"]
        os.environ["LLM_SMOKE"] = "1"
        payload = DummyPayload()
        self.assertEqual(resolve_llm_mode(payload), "openrouter")

    def test_default_stub_when_env_empty(self) -> None:
        os.environ["DEFAULT_LLM_MODE"] = ""
        if "LLM_SMOKE" in os.environ:
            del os.environ["LLM_SMOKE"]
        payload = DummyPayload()
        self.assertEqual(resolve_llm_mode(payload), "stub")

    def test_respects_default_cli(self) -> None:
        os.environ["DEFAULT_LLM_MODE"] = "cli"
        payload = DummyPayload()
        self.assertEqual(resolve_llm_mode(payload), "cli")

    def test_invalid_llm_mode_falls_back_to_default(self) -> None:
        os.environ["DEFAULT_LLM_MODE"] = "cli"
        payload = DummyPayload(llm_mode="garbage")
        self.assertEqual(resolve_llm_mode(payload), "cli")

    def test_explicit_payload_mode_overrides_default(self) -> None:
        os.environ["DEFAULT_LLM_MODE"] = "openrouter"
        payload = DummyPayload(llm_mode="cli")
        self.assertEqual(resolve_llm_mode(payload), "cli")

    def test_gemini_mode_works(self) -> None:
        payload = DummyPayload(llm_mode="gemini")
        self.assertEqual(resolve_llm_mode(payload), "gemini")

    def test_codex_mode_works(self) -> None:
        payload = DummyPayload(llm_mode="codex")
        self.assertEqual(resolve_llm_mode(payload), "codex")

    def test_empty_env_and_empty_payload_defaults_to_stub(self) -> None:
        if "DEFAULT_LLM_MODE" in os.environ:
            del os.environ["DEFAULT_LLM_MODE"]
        if "LLM_SMOKE" in os.environ:
            del os.environ["LLM_SMOKE"]
        payload = DummyPayload(llm_mode=None)
        self.assertEqual(resolve_llm_mode(payload), "stub")

    def test_stub_mode_works(self) -> None:
        payload = DummyPayload(llm_mode="stub")
        self.assertEqual(resolve_llm_mode(payload), "stub")

    def test_cheap_mode_works(self) -> None:
        payload = DummyPayload(llm_mode="cheap")
        self.assertEqual(resolve_llm_mode(payload), "cheap")

if __name__ == "__main__":
    unittest.main()