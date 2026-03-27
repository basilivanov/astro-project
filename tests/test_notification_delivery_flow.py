from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services import notification


def test_send_report_ready_notification_delegates_and_emits_trace() -> None:
    with patch.object(notification, "send_bot_notification", new=AsyncMock(return_value=True)) as mock_send, patch.object(
        notification, "log_grace_event"
    ) as mock_log:
        ok = asyncio.run(notification.send_report_ready_notification(
            12345,
            "Your report is ready",
            image_url="https://example.com/report.png",
            correlation_id="cid-ready",
            notification_id="notif-ready",
        ))

    assert ok is True
    mock_send.assert_awaited_once_with(
        12345,
        "Your report is ready",
        image_url="https://example.com/report.png",
        correlation_id="cid-ready",
        notification_id="notif-ready",
    )
    logged_events = [entry.args[:2] for entry in mock_log.call_args_list]
    assert ("info", "START_CONTRACT") in logged_events
    assert ("info", "START_BLOCK") in logged_events
    assert ("info", "END_BLOCK") in logged_events
    assert ("info", "END_CONTRACT") in logged_events
    delegate_end = next(
        entry.kwargs
        for entry in mock_log.call_args_list
        if entry.args[:2] == ("info", "END_BLOCK")
        and entry.kwargs.get("contract") == "send_report_ready_notification"
    )
    assert delegate_end["block"] == "DELEGATE_DELIVERY"
    assert delegate_end["label"] == "report_ready"
    assert delegate_end["outcome"] == "delivered"


def test_send_failure_notification_preserves_failure_outcome() -> None:
    with patch.object(notification, "send_bot_notification", new=AsyncMock(return_value=False)) as mock_send, patch.object(
        notification, "log_grace_event"
    ) as mock_log:
        ok = asyncio.run(notification.send_failure_notification(
            67890,
            "Report generation failed",
            correlation_id="cid-failure",
            notification_id="notif-failure",
        ))

    assert ok is False
    mock_send.assert_awaited_once_with(
        67890,
        "Report generation failed",
        correlation_id="cid-failure",
        notification_id="notif-failure",
    )
    end_events = [entry for entry in mock_log.call_args_list if entry.args[:2] == ("warning", "END_CONTRACT")]
    assert end_events, "expected warning END_CONTRACT log"
    assert any(
        entry.kwargs.get("contract") == "send_failure_notification"
        and entry.kwargs.get("label") == "report_failure"
        and entry.kwargs.get("outcome") == "not_delivered"
        for entry in end_events
    )


def test_enqueue_notification_job_logs_queue_before_delivery() -> None:
    with patch.object(notification, "send_bot_notification", new=AsyncMock(return_value=True)) as mock_send, patch.object(
        notification, "log_grace_event"
    ) as mock_log:
        ok = asyncio.run(notification.enqueue_notification_job(
            24680,
            "Queued message",
            label="report_ready_job",
            image_url="https://example.com/queued.png",
            correlation_id="cid-enqueue",
            notification_id="notif-enqueue",
        ))

    assert ok is True
    mock_send.assert_awaited_once_with(
        24680,
        "Queued message",
        image_url="https://example.com/queued.png",
        correlation_id="cid-enqueue",
        notification_id="notif-enqueue",
    )
    queue_calls = [
        entry
        for entry in mock_log.call_args_list
        if entry.kwargs.get("contract") == "enqueue_notification_job"
        and entry.kwargs.get("block") == "QUEUE_NOTIFICATION_JOB"
    ]
    assert [entry.args[:2] for entry in queue_calls] == [
        ("info", "START_BLOCK"),
        ("info", "END_BLOCK"),
    ]
    assert queue_calls[1].kwargs["outcome"] == "queued"
    assert queue_calls[1].kwargs["label"] == "report_ready_job"


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"delivered": True, "status_code": 200, "attempt": 1}, {"delivery_status": "delivered", "non_fatal": False, "status_code": 200, "attempt": 1}),
        ({"delivered": False, "status_code": 403}, {"delivery_status": "blocked_chat", "non_fatal": True, "status_code": 403}),
        ({"delivered": False, "status_code": 404}, {"delivery_status": "chat_not_found", "non_fatal": True, "status_code": 404}),
        ({"delivered": False, "status_code": 503, "attempt": 2}, {"delivery_status": "server_error", "non_fatal": False, "status_code": 503, "attempt": 2}),
        ({"delivered": False, "error": "boom"}, {"delivery_status": "network_error", "non_fatal": False, "error": "boom"}),
        ({"delivered": False}, {"delivery_status": "failed", "non_fatal": False}),
    ],
)
def test_get_notification_delivery_telemetry_variants(kwargs: dict[str, object], expected: dict[str, object]) -> None:
    assert notification.get_notification_delivery_telemetry(**kwargs) == expected
