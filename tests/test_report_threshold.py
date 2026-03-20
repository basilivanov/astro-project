import unittest
import asyncio
import sys
import os
import uuid
from unittest.mock import MagicMock, patch

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.services.report_workflow import generate_report_sections
from backend.app.models import Report

class TestReportThreshold(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MagicMock()
        self.report = Report(
            id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            report_type="natal_master",
            status="pending"
        )
        self.payload = MagicMock()
        self.payload.report_type = "natal_master"
        self.payload.sections = None # Use defaults
        self.payload.house_system = "placidus"
        self.payload.birth_date = "1990-01-01T12:00:00"
        self.payload.birth_location = "Moscow"
        self.payload.birth_lat = 55.75
        self.payload.birth_lon = 37.61
        self.payload.birth_timezone = "Europe/Moscow"
        self.payload.include_fixed_stars = True
        self.payload.fixed_star_orb = 1.0

    @patch("backend.app.services.report_workflow.build_chart_data")
    @patch("backend.app.services.report_workflow.build_report_context")
    @patch("backend.app.services.report_workflow.generate_section_content")
    @patch("backend.app.services.report_workflow.initialize_report_chunks")
    async def test_report_fails_below_threshold(self, mock_init_chunks, mock_gen_content, mock_context, mock_chart):
        # Setup mocks
        mock_init_chunks.return_value = {}
        mock_chart.return_value = {}
        mock_context.return_value = {"client": {"gender": "male"}}
        
        # Simulate only 2 successful sections out of many (natal_master has ~18)
        # We'll make generate_section_content return "Ошибка генерации" for most
        # but valid content for 2.
        
        success_content = '[{"type":"paragraph","text":"success"}]'
        fail_content = '[{"type":"callout","variant":"error","title":"Ошибка генерации","content":"fail"}]'
        
        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return success_content
            return fail_content
            
        mock_gen_content.side_effect = side_effect
        
        # Execute
        results, chart = await generate_report_sections(
            self.report,
            self.payload,
            self.db,
            llm_client=MagicMock(),
            llm_mode="openrouter",
            reset_chunks=True,
            raise_on_error=False
        )
        
        # Verify
        self.assertEqual(self.report.status, "failed")
        self.assertIn("only 2", self.report.error_message)
        self.assertIn("min 5", self.report.error_message)
        print("✅ Success: Report marked as failed when success count below threshold.")

    @patch("backend.app.services.report_workflow.build_chart_data")
    @patch("backend.app.services.report_workflow.build_report_context")
    @patch("backend.app.services.report_workflow.generate_section_content")
    @patch("backend.app.services.report_workflow.initialize_report_chunks")
    async def test_report_succeeds_above_threshold(self, mock_init_chunks, mock_gen_content, mock_context, mock_chart):
        # Setup mocks
        mock_init_chunks.return_value = {}
        mock_chart.return_value = {}
        mock_context.return_value = {"client": {"gender": "male"}}
        
        # Simulate 6 successful sections
        success_content = '[{"type":"paragraph","text":"success"}]'
        fail_content = '[{"type":"callout","variant":"error","title":"Ошибка генерации","content":"fail"}]'
        
        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 6:
                return success_content
            return fail_content
            
        mock_gen_content.side_effect = side_effect
        
        # Execute
        results, chart = await generate_report_sections(
            self.report,
            self.payload,
            self.db,
            llm_client=MagicMock(),
            llm_mode="openrouter",
            reset_chunks=True,
            raise_on_error=False
        )
        
        # Verify
        self.assertEqual(self.report.status, "completed")
        print("✅ Success: Report marked as completed when success count above threshold.")

if __name__ == "__main__":
    unittest.main()
