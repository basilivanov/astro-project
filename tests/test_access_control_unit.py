# ############################################################################
# AI_HEADER: TEST_ACCESS_CONTROL_UNIT
# ROLE: Unit test for access control logic.
# ############################################################################

import unittest
import sys
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone

# Mock dependencies before import
sys.modules["backend.app.models"] = MagicMock()
from backend.app.services.access_control import check_user_access

class MockUser:
    def __init__(self, is_partner=False, is_test=False, subscription_active_until=None, telegram_id=123):
        self.is_partner = is_partner
        self.is_test = is_test
        self.subscription_active_until = subscription_active_until
        self.telegram_id = telegram_id

class TestAccessControl(unittest.TestCase):
    def test_partner_access(self):
        user = MockUser(is_partner=True)
        self.assertTrue(check_user_access(user))

    def test_active_subscription(self):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        user = MockUser(subscription_active_until=future)
        self.assertTrue(check_user_access(user))

    def test_expired_subscription(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        user = MockUser(subscription_active_until=past)
        self.assertFalse(check_user_access(user))

    def test_no_subscription(self):
        user = MockUser(subscription_active_until=None)
        self.assertFalse(check_user_access(user))

if __name__ == '__main__':
    unittest.main()
