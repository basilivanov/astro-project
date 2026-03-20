import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ############################################################################
# AI_HEADER: TEST_ONE_OFF_RUNTIME_SMOKE
# ROLE: Targeted HTTP smoke coverage for checkout -> webhook -> entitlement -> consume.
# ############################################################################

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
TEST_BOT_TOKEN = "test_token_for_one_off_runtime_smoke"
os.environ["TELEGRAM_BOT_TOKEN"] = TEST_BOT_TOKEN
os.environ["ENVIRONMENT"] = "test"

from backend.app.main import app, get_db
from backend.app.models import (
    Base,
    BillingCheckoutSession,
    Report,
    ReportEntitlement,
    Subscription,
    Transaction,
    User,
)
from backend.app.services.one_off_entitlements import AccessGrantSource, BillingKind
from tests.utils import sign_init_data


def _build_auth_headers(telegram_id: int) -> dict[str, str]:
    init_data = sign_init_data(
        {
            "id": telegram_id,
            "first_name": "Smoke",
            "last_name": "Tester",
            "username": f"smoke_{telegram_id}",
        },
        TEST_BOT_TOKEN,
    )
    return {"X-Telegram-Auth": init_data}


def _seed_profiled_user(db_session, telegram_id: int) -> User:
    user = User(
        telegram_id=telegram_id,
        username=f"smoke_{telegram_id}",
        full_name="Smoke Tester",
        birth_date="1990-01-01",
        birth_time="12:00",
        birth_time_known=True,
        birth_place="Moscow",
        birth_lat=55.75,
        birth_lon=37.61,
        birth_timezone="Europe/Moscow",
        current_timezone="Europe/Moscow",
        subscription_active_until=None,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with patch("backend.app.main.start_scheduler", new=AsyncMock(return_value=None)), patch(
        "backend.app.main.log_analytics_event"
    ), patch("backend.app.services.billing.log_analytics_event"), patch(
        "backend.app.services.referral_service.process_partner_reward"
    ), patch(
        "backend.app.main.run_report_generation",
        new=lambda *args, **kwargs: None,
    ):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


def test_checkout_webhook_entitlement_consume_smoke(client, db_session):
    user = _seed_profiled_user(db_session, telegram_id=550001)
    headers = _build_auth_headers(user.telegram_id)

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
            "WEBAPP_URL": "https://app.example.com",
            "PAYMENTS_MODE": "real",
        },
        clear=False,
    ), patch("backend.app.routers.billing.create_payment") as mock_create_payment:
        mock_create_payment.return_value = json.dumps(
            {
                "id": "pay_smoke_month_1",
                "status": "pending",
                "confirmation": {
                    "confirmation_url": "https://pay.example.com/confirm/pay_smoke_month_1"
                },
            }
        )

        pay_response = client.post(
            "/api/billing/pay",
            headers=headers,
            json={
                "product_type": "month_forecast",
                "return_path": "/create?type=month_forecast",
                "draft_payload": {
                    "report_type": "month_forecast",
                    "focus_area": "career",
                },
            },
        )

        assert pay_response.status_code == 200
        pay_data = pay_response.json()
        assert pay_data["session_status"] == "pending"
        assert pay_data["url"] == "https://pay.example.com/confirm/pay_smoke_month_1"

        checkout_session = db_session.query(BillingCheckoutSession).one()
        checkout_session_id = checkout_session.id
        assert checkout_session.status == "pending"
        assert checkout_session.billing_kind == BillingKind.REPORT_UNLOCK.value
        assert checkout_session.product_code == "month_forecast"
        assert checkout_session.report_type == "month_forecast"
        assert checkout_session.return_path == "/create?type=month_forecast"
        assert json.loads(checkout_session.draft_payload) == {
            "report_type": "month_forecast",
            "focus_area": "career",
        }

        create_payment_kwargs = mock_create_payment.call_args.kwargs
        assert create_payment_kwargs["return_url"] == (
            f"https://app.example.com/billing/complete?checkout={checkout_session.resume_token}"
        )
        assert create_payment_kwargs["metadata"]["checkout_session_id"] == str(checkout_session.id)
        assert create_payment_kwargs["metadata"]["billing_kind"] == BillingKind.REPORT_UNLOCK.value
        assert create_payment_kwargs["metadata"]["report_type"] == "month_forecast"

        session_response = client.get(
            f"/api/billing/sessions/{checkout_session.resume_token}",
            headers=headers,
        )
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert session_data["status"] == "pending"
        assert session_data["billing_kind"] == BillingKind.REPORT_UNLOCK.value
        assert session_data["product_code"] == "month_forecast"
        assert session_data["return_path"] == "/create?type=month_forecast"
        assert session_data["has_draft_payload"] is True
        assert session_data["entitlement_id"] is None

        webhook_payload = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "pay_smoke_month_1",
                "status": "succeeded",
                "amount": {"value": "199.00", "currency": "RUB"},
                "payment_method": {"id": "card_smoke_1", "saved": False},
                "metadata": {
                    "user_id": str(user.id),
                    "product_type": "month_forecast",
                    "billing_kind": BillingKind.REPORT_UNLOCK.value,
                    "product_code": "month_forecast",
                    "report_type": "month_forecast",
                    "checkout_session_id": str(checkout_session.id),
                },
            },
        }

        webhook_response = client.post("/api/billing/webhook", json=webhook_payload)
        assert webhook_response.status_code == 200
        assert webhook_response.json() == {"status": "ok"}

        unlocked_profile = client.get("/api/users/me", headers=headers)
        assert unlocked_profile.status_code == 200
        assert unlocked_profile.json()["report_unlocks"]["month_forecast"] == 1

        session_after_webhook = client.get(
            f"/api/billing/sessions/{checkout_session.resume_token}",
            headers=headers,
        )
        assert session_after_webhook.status_code == 200
        assert session_after_webhook.json()["status"] == "succeeded"
        assert session_after_webhook.json()["entitlement_id"] is not None
        assert session_after_webhook.json()["resumed_report_id"] is None

        assert db_session.query(Transaction).filter(Transaction.type == "payment").count() == 1
        assert db_session.query(Subscription).count() == 0

        create_report_response = client.post(
            "/api/reports/create",
            headers=headers,
            json={"report_type": "month_forecast"},
        )
        assert create_report_response.status_code == 200
        report_id = uuid.UUID(create_report_response.json()["report_id"])

        db_session.expire_all()
        report = db_session.query(Report).filter(Report.id == report_id).one()
        entitlement = db_session.query(ReportEntitlement).one()
        checkout_session = db_session.get(BillingCheckoutSession, checkout_session_id)

        assert report.access_source == AccessGrantSource.REPORT_ENTITLEMENT.value
        assert report.entitlement_id == entitlement.id
        assert report.checkout_session_id == checkout_session.id
        assert report.paid is True
        assert entitlement.status == "consumed"
        assert entitlement.consumed_report_id == report.id
        assert checkout_session.status == "resumed"
        assert checkout_session.resumed_report_id == report.id

        consumed_profile = client.get("/api/users/me", headers=headers)
        assert consumed_profile.status_code == 200
        assert consumed_profile.json()["report_unlocks"]["month_forecast"] == 0

        second_create_response = client.post(
            "/api/reports/create",
            headers=headers,
            json={"report_type": "month_forecast"},
        )
        assert second_create_response.status_code == 402


