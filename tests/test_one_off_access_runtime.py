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
    Client,
    Report,
    ReportEntitlement,
    User,
)
from backend.app.services.access_control import consume_report_access, resolve_report_access
from backend.app.services.one_off_entitlements import (
    AccessGrantSource,
    BillingKind,
    EntitlementSource,
    build_report_unlock_snapshot,
)


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
    user = User(
        telegram_id=424242,
        full_name="One-Off Runtime User",
        birth_date="1990-01-01",
        birth_place="Moscow",
        birth_timezone="Europe/Moscow",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_resolve_report_access_allows_active_entitlement(db_session, user):
    entitlement = ReportEntitlement(
        user_id=user.id,
        report_type="month_forecast",
        status="active",
        source=EntitlementSource.PAYMENT.value,
    )
    db_session.add(entitlement)
    db_session.commit()
    db_session.refresh(entitlement)

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
        },
        clear=False,
    ):
        decision = resolve_report_access(user, "month_forecast", db_session)

    assert decision.allowed is True
    assert decision.granted_via == AccessGrantSource.REPORT_ENTITLEMENT
    assert decision.entitlement_id == str(entitlement.id)
    assert decision.remaining_unlocks == 1
    assert decision.legacy_subscription_applied is False


def test_resolve_report_access_normalizes_one_off_aliases(db_session, user):
    entitlement = ReportEntitlement(
        user_id=user.id,
        report_type="synastry",
        status="active",
        source=EntitlementSource.PAYMENT.value,
    )
    db_session.add(entitlement)
    db_session.commit()

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
        },
        clear=False,
    ):
        decision = resolve_report_access(user, "synastry_master", db_session)

    assert decision.allowed is True
    assert decision.report_type == "synastry"
    assert decision.granted_via == AccessGrantSource.REPORT_ENTITLEMENT


def test_consume_report_access_links_report_entitlement_and_checkout_session(db_session, user):
    client = Client(
        full_name="One-Off Runtime User",
        user_id=user.id,
        birth_datetime=None,
        birth_location="Moscow",
        birth_timezone="Europe/Moscow",
        is_test=False,
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)

    checkout_session = BillingCheckoutSession(
        user_id=user.id,
        provider="mock",
        status="succeeded",
        billing_kind=BillingKind.REPORT_UNLOCK.value,
        product_code="month_forecast",
        report_type="month_forecast",
        amount=199.0,
        currency="RUB",
        idempotence_key=uuid.uuid4().hex,
        resume_token=uuid.uuid4().hex,
        provider_payment_id="pay_runtime_1",
    )
    db_session.add(checkout_session)
    db_session.commit()
    db_session.refresh(checkout_session)

    entitlement = ReportEntitlement(
        user_id=user.id,
        report_type="month_forecast",
        status="active",
        source=EntitlementSource.PAYMENT.value,
        checkout_session_id=checkout_session.id,
    )
    db_session.add(entitlement)
    db_session.commit()
    db_session.refresh(entitlement)

    report = Report(
        client_id=client.id,
        user_id=user.id,
        report_type="month_forecast",
        status="in_progress",
        paid=False,
        is_test=False,
    )
    db_session.add(report)
    db_session.flush()

    with patch.dict(
        os.environ,
        {
            "ENABLE_ONE_OFF_ENTITLEMENTS_RUNTIME": "true",
            "LEGACY_PREMIUM_SUBSCRIPTION_ACCESS": "false",
        },
        clear=False,
    ):
        decision = resolve_report_access(user, "month_forecast", db_session)
        consume_report_access(user, report, db_session, decision=decision)
        db_session.commit()

    db_session.refresh(report)
    db_session.refresh(entitlement)
    db_session.refresh(checkout_session)

    assert report.access_source == AccessGrantSource.REPORT_ENTITLEMENT.value
    assert report.entitlement_id == entitlement.id
    assert report.checkout_session_id == checkout_session.id
    assert report.paid is True
    assert entitlement.status == "consumed"
    assert entitlement.consumed_report_id == report.id
    assert checkout_session.resumed_report_id == report.id
    assert checkout_session.status == "resumed"


def test_build_report_unlock_snapshot_returns_zero_filled_counts(db_session, user):
    db_session.add(
        ReportEntitlement(
            user_id=user.id,
            report_type="year_forecast",
            status="active",
            source=EntitlementSource.PAYMENT.value,
        )
    )
    db_session.add(
        ReportEntitlement(
            user_id=user.id,
            report_type="year_forecast",
            status="active",
            source=EntitlementSource.PAYMENT.value,
        )
    )
    db_session.commit()

    snapshot = build_report_unlock_snapshot(db_session, user_id=user.id)

    assert snapshot["year_forecast"] == 2
    assert snapshot["month_forecast"] == 0
    assert snapshot["natal_master"] == 0
