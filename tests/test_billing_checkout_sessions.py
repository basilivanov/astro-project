import json
import os
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.models import (
    Base,
    BillingCheckoutSession,
    ReportEntitlement,
    Subscription,
    Transaction,
    User,
)
from backend.app.routers.billing import (
    CreatePaymentRequest,
    get_checkout_session_status,
    initiate_payment,
)
from backend.app.services.billing import handle_payment_canceled, handle_payment_succeeded
from backend.app.services.one_off_entitlements import BillingKind, CheckoutSessionStatus


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user(db_session):
    user = User(telegram_id=100500, full_name="Billing Test User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_checkout_session(db_session, user, **overrides):
    checkout_session = BillingCheckoutSession(
        user_id=user.id,
        provider=overrides.get("provider", "yookassa"),
        status=overrides.get("status", "pending"),
        billing_kind=overrides.get("billing_kind", BillingKind.SUBSCRIPTION.value),
        product_code=overrides.get("product_code", "subscription"),
        report_type=overrides.get("report_type"),
        pack_id=overrides.get("pack_id"),
        amount=overrides.get("amount", 299.0),
        currency=overrides.get("currency", "RUB"),
        provider_payment_id=overrides.get("provider_payment_id"),
        provider_status=overrides.get("provider_status"),
        idempotence_key=overrides.get("idempotence_key", uuid.uuid4().hex),
        resume_token=overrides.get("resume_token", uuid.uuid4().hex),
        return_path=overrides.get("return_path"),
        draft_payload=overrides.get("draft_payload"),
    )
    db_session.add(checkout_session)
    db_session.commit()
    db_session.refresh(checkout_session)
    return checkout_session


@patch("backend.app.routers.billing.create_payment")
def test_initiate_payment_persists_checkout_session_with_resume_metadata(
    mock_create_payment,
    db_session,
    user,
):
    mock_create_payment.return_value = json.dumps(
        {
            "id": "pay_123",
            "status": "pending",
            "confirmation": {"confirmation_url": "https://pay.example/redirect"},
        }
    )

    with patch.dict(
        os.environ,
        {
            "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
            "PAYMENTS_MODE": "real",
            "WEBAPP_URL": "https://app.example.com",
        },
        clear=False,
    ):
        response = initiate_payment(
            CreatePaymentRequest(
                product_type="month_forecast",
                return_path="/create?type=month_forecast",
                draft_payload={"report_type": "month_forecast", "client_name": "Alice"},
            ),
            user=user,
            db=db_session,
        )

    checkout_session = db_session.query(BillingCheckoutSession).one()
    assert response["checkout_token"] == checkout_session.resume_token
    assert response["session_status"] == "pending"
    assert checkout_session.status == "pending"
    assert checkout_session.billing_kind == BillingKind.REPORT_UNLOCK.value
    assert checkout_session.product_code == "month_forecast"
    assert checkout_session.report_type == "month_forecast"
    assert checkout_session.return_path == "/create?type=month_forecast"
    assert json.loads(checkout_session.draft_payload)["client_name"] == "Alice"

    kwargs = mock_create_payment.call_args.kwargs
    assert kwargs["amount"] == 199.0
    assert kwargs["return_url"] == (
        f"https://app.example.com/billing/complete?checkout={checkout_session.resume_token}"
    )
    assert kwargs["idempotence_key"] == checkout_session.idempotence_key
    assert kwargs["metadata"]["checkout_session_id"] == str(checkout_session.id)
    assert kwargs["metadata"]["billing_kind"] == BillingKind.REPORT_UNLOCK.value
    assert kwargs["metadata"]["product_code"] == "month_forecast"
    assert kwargs["metadata"]["report_type"] == "month_forecast"


@patch("backend.app.routers.billing.create_payment")
def test_initiate_payment_normalizes_one_off_alias_product_type(
    mock_create_payment,
    db_session,
    user,
):
    mock_create_payment.return_value = json.dumps(
        {
            "id": "pay_alias_123",
            "status": "pending",
            "confirmation": {"confirmation_url": "https://pay.example/redirect"},
        }
    )

    with patch.dict(
        os.environ,
        {
            "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
            "PAYMENTS_MODE": "real",
        },
        clear=False,
    ):
        initiate_payment(
            CreatePaymentRequest(product_type="solar_return_master"),
            user=user,
            db=db_session,
        )

    checkout_session = db_session.query(BillingCheckoutSession).one()
    assert checkout_session.billing_kind == BillingKind.REPORT_UNLOCK.value
    assert checkout_session.product_code == "solar_return"
    assert checkout_session.report_type == "solar_return"

    kwargs = mock_create_payment.call_args.kwargs
    assert kwargs["amount"] == 199.0
    assert kwargs["metadata"]["product_type"] == "solar_return"
    assert kwargs["metadata"]["product_code"] == "solar_return"
    assert kwargs["metadata"]["report_type"] == "solar_return"


@patch("backend.app.routers.billing.log_checkout_status")
@patch("backend.app.routers.billing.log_checkout_payment_created")
@patch("backend.app.routers.billing.log_checkout_start")
@patch("backend.app.routers.billing.create_payment")
def test_initiate_payment_emits_catalog_events(
    mock_create_payment,
    mock_log_start,
    mock_log_payment_created,
    mock_log_status,
    db_session,
    user,
):
    mock_create_payment.return_value = json.dumps(
        {
            "id": "pay_catalog_1",
            "status": "pending",
            "confirmation": {"confirmation_url": "https://pay.example/redirect"},
        }
    )

    with patch.dict(
        os.environ,
        {
            "ENABLE_PERSISTENT_CHECKOUT_SESSIONS": "true",
            "PAYMENTS_MODE": "real",
            "WEBAPP_URL": "https://app.example.com",
        },
        clear=False,
    ):
        initiate_payment(
            CreatePaymentRequest(product_type="month_forecast"),
            user=user,
            db=db_session,
        )

    assert mock_log_start.call_count == 1
    assert mock_log_payment_created.call_count == 1
    assert mock_log_status.call_count == 1


def test_get_checkout_session_status_returns_owned_session(db_session, user):
    checkout_session = _create_checkout_session(
        db_session,
        user,
        billing_kind=BillingKind.REPORT_UNLOCK.value,
        product_code="natal_master",
        report_type="natal_master",
        return_path="/create?type=natal_master",
        draft_payload=json.dumps({"report_type": "natal_master"}),
    )

    response = get_checkout_session_status(checkout_session.resume_token, user=user, db=db_session)

    assert response["checkout_token"] == checkout_session.resume_token
    assert response["status"] == "pending"
    assert response["billing_kind"] == BillingKind.REPORT_UNLOCK.value
    assert response["product_code"] == "natal_master"
    assert response["has_draft_payload"] is True
    assert response["return_path"] == "/create?type=natal_master"


@patch("backend.app.routers.billing.log_catalog_event")
def test_get_checkout_session_status_logs_resume_ready(mock_log_event, db_session, user):
    checkout_session = _create_checkout_session(
        db_session,
        user,
        billing_kind=BillingKind.REPORT_UNLOCK.value,
        product_code="natal_master",
        report_type="natal_master",
        status=CheckoutSessionStatus.SUCCEEDED.value,
    )

    response = get_checkout_session_status(checkout_session.resume_token, user=user, db=db_session)

    assert response["checkout_token"] == checkout_session.resume_token
    assert response["status"] == CheckoutSessionStatus.SUCCEEDED.value
    events = [call.args[0] for call in mock_log_event.call_args_list]
    assert "catalog.checkout_resume_ready" in events


@patch("backend.app.services.referral_service.process_partner_reward")
@patch("backend.app.services.billing.log_analytics_event")
def test_handle_payment_succeeded_is_idempotent_for_checkout_session(
    mock_log_analytics_event,
    mock_process_partner_reward,
    db_session,
    user,
):
    checkout_session = _create_checkout_session(
        db_session,
        user,
        billing_kind=BillingKind.SUBSCRIPTION.value,
        product_code="subscription",
        provider_payment_id="pay_123",
    )

    payment_object = {
        "id": "pay_123",
        "status": "succeeded",
        "amount": {"value": "299.00", "currency": "RUB"},
        "payment_method": {"id": "card_123", "saved": False},
        "metadata": {
            "user_id": str(user.id),
            "is_recurring": "True",
            "product_type": "subscription",
            "checkout_session_id": str(checkout_session.id),
        },
    }

    handle_payment_succeeded(payment_object, db_session)
    db_session.refresh(user)
    first_subscription_end = user.subscription_active_until

    handle_payment_succeeded(payment_object, db_session)

    db_session.expire_all()
    refreshed_session = db_session.get(BillingCheckoutSession, checkout_session.id)
    refreshed_user = db_session.get(User, user.id)

    assert refreshed_session.status == "succeeded"
    assert refreshed_session.provider_payment_id == "pay_123"
    assert db_session.query(Transaction).filter(Transaction.type == "payment").count() == 1
    assert db_session.query(Subscription).count() == 1
    assert refreshed_user.subscription_active_until == first_subscription_end
    mock_process_partner_reward.assert_called_once()
    mock_log_analytics_event.assert_called_once()


def test_handle_payment_canceled_marks_checkout_session(db_session, user):
    checkout_session = _create_checkout_session(
        db_session,
        user,
        billing_kind=BillingKind.REPORT_UNLOCK.value,
        product_code="year_forecast",
        report_type="year_forecast",
        provider_payment_id="pay_cancel_1",
    )

    handle_payment_canceled(
        {
            "id": "pay_cancel_1",
            "status": "canceled",
            "metadata": {"checkout_session_id": str(checkout_session.id)},
            "cancellation_details": {"reason": "canceled_by_user"},
        },
        db_session,
    )

    db_session.refresh(checkout_session)
    assert checkout_session.status == "canceled"
    assert checkout_session.canceled_at is not None
    assert checkout_session.error_code == "payment_canceled"
    assert checkout_session.error_message == "canceled_by_user"


@patch("backend.app.services.referral_service.process_partner_reward")
@patch("backend.app.services.billing.log_analytics_event")
def test_handle_payment_succeeded_grants_report_unlock_entitlement(
    mock_log_analytics_event,
    mock_process_partner_reward,
    db_session,
    user,
):
    checkout_session = _create_checkout_session(
        db_session,
        user,
        billing_kind=BillingKind.REPORT_UNLOCK.value,
        product_code="month_forecast",
        report_type="month_forecast",
    )

    payment_object = {
        "id": "pay_report_unlock_1",
        "status": "succeeded",
        "amount": {"value": "199.00", "currency": "RUB"},
        "payment_method": {"id": "card_123", "saved": False},
        "metadata": {
            "user_id": str(user.id),
            "product_type": "month_forecast",
            "billing_kind": BillingKind.REPORT_UNLOCK.value,
            "product_code": "month_forecast",
            "report_type": "month_forecast",
            "checkout_session_id": str(checkout_session.id),
        },
    }

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
        },
        clear=False,
    ):
        handle_payment_succeeded(payment_object, db_session)

    db_session.expire_all()
    refreshed_user = db_session.get(User, user.id)
    refreshed_session = db_session.get(BillingCheckoutSession, checkout_session.id)
    entitlement = db_session.query(ReportEntitlement).one()

    assert refreshed_user.subscription_active_until is None
    assert refreshed_session.status == "succeeded"
    assert refreshed_session.entitlement_id == entitlement.id
    assert entitlement.user_id == user.id
    assert entitlement.report_type == "month_forecast"
    assert entitlement.status == "active"
    assert entitlement.source == "payment"
    assert entitlement.checkout_session_id == checkout_session.id
    assert db_session.query(Transaction).filter(Transaction.type == "payment").count() == 1
    assert db_session.query(Subscription).count() == 0
    mock_process_partner_reward.assert_called_once()
    mock_log_analytics_event.assert_called_once()


