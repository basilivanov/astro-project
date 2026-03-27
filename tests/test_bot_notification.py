import unittest
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.append(os.getcwd())

from backend.app.services.notification import (
    get_notification_delivery_telemetry,
    send_bot_notification,
)


class TestBotNotificationRegression(unittest.IsolatedAsyncioTestCase):
    def test_delivery_telemetry_marks_blocked_chat_as_non_fatal(self):
        telemetry = get_notification_delivery_telemetry(delivered=False, status_code=403)
        self.assertEqual(telemetry["delivery_status"], "blocked_chat")
        self.assertTrue(telemetry["non_fatal"])
        self.assertEqual(telemetry["status_code"], 403)

    @patch("backend.app.services.notification.log_grace_event")
    @patch("httpx.AsyncClient.post")
    async def test_send_bot_notification_logs_non_fatal_blocked_chat(self, mock_post, mock_grace_event):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        result = await send_bot_notification(12345, "Blocked chat")

        self.assertFalse(result)
        self.assertEqual(mock_post.call_count, 1)
        blocked_events = [
            call.kwargs
            for call in mock_grace_event.call_args_list
            if call.args[:2] == ("warning", "END_BLOCK")
            and call.kwargs.get("block") == "POST_NOTIFY_REQUEST"
        ]
        self.assertTrue(blocked_events)
        self.assertEqual(blocked_events[-1]["delivery_status"], "blocked_chat")
        self.assertTrue(blocked_events[-1]["non_fatal"])
        self.assertEqual(blocked_events[-1]["status_code"], 403)

    @patch("backend.app.services.notification.log_grace_event")
    @patch("httpx.AsyncClient.post")
    async def test_send_bot_notification_logs_delivery_success_telemetry(self, mock_post, mock_grace_event):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        result = await send_bot_notification(12345, "Delivered")

        self.assertTrue(result)
        delivered_events = [
            call.kwargs
            for call in mock_grace_event.call_args_list
            if call.args[:2] == ("info", "END_BLOCK")
            and call.kwargs.get("block") == "POST_NOTIFY_REQUEST"
        ]
        self.assertTrue(delivered_events)
        self.assertEqual(delivered_events[-1]["delivery_status"], "delivered")
        self.assertFalse(delivered_events[-1]["non_fatal"])
        self.assertEqual(delivered_events[-1]["status_code"], 200)
