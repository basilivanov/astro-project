import unittest
from unittest.mock import MagicMock
import os
import sys

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.services.report_workflow import generate_section_with_retries
from backend.app.llm.orchestrator import SectionSpec, LLMClient

class TestNameErrorRepro(unittest.TestCase):
    def test_repro_clillmclient_nameerror(self):
        spec = SectionSpec(section_id="test", title="Test", prompt="test")
        context = {"facts": {"v": "facts_v1", "pos": []}}
        
        # We use a mock that is NOT CliLLMClient and NOT OpenRouterClient
        primary_client = MagicMock(spec=LLMClient)
        
        # This should NOT raise NameError
        try:
            generate_section_with_retries(
                spec,
                context,
                primary_client=primary_client,
                fallback_models=[],
                max_attempts=1
            )
        except NameError as e:
            self.fail(f"NameError raised: {e}")
        except Exception:
            # We expect some exception because generate_sections is not mocked here, 
            # but NameError is what we want to avoid.
            pass

if __name__ == "__main__":
    unittest.main()
