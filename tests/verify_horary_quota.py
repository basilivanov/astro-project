import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.access_control import check_user_access, consume_access_if_needed, get_local_week_start_utc
from backend.app.models import User, Transaction, Report

class TestHoraryQuota(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user = User(id="u1", telegram_id=123, is_partner=False, is_test=False)
        self.user.subscription_active_until = None
        self.user.birth_timezone = "UTC"
        self.user.current_timezone = "UTC"

    def test_subscriber_free_quota(self):
        # Active subscription
        self.user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Mock 0 reports this week
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 0
        
        # We call access check then consume, both query quota
        self.db.query.side_effect = [q1, q1]
        
        # Check Access
        self.assertTrue(check_user_access(self.user, "horary", self.db))
        
        # Consume
        self.assertTrue(consume_access_if_needed(self.user, "horary", self.db))
        # Should NOT add transaction (uses free quota)
        self.db.add.assert_not_called()
        print("\n[Quota] Subscriber free question OK")

    def test_subscriber_quota_used_requires_credits(self):
        # Active subscription
        self.user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Mock 1 report this week (Quota used) -> q1
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 1
        
        # Mock 0 credits -> q2
        q2 = MagicMock()
        q2.filter.return_value.filter.return_value.scalar.return_value = 0
        
        self.db.query.side_effect = [q1, q2]
        
        self.assertFalse(check_user_access(self.user, "horary", self.db))
        print("[Quota] Subscriber quota exhausted OK")

    def test_guest_no_free_quota(self):
        # NO subscription
        self.user.subscription_active_until = None
        
        # Mock 0 credits -> q1 (only credit check is performed for guests)
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.scalar.return_value = 0
        
        self.db.query.side_effect = [q1]
        
        # Access should be denied even if quota_used would be 0
        self.assertFalse(check_user_access(self.user, "horary", self.db))
        print("[Quota] Guest no free quota OK")

    def test_guest_with_credits(self):
        # NO subscription
        self.user.subscription_active_until = None
        
        # Mock 5 credits -> q1
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.scalar.return_value = 5
        
        self.db.query.side_effect = [q1]
        
        self.assertTrue(check_user_access(self.user, "horary", self.db))
        
        # Consume
        q2 = MagicMock()
        q2.filter.return_value.filter.return_value.scalar.return_value = 5
        self.db.query.side_effect = [q2] # Reset side effect for consume call
        res = consume_access_if_needed(self.user, "horary", self.db)
        
        self.assertTrue(res)
        self.db.add.assert_called()
        print("[Quota] Guest with credits OK")

if __name__ == '__main__':
    unittest.main()
