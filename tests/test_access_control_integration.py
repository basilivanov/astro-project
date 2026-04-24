import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys
import os
import uuid

sys.path.append(os.getcwd())

from backend.app.main import app, get_db
from backend.app.auth import get_current_user
from backend.app.models import User, Client
from backend.app.services.one_off_entitlements import allow_access, deny_access, AccessGrantSource

class TestAccessControlIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user = User(
            id=uuid.uuid4(),
            telegram_id=123,
            is_partner=False,
            is_test=False,
            subscription_active_until=None,
            birth_date="2000-01-01",
            birth_place="Moscow"
        )

    @patch("backend.app.routers.b2c_reports.upsert_client_from_payload")
    @patch("backend.app.services.access_control.consume_report_access")
    @patch("backend.app.services.access_control.resolve_report_access")
    def test_report_create_allow(self, mock_resolve, mock_consume, mock_upsert):
        mock_resolve.return_value = allow_access("horary", AccessGrantSource.CREDITS)
        mock_upsert.return_value = Client(id=uuid.uuid4())
        
        app.dependency_overrides[get_current_user] = lambda: self.user
        
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        payload = {
            "client_name": "Test",
            "birth_date": "2000-01-01",
            "birth_location": "Moscow",
            "report_type": "horary"
        }
        
        response = self.client.post("/api/reports/create", json=payload)
        
        app.dependency_overrides = {}
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_resolve.called)
        self.assertTrue(mock_consume.called)
        print("\n[Integration] Report Create ALLOW verified.")

    @patch("backend.app.services.access_control.resolve_report_access")
    def test_report_create_deny(self, mock_resolve):
        mock_resolve.return_value = deny_access("natal_master")
        app.dependency_overrides[get_current_user] = lambda: self.user
        app.dependency_overrides[get_db] = lambda: MagicMock()
        
        response = self.client.post(
            "/api/reports/create",
            json={
                "client_name": "Test",
                "birth_date": "2000-01-01",
                "birth_location": "Moscow",
                "report_type": "natal_master"
            }
        )
        
        app.dependency_overrides = {}
        self.assertEqual(response.status_code, 402)
        print("\n[Integration] Report Create DENY verified.")

    @patch("backend.app.routers.b2c_reports.upsert_client_from_payload")
    @patch("backend.app.services.access_control.resolve_report_access")
    def test_synastry_requires_partner_birth_inputs(self, mock_resolve, mock_upsert):
        mock_resolve.return_value = allow_access("synastry", AccessGrantSource.SUBSCRIPTION)
        app.dependency_overrides[get_current_user] = lambda: self.user
        app.dependency_overrides[get_db] = lambda: MagicMock()

        response = self.client.post(
            "/api/reports/create",
            json={
                "report_type": "synastry",
                "partner_name": "Partner",
            },
        )

        app.dependency_overrides = {}

        self.assertEqual(response.status_code, 400)
        self.assertIn("partner birth date/time", response.json()["detail"])
        self.assertFalse(mock_upsert.called)
        print("\n[Integration] Synastry input validation verified.")

if __name__ == "__main__":
    unittest.main()
