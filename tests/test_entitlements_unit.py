import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.access_control import check_user_access, consume_access_if_needed
from backend.app.models import User, Transaction

class TestEntitlementsUnit(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.user = User(
            id="u1", 
            telegram_id=123, 
            is_partner=False, 
            is_test=False,
            subscription_active_until=None,
            birth_timezone="UTC",
            current_timezone="UTC"
        )

    def test_partner_bypass(self):
        self.user.is_partner = True
        self.assertTrue(check_user_access(self.user, "natal_master", self.db))

    def test_free_forecasts(self):
        # general_week should be free for everyone
        self.assertTrue(check_user_access(self.user, "general_week", self.db))
        self.assertTrue(check_user_access(self.user, "feed_daily", self.db))

    def test_subscription_active(self):
        self.user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=5)
        self.assertTrue(check_user_access(self.user, "natal_master", self.db))

    def test_subscription_expired(self):
        self.user.subscription_active_until = datetime.now(timezone.utc) - timedelta(days=1)
        self.assertFalse(check_user_access(self.user, "natal_master", self.db))

    def test_trial_active(self):
        self.user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=14)
        self.assertTrue(check_user_access(self.user, "natal_master", self.db))

    def test_horary_sub_active_quota_free(self):
        # sub active + quota_used=0 -> allow, no transaction
        self.user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=5)
        
        # Quota used = 0
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.side_effect = [q1, q1] # One for check, one for consume
        
        self.assertTrue(check_user_access(self.user, "horary", self.db))
        res = consume_access_if_needed(self.user, "horary", self.db)
        self.assertTrue(res)
        self.db.add.assert_not_called()

    def test_horary_sub_active_quota_used_has_credits(self):
        # sub active + quota_used=1 + credits>=1 -> allow, spend credit
        self.user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=5)
        
        # 1. Check access: quota=1, credits=1
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 1
        q2 = MagicMock()
        q2.filter.return_value.filter.return_value.scalar.return_value = 1
        
        # 2. Consume access: quota=1, credits=1
        q3 = MagicMock()
        q3.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 1
        q4 = MagicMock()
        q4.filter.return_value.filter.return_value.scalar.return_value = 1
        
        self.db.query.side_effect = [q1, q2, q3, q4]
        
        self.assertTrue(check_user_access(self.user, "horary", self.db))
        res = consume_access_if_needed(self.user, "horary", self.db)
        self.assertTrue(res)
        
        # Verify transaction added (credit spent)
        self.db.add.assert_called()
        args, _ = self.db.add.call_args
        obj = args[0]
        self.assertIsInstance(obj, Transaction)
        self.assertEqual(obj.amount, -1)

    def test_horary_sub_active_quota_used_no_credits(self):
        # sub active + quota_used=1 + credits=0 -> deny
        self.user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=5)
        
        # Quota used = 1, Credits = 0
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = 1
        q2 = MagicMock()
        q2.filter.return_value.filter.return_value.scalar.return_value = 0
        
        self.db.query.side_effect = [q1, q2]
        
        self.assertFalse(check_user_access(self.user, "horary", self.db))

    def test_horary_sub_inactive_has_credits(self):
        # sub inactive + credits>=1 -> allow, spend
        self.user.subscription_active_until = None
        
        # Check: credits=1
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.scalar.return_value = 1
        # Consume: credits=1
        q2 = MagicMock()
        q2.filter.return_value.filter.return_value.scalar.return_value = 1
        
        self.db.query.side_effect = [q1, q2]
        
        self.assertTrue(check_user_access(self.user, "horary", self.db))
        res = consume_access_if_needed(self.user, "horary", self.db)
        self.assertTrue(res)
        self.db.add.assert_called()

    def test_horary_sub_inactive_no_credits(self):
        # sub inactive + credits=0 -> deny
        self.user.subscription_active_until = None
        
        # Check: credits=0
        q1 = MagicMock()
        q1.filter.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.side_effect = [q1]
        
        self.assertFalse(check_user_access(self.user, "horary", self.db))

if __name__ == '__main__':
    unittest.main()