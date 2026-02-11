import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.services.report_workflow import generate_section_with_retries, resolve_llm_fallback_chain
from backend.app.llm.orchestrator import SectionSpec, SectionResult, LLMClient, OpenRouterClient

class TestLLMFallbackChain(unittest.TestCase):
    def setUp(self):
        self.spec = SectionSpec(section_id="test", title="Test", prompt="test")
        self.context = {"facts": {"v": "facts_v1", "pos": []}}
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_resolve_fallback_chain_defaults(self):
        if "OPENROUTER_FALLBACK_CHAIN" in os.environ:
            del os.environ["OPENROUTER_FALLBACK_CHAIN"]
        chain = resolve_llm_fallback_chain()
        self.assertIn("openai/gpt-4o-mini", chain)
        self.assertEqual(chain[0], "openai/gpt-4o-mini")
        
        # Verify no forbidden models
        forbidden = [
            "mistralai/pixtral-12b:free", 
            "google/gemini-2.0-flash-lite-preview-02-05:free"
        ]
        for f in forbidden:
            self.assertNotIn(f, chain, f"Forbidden model {f} found in default fallback chain!")

    def test_resolve_fallback_chain_from_env(self):
        os.environ["OPENROUTER_FALLBACK_CHAIN"] = "model1,model2"
        chain = resolve_llm_fallback_chain()
        self.assertEqual(chain, ["model1", "model2"])

    @patch("backend.app.services.report_workflow.LLMOrchestrator")
    @patch("backend.app.services.report_workflow.OpenRouterClient.from_env")
    def test_fallback_chain_switching(self, mock_from_env, mock_orchestrator_cls):
        # Setup: Primary client
        primary_client = MagicMock(spec=OpenRouterClient)
        primary_client.model = "primary-model"
        
        # Setup: Fallback models
        fallback_models = ["fallback-1", "fallback-2"]
        
        # Configure Orchestrator mocks
        # First call (primary) fails with Exception (e.g. 429)
        # Second call (fallback-1) fails with Exception
        # Third call (fallback-2) succeeds
        
        mock_orch_primary = MagicMock()
        mock_orch_primary.generate_sections.side_effect = Exception("Primary failed")
        
        mock_orch_fb1 = MagicMock()
        mock_orch_fb1.generate_sections.side_effect = Exception("FB1 failed")
        
        mock_orch_fb2 = MagicMock()
        mock_orch_fb2.generate_sections.return_value = [
            SectionResult(section_id="test", title="Test", content='[{"type":"paragraph","text":"success"}]')
        ]
        
        # Return different orchestrators for different clients
        def get_orchestrator(client):
            if client == primary_client:
                return mock_orch_primary
            if getattr(client, "model", None) == "fallback-1":
                return mock_orch_fb1
            if getattr(client, "model", None) == "fallback-2":
                return mock_orch_fb2
            return MagicMock()

        mock_orchestrator_cls.side_effect = get_orchestrator
        
        # Mock client creation for fallbacks
        def create_fb_client(model_override):
            c = MagicMock(spec=OpenRouterClient)
            c.model = model_override
            return c
        mock_from_env.side_effect = create_fb_client

        # Execute
        result = generate_section_with_retries(
            self.spec,
            self.context,
            primary_client=primary_client,
            fallback_models=fallback_models,
            max_attempts=1 # 1 attempt per model for fast test
        )
        
        # Verify
        self.assertEqual(json.loads(result.content)[0]["text"], "success")
        
        # Verify chain order: primary -> fb1 -> fb2
        # Check that from_env was called for both fallbacks
        self.assertEqual(mock_from_env.call_count, 2)
        mock_from_env.assert_any_call(model_override="fallback-1")
        mock_from_env.assert_any_call(model_override="fallback-2")

    @patch("backend.app.services.report_workflow.OpenRouterClient.from_env")
    def test_fallback_with_real_orchestrator_and_markdown(self, mock_from_env):
        # This test ensures that if a fallback returns Markdown, it's correctly parsed into JSON blocks
        
        primary_client = MagicMock(spec=OpenRouterClient)
        primary_client.model = "primary"
        primary_client.generate.side_effect = Exception("Primary API Error")
        
        fallback_client = MagicMock(spec=LLMClient)
        # Model returns markdown fences. Ensure text is long enough to pass validation (>30 chars)
        fallback_client.generate.return_value = ('```json\n[{"type":"paragraph","text":"this is a long enough text parsed from markdown to pass validation"}]\n```', {})
        
        # When creating fallback client for "fb1"
        mock_from_env.return_value = fallback_client
        
        result = generate_section_with_retries(
            self.spec,
            self.context,
            primary_client=primary_client,
            fallback_models=["fb1"],
            max_attempts=1
        )
        
        # Verify it was parsed into clean JSON (no backticks)
        content = result.content
        self.assertTrue(content.startswith('[{"type"'))
        self.assertNotIn("```", content)
        data = json.loads(content)
        self.assertEqual(data[0]["text"], "this is a long enough text parsed from markdown to pass validation")

if __name__ == "__main__":
    unittest.main()
