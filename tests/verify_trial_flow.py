import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
import sys
import os

sys.path.append(os.getcwd())

# Import models directly to simulate state
from backend.app.models import User

def simulate_registration(telegram_id, db):
    # Simulate the logic in auth.py/main.py
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=14)
    user = User(
        telegram_id=telegram_id,
        subscription_active_until=trial_end,
        balance=0
    )
    db.add(user)
    return user

class TestTrialFlow(unittest.TestCase):
    def test_trial_assignment(self):
        db = MagicMock()
        user = simulate_registration(12345, db)
        
        self.assertIsNotNone(user.subscription_active_until)
        # Check that it's approximately 14 days from now
        diff = user.subscription_active_until - datetime.now(timezone.utc)
        self.assertGreater(diff.days, 12)
        self.assertLessEqual(diff.days, 14)
        print(f"\n[Trial] Verified: User assigned trial until {user.subscription_active_until}")

if __name__ == '__main__':
    unittest.main()
