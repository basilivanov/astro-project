import os
import unittest

from backend.app.services.feed_service import resolve_feed_llm_mode


class TestFeedModeResolution(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_feed_mode_override(self) -> None:
        os.environ["FEED_LLM_MODE"] = "codex"
        os.environ["DEFAULT_LLM_MODE"] = "openrouter"
        self.assertEqual(resolve_feed_llm_mode(), "codex")

    def test_feed_mode_defaults_to_global(self) -> None:
        os.environ.pop("FEED_LLM_MODE", None)
        os.environ["DEFAULT_LLM_MODE"] = "cli"
        self.assertEqual(resolve_feed_llm_mode(), "cli")

    def test_feed_mode_invalid_fallback(self) -> None:
        os.environ["FEED_LLM_MODE"] = "invalid"
        os.environ["DEFAULT_LLM_MODE"] = "openrouter"
        self.assertEqual(resolve_feed_llm_mode(), "openrouter")


if __name__ == "__main__":
    unittest.main()
