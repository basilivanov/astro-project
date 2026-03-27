import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import sys
import os
import uuid

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.referral_service import process_referral, process_partner_reward
from backend.app.models import User, Referral, Transaction

class TestReferralFlow(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        
    def test_user_referral_days(self):
        # Setup users
        referrer = User(id=uuid.uuid4(), is_partner=False, subscription_active_until=None)
        referee = User(id=uuid.uuid4(), is_partner=False, subscription_active_until=None)
        
        # Mock Query object
        mock_query = MagicMock()
        # Ensure filter() returns the same mock_query to support chaining
        mock_query.filter.return_value = mock_query
        
        # Configure side_effect for first()
        # Calls:
        # 1. User (referrer)
        # 2. User (referee)
        # 3. Referral (existing check) -> None
        mock_query.first.side_effect = [referrer, referee, None]
        
        # Make db.query return this mock_query
        self.db.query.return_value = mock_query
        
        # Process
        res = process_referral(referrer.id, referee.id, self.db)
        
        # Verify
        self.assertTrue(res)
        self.assertIsNotNone(referee.subscription_active_until) # Trial given
        self.assertIsNotNone(referrer.subscription_active_until) # Reward given
        self.db.add.assert_called() # Referral record created

    def test_partner_referral_money(self):
        # Setup
        partner = User(id=uuid.uuid4(), is_partner=True, balance=Decimal(0))
        payer = User(id=uuid.uuid4())
        
        # Mock Referral Link
        ref_link = Referral(referrer_id=partner.id, referee_id=payer.id)
        
        # Mock Query object
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        
        # Calls in process_partner_reward:
        # 1. Referral (by referee_id) -> ref_link
        # 2. User (referrer) -> partner
        mock_query.first.side_effect = [ref_link, partner]
        
        self.db.query.return_value = mock_query
        
        # Process Payment 1000 RUB
        process_partner_reward(payer.id, 1000.0, self.db)
        
        # Verify
        # 20% of 1000 = 200
        self.assertEqual(partner.balance, 200)
        self.db.add.assert_called() # Transaction added

    def test_partner_reward_idempotent_when_already_rewarded(self):
        partner = User(id=uuid.uuid4(), is_partner=True, balance=Decimal(50))
        payer = User(id=uuid.uuid4())
        ref_link = Referral(referrer_id=partner.id, referee_id=payer.id, status="rewarded")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [ref_link]
        self.db.query.return_value = mock_query

        process_partner_reward(payer.id, 1000.0, self.db)

        self.assertEqual(partner.balance, Decimal(50))
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
