import unittest
import sys
import os
import uuid
from unittest.mock import MagicMock

# Ensure backend path is available
sys.path.append(os.getcwd())

from backend.app.main import app
from backend.app.auth import get_current_user
from backend.app.db import get_db
from fastapi.testclient import TestClient

class TestReportContract(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.report_id = str(uuid.uuid4())

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_report_detail_no_markdown_key(self):
        # Setup mocks
        mock_user = MagicMock(id=uuid.uuid4())
        
        mock_report = MagicMock()
        mock_report.id = uuid.UUID(self.report_id)
        mock_report.user_id = mock_user.id
        mock_report.chunks = []
        mock_report.client.full_name = "Test Client"
        mock_report.report_type = "natal_master"
        mock_report.status = "completed"
        mock_report.created_at = MagicMock()
        mock_report.created_at.isoformat.return_value = "2026-02-10T06:00:00"
        
        db_session = MagicMock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_report
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: db_session

        # Execute
        response = self.client.get(f"/api/reports/{self.report_id}", headers={"X-Telegram-Auth": "test"})
        
        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("markdown", data, "Legacy 'markdown' key found in report detail API response!")
        print("✅ Success: 'markdown' key is absent from report detail API.")

if __name__ == "__main__":
    unittest.main()
