import unittest
from unittest.mock import MagicMock, patch
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.notification import send_bot_notification

class TestNotificationMock(unittest.IsolatedAsyncioTestCase):
    @patch("httpx.AsyncClient.post")
    async def test_send_success(self, mock_post):
        # Setup mock for successful Telegram API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response
        
        res = await send_bot_notification(12345, "Test message")
        self.assertTrue(res)
        print("\n[Notification] Verified: Successfully sent via mock (200 OK)")

    @patch("httpx.AsyncClient.post")
    async def test_send_retry_on_5xx(self, mock_post):
        # Mock 500 then 200
        mock_500 = MagicMock(); mock_500.status_code = 500
        mock_200 = MagicMock(); mock_200.status_code = 200; mock_200.json.return_value = {"ok": True}
        mock_post.side_effect = [mock_500, mock_200]
        
        res = await send_bot_notification(12345, "Retry message")
        self.assertTrue(res)
        self.assertEqual(mock_post.call_count, 2)
        print("\n[Notification] Verified: Retried on 5xx and succeeded.")

    @patch("httpx.AsyncClient.post")
    async def test_send_abort_on_403(self, mock_post):
        # Mock 403 (User blocked bot)
        mock_403 = MagicMock(); mock_403.status_code = 403
        mock_post.return_value = mock_403
        
        res = await send_bot_notification(12345, "Abort message")
        self.assertFalse(res)
        self.assertEqual(mock_post.call_count, 1) # Should not retry 403
        print("\n[Notification] Verified: Aborted on 403 (expected behavior).")

if __name__ == "__main__":
    unittest.main()