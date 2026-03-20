import json
import os
import unittest
from unittest.mock import patch

from backend.app.llm.orchestrator import (
    _build_codex_subprocess_env,
    _parse_codex_cli_output,
    _parse_gemini_cli_output,
    build_cli_client_from_env,
)


class TestLLMCliParsing(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_gemini_parsing(self) -> None:
        payload = {"response": "{\"ok\": true}", "stats": {"tokens": {"total": 3}}}
        raw = json.dumps(payload)
        self.assertEqual(_parse_gemini_cli_output(raw), "{\"ok\": true}")

    def test_gemini_parsing_with_preamble(self) -> None:
        payload = {"response": "{\"ok\": true}", "stats": {"tokens": {"total": 3}}}
        raw = "Loaded cached credentials.\n" + json.dumps(payload)
        self.assertEqual(_parse_gemini_cli_output(raw), "{\"ok\": true}")

    def test_codex_parsing(self) -> None:
        lines = [
            json.dumps({"type": "thread.started", "thread_id": "t1"}),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"id": "item_0", "type": "agent_message", "text": "{\"ok\": true}"},
                }
            ),
            json.dumps({"type": "turn.completed", "usage": {"output_tokens": 3}}),
        ]
        raw = "\n".join(lines)
        self.assertEqual(_parse_codex_cli_output(raw), "{\"ok\": true}")

    def test_codex_uses_provider_specific_env_overrides(self) -> None:
        os.environ["LLM_CLI_PROVIDER"] = "gemini"
        os.environ["LLM_CLI_MODEL"] = "gemini-3-flash-preview"
        os.environ["LLM_CLI_REASONING"] = "medium"
        os.environ["LLM_CLI_ARGS"] = "--debug"
        os.environ["LLM_CLI_MODEL_CODEX"] = "codex-codex4/gpt-5-codex"
        os.environ["LLM_CLI_REASONING_CODEX"] = "high"
        os.environ["LLM_CLI_ARGS_CODEX"] = "--skip-git-repo-check"

        client = build_cli_client_from_env(provider_override="codex")

        self.assertEqual(client.provider, "codex")
        self.assertEqual(client.model, "codex-codex4/gpt-5-codex")
        self.assertEqual(client.reasoning, "high")
        self.assertEqual(client.extra_args, ["--skip-git-repo-check"])

    def test_codex_subprocess_env_prefers_codex_proxy_settings(self) -> None:
        with patch(
            "backend.app.llm.orchestrator._resolve_docker_host_gateway",
            return_value="172.21.0.1",
        ):
            env = _build_codex_subprocess_env(
                {
                    "OPENAI_BASE_URL": "https://generic.invalid/v1",
                    "OPENAI_API_KEY": "sk-generic",
                    "LLM_CLI_OPENAI_BASE_URL_CODEX": "http://__DOCKER_HOST_GATEWAY__:18317/v1",
                    "LLM_CLI_OPENAI_API_KEY_CODEX": "sk-cliproxy-local",
                }
            )

        self.assertEqual(env["OPENAI_BASE_URL"], "http://172.21.0.1:18317/v1")
        self.assertEqual(env["OPENAI_API_KEY"], "sk-cliproxy-local")


if __name__ == "__main__":
    unittest.main()