def test_users_me_exposes_structured_report_access_snapshot(client, db_session):
    user = _seed_profiled_user(db_session, telegram_id=550004)
    user.subscription_active_until = datetime.now(timezone.utc) + timedelta(days=30)
    db_session.add(user)
    db_session.add(
        ReportEntitlement(
            user_id=user.id,
            report_type="month_forecast",
            status="active",
            source="payment",
        )
    )
    db_session.commit()

    headers = _build_auth_headers(user.telegram_id)

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
        },
        clear=False,
    ):
        profile_response = client.get("/api/users/me", headers=headers)

    assert profile_response.status_code == 200
    profile = profile_response.json()

    assert profile["can_access_premium"] is True
    assert profile["report_unlocks"]["month_forecast"] == 1
    assert profile["report_access"]["month_forecast"] == {
        "allowed": True,
        "granted_via": AccessGrantSource.REPORT_ENTITLEMENT.value,
        "remaining_unlocks": 1,
        "reason_code": "ok",
        "legacy_subscription_applied": False,
    }
    assert profile["report_access"]["year_forecast"] == {
        "allowed": False,
        "granted_via": None,
        "remaining_unlocks": 0,
        "reason_code": "payment_required",
        "legacy_subscription_applied": False,
    }
    assert profile["report_access"]["natal_master"]["allowed"] is False


def test_duplicate_webhook_keeps_single_unlock(client, db_session):
    user = _seed_profiled_user(db_session, telegram_id=550002)
    headers = _build_auth_headers(user.telegram_id)

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
            "PAYMENTS_MODE": "real",
        },
        clear=False,
    ), patch("backend.app.routers.billing.create_payment") as mock_create_payment:
        mock_create_payment.return_value = json.dumps(
            {
                "id": "pay_smoke_year_dup",
                "status": "pending",
                "confirmation": {
                    "confirmation_url": "https://pay.example.com/confirm/pay_smoke_year_dup"
                },
            }
        )

        pay_response = client.post(
            "/api/billing/pay",
            headers=headers,
            json={"product_type": "year_forecast"},
        )
        assert pay_response.status_code == 200
        checkout_session = db_session.query(BillingCheckoutSession).one()

        webhook_payload = {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "pay_smoke_year_dup",
                "status": "succeeded",
                "amount": {"value": "499.00", "currency": "RUB"},
                "payment_method": {"id": "card_smoke_2", "saved": False},
                "metadata": {
                    "user_id": str(user.id),
                    "product_type": "year_forecast",
                    "billing_kind": BillingKind.REPORT_UNLOCK.value,
                    "product_code": "year_forecast",
                    "report_type": "year_forecast",
                    "checkout_session_id": str(checkout_session.id),
                },
            },
        }

        first_webhook = client.post("/api/billing/webhook", json=webhook_payload)
        second_webhook = client.post("/api/billing/webhook", json=webhook_payload)
        assert first_webhook.status_code == 200
        assert second_webhook.status_code == 200

        db_session.expire_all()
        checkout_session = db_session.get(BillingCheckoutSession, checkout_session.id)

        assert checkout_session.status == "succeeded"
        assert db_session.query(Transaction).filter(Transaction.type == "payment").count() == 1
        assert db_session.query(ReportEntitlement).count() == 1

        profile_response = client.get("/api/users/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["report_unlocks"]["year_forecast"] == 1

        session_response = client.get(
            f"/api/billing/sessions/{checkout_session.resume_token}",
            headers=headers,
        )
        assert session_response.status_code == 200
        assert session_response.json()["status"] == "succeeded"
        assert session_response.json()["entitlement_id"] is not None
