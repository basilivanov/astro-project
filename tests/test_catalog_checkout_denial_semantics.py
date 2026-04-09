from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import BackgroundTasks, HTTPException
from structlog.testing import capture_logs

from backend.app.main import B2CReportCreateRequest, create_b2c_report
from backend.app.services.one_off_entitlements import deny_access


def _build_user(**overrides):
    defaults = {
        "id": "user-1",
        "telegram_id": 123,
        "full_name": "Test User",
        "birth_date": "1990-01-01",
        "birth_time": "08:00",
        "birth_place": "Moscow",
        "birth_lat": 55.7558,
        "birth_lon": 37.6173,
        "birth_timezone": "Europe/Moscow",
        "birth_time_known": True,
        "current_location": "Moscow",
        "current_lat": 55.7558,
        "current_lon": 37.6173,
        "current_timezone": "Europe/Moscow",
        "is_test": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@patch("backend.app.services.access_control.resolve_report_access")
def test_create_b2c_report_denial_does_not_emit_catalog_error(mock_resolve_access):
    user = _build_user()
    db = MagicMock()
    db.rollback = MagicMock()

    access_decision = deny_access("natal_master", reason_code="payment_required")
    mock_resolve_access.return_value = access_decision

    payload = B2CReportCreateRequest(report_type="natal_master")
    background_tasks = BackgroundTasks()

    with capture_logs() as cap:
        try:
            create_b2c_report(payload, background_tasks, user=user, db=db)
        except HTTPException as exc:
            assert exc.status_code == 402
        else:  # pragma: no cover - safety for regression readability
            raise AssertionError("Expected create_b2c_report to raise HTTPException")

    events = [entry["event"] for entry in cap]
    assert "catalog.checkout_start" in events
    assert "catalog.checkout_decision" in events
    assert "catalog.checkout_denied" in events
    assert "catalog.error" not in events

    denied_event = next(entry for entry in cap if entry["event"] == "catalog.checkout_denied")
    assert denied_event["decision_allowed"] is False
    assert denied_event["decision_reason"] == "payment_required"