@patch("backend.app.services.referral_service.process_partner_reward")
@patch("backend.app.services.billing.log_analytics_event")
def test_handle_payment_succeeded_report_unlock_is_idempotent(
    mock_log_analytics_event,
    mock_process_partner_reward,
    db_session,
    user,
):
    checkout_session = _create_checkout_session(
        db_session,
        user,
        billing_kind=BillingKind.REPORT_UNLOCK.value,
        product_code="natal_master",
        report_type="natal_master",
        provider_payment_id="pay_report_unlock_dup",
    )

    payment_object = {
        "id": "pay_report_unlock_dup",
        "status": "succeeded",
        "amount": {"value": "199.00", "currency": "RUB"},
        "payment_method": {"id": "card_123", "saved": False},
        "metadata": {
            "user_id": str(user.id),
            "product_type": "natal_master",
            "billing_kind": BillingKind.REPORT_UNLOCK.value,
            "product_code": "natal_master",
            "report_type": "natal_master",
            "checkout_session_id": str(checkout_session.id),
        },
    }

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
        },
        clear=False,
    ):
        handle_payment_succeeded(payment_object, db_session)
        handle_payment_succeeded(payment_object, db_session)

    db_session.expire_all()
    refreshed_session = db_session.get(BillingCheckoutSession, checkout_session.id)

    assert refreshed_session.status == "succeeded"
    assert db_session.query(Transaction).filter(Transaction.type == "payment").count() == 1
    assert db_session.query(ReportEntitlement).count() == 1
    mock_process_partner_reward.assert_called_once()
    mock_log_analytics_event.assert_called_once()
