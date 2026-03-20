import unittest
import sys
import os
import json

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.engine_utils import translate_sign
from backend.app.services.report_workflow import cleanup_content_artifacts, RU_SIGNS, RU_PLANETS_FULL

class TestRULocalization(unittest.TestCase):
    def test_dicts_completeness(self):
        # Ensure all signs and planets are mapped
        self.assertIn("Aries", RU_SIGNS)
        self.assertIn("Sun", RU_PLANETS_FULL)
        self.assertIn("Chiron", RU_PLANETS_FULL)
        
    def test_sign_translation(self):
        self.assertEqual(translate_sign("Aries"), "Овен")
        self.assertEqual(translate_sign("Sagittarius"), "Стрелец")
        self.assertEqual(translate_sign("Unknown"), "Unknown")

    def test_cleanup_artifacts_anti_anglicism(self):
        # Test plain text
        text = "Your Sun is in Aries and Moon is in Sagittarius."
        cleaned = cleanup_content_artifacts(text)
        self.assertIn("Овен", cleaned)
        self.assertIn("Стрелец", cleaned)
        self.assertNotIn("Aries", cleaned)
        self.assertNotIn("Sagittarius", cleaned)

        # Test case insensitivity
        text = "aries and sagittarius"
        cleaned = cleanup_content_artifacts(text)
        self.assertIn("Овен", cleaned)
        self.assertIn("Стрелец", cleaned)

    def test_cleanup_artifacts_json_aware(self):
        # Test JSON blocks
        blocks = [
            {"type": "paragraph", "text": "Sun in Leo"},
            {"type": "header", "text": "Pisces Vibe"}
        ]
        text = json.dumps(blocks)
        cleaned_json = cleanup_content_artifacts(text)
        cleaned = json.loads(cleaned_json)
        
        self.assertEqual(cleaned[0]["text"], "Sun in Лев")
        self.assertEqual(cleaned[1]["text"], "Рыбы Vibe")

if __name__ == "__main__":
    unittest.main()
