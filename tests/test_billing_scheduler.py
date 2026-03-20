import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
import sys
import os
import uuid

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.scheduler import check_expired_subscriptions
from backend.app.models import User, Subscription

class TestBillingScheduler(unittest.IsolatedAsyncioTestCase):
    @patch("backend.app.services.scheduler.SessionLocal")
    @patch("backend.app.services.scheduler.send_bot_notification", new_callable=AsyncMock)
    @patch("asyncio.sleep", side_effect=InterruptedError) # Break loop
    async def test_expired_subscription(self, mock_sleep, mock_notify, mock_session_cls):
        # Setup DB mock
        db = MagicMock()
        mock_session_cls.return_value = db
        
        # User & Sub
        user = User(id=uuid.uuid4(), telegram_id=123)
        # Expired 2 days ago
        expired_date = datetime.now(timezone.utc) - timedelta(days=2)
        user.subscription_active_until = expired_date
        
        sub = Subscription(id=uuid.uuid4(), status="active", user=user)
        
        # Mock Query
        # query(Subscription).join(User).filter...all() -> [sub]
        db.query.return_value.join.return_value.filter.return_value.filter.return_value.all.return_value = [sub]
        
        # Run
        try:
            await check_expired_subscriptions()
        except InterruptedError:
            pass # Expected
            
        # Verify
        self.assertEqual(sub.status, "inactive")
        mock_notify.assert_called_once()
        db.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
