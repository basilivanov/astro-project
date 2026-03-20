import unittest
import os
import sys

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.services.report_workflow import resolve_primary_model

class TestLLMModelRouting(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        # Clear model envs for clean start
        for k in list(os.environ.keys()):
            if k.startswith("OPENROUTER_MODEL"):
                del os.environ[k]

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_default_free_model_when_all_empty(self):
        # Case: No env variables set at all
        model = resolve_primary_model("natal_master")
        self.assertEqual(model, "openai/gpt-4.1-nano")

    def test_specific_model_routing(self):
        os.environ["OPENROUTER_MODEL_NATAL"] = "high-end-natal"
        os.environ["OPENROUTER_MODEL_HORARY"] = "fast-horary"
        
        self.assertEqual(resolve_primary_model("natal_master"), "high-end-natal")
        self.assertEqual(resolve_primary_model("horary_answer"), "fast-horary")
        # Default for unknown type should still be the base model (which is empty in this test setup)
        # But wait, if OPENROUTER_MODEL is missing, it returns the hardcoded free default.
        self.assertEqual(resolve_primary_model("unknown"), "openai/gpt-4.1-nano")

    def test_fallback_to_base_openrouter_model(self):
        os.environ["OPENROUTER_MODEL"] = "base-model"
        # No specific natal model
        self.assertEqual(resolve_primary_model("natal_master"), "base-model")

if __name__ == "__main__":
    unittest.main()
