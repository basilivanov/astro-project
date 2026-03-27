# ############################################################################
# AI_HEADER: TEST_REFERRAL_PARTNER_REWARD
# ROLE: Regression coverage for partner referral payout guardrails and telemetry.
# DEPENDENCIES: pytest, backend.app.services.referral_service
# ############################################################################

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
sys.path.append(os.getcwd())

from backend.app.db import SessionLocal
from backend.app.models import Referral, Transaction, User
from backend.app.services import referral_service


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_test_user(db_session, *, is_partner=False, subscription_active_until=None) -> User:
    tg_id = int(datetime.now(timezone.utc).timestamp() * 1000) + int(uuid.uuid4().int % 10000)
    user = User(
        telegram_id=tg_id,
        full_name=f"Referral Partner User {tg_id}",
        is_partner=is_partner,
        subscription_active_until=subscription_active_until,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_partner_referral(db_session, *, status="active"):
    partner = create_test_user(db_session, is_partner=True)
    referee = create_test_user(db_session, is_partner=False)
    referral = Referral(
        referrer_id=partner.id,
        referee_id=referee.id,
        reward_type="money",
        status=status,
    )
    db_session.add(referral)
    db_session.commit()
    db_session.refresh(referral)
    return partner, referee, referral


def test_partner_signup_keeps_money_reward_pending_after_15_days(db_session, monkeypatch):
    partner = create_test_user(db_session, is_partner=True)
    referee = create_test_user(db_session, is_partner=False)
    events = []

    def fake_log(level, event, **fields):
        events.append((level, event, fields))

    monkeypatch.setattr(referral_service, "log_grace_event", fake_log)

    now = datetime.now(timezone.utc)
    original_datetime = referral_service.datetime

    class FixedDateTime:
        @staticmethod
        def now(tz=None):
            return now if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(referral_service, "datetime", FixedDateTime)
    try:
        result = referral_service.process_referral_signup(
            partner.id,
            referee.id,
            db_session,
            correlation_id="corr-partner-signup",
        )
    finally:
        monkeypatch.setattr(referral_service, "datetime", original_datetime)

    assert result is True

    db_session.refresh(partner)
    db_session.refresh(referee)
    referral = db_session.query(Referral).filter(Referral.referee_id == referee.id).one()

    assert partner.subscription_active_until is None
    assert referee.subscription_active_until == now + timedelta(days=14)
    assert referral.reward_type == "money"
    assert referral.status == "active"

    assert [event for _, event, _ in events] == [
        "referral.signup_edge_created",
        "referral.referee_reward_applied",
        "referral.partner_reward_pending",
        "referral.signup_processed",
    ]
    assert events[2][2]["result"] == "pending"
    assert events[2][2]["referrer_id"] == str(partner.id)


def test_partner_reward_double_credit_guard_keeps_single_transaction(db_session, monkeypatch):
    partner, referee, referral = create_partner_referral(db_session, status="active")
    events = []

    def fake_log(level, event, **fields):
        events.append((level, event, fields))

    monkeypatch.setattr(referral_service, "log_grace_event", fake_log)
    monkeypatch.setattr(referral_service, "notify_partner_reward", lambda **_: None)

    referral_service.process_partner_reward(
        referee.id,
        1000.0,
        db_session,
        correlation_id="corr-credit-1",
    )
    db_session.refresh(partner)
    db_session.refresh(referral)

    assert float(partner.balance) == pytest.approx(200.0)
    assert referral.status == "rewarded"
    assert db_session.query(Transaction).filter(Transaction.user_id == partner.id).count() == 1

    referral_service.process_partner_reward(
        referee.id,
        1000.0,
        db_session,
        correlation_id="corr-credit-2",
    )
    db_session.refresh(partner)
    db_session.refresh(referral)

    assert float(partner.balance) == pytest.approx(200.0)
    assert referral.status == "rewarded"
    transactions = db_session.query(Transaction).filter(Transaction.user_id == partner.id).all()
    assert len(transactions) == 1
    assert transactions[0].type == "referral_bonus"

    assert [event for _, event, _ in events] == [
        "referral.partner_reward",
        "referral.partner_reward_skipped",
    ]
    assert events[1][2]["reason"] == "already_rewarded"
    assert events[1][2]["result"] == "skip"
    assert events[1][2]["referrer_id"] == str(partner.id)


def test_partner_reward_emits_credit_and_notification_telemetry(db_session, monkeypatch):
    partner, referee, _ = create_partner_referral(db_session, status="active")
    events = []

    def fake_log(level, event, **fields):
        events.append((level, event, fields))

    def fake_notify_partner_reward(**kwargs):
        referral_service._referral_log(
            "info",
            "referral.partner_reward_notification",
            fn="notify_partner_reward",
            block="DISPATCH_NOTIFICATION",
            correlation_id=kwargs["correlation_id"],
            result="ok",
            telegram_id=kwargs["telegram_id"],
            commission=kwargs["commission"],
        )

    monkeypatch.setattr(referral_service, "log_grace_event", fake_log)
    monkeypatch.setattr(referral_service, "notify_partner_reward", fake_notify_partner_reward)

    referral_service.process_partner_reward(
        referee.id,
        1500.0,
        db_session,
        correlation_id="corr-telemetry",
    )

    db_session.refresh(partner)
    assert float(partner.balance) == pytest.approx(300.0)

    assert [event for _, event, _ in events] == [
        "referral.partner_reward",
        "referral.partner_reward_notification",
    ]

    credit_fields = events[0][2]
    assert credit_fields["module"] == referral_service.MODULE_ID
    assert credit_fields["fn"] == "process_partner_reward"
    assert credit_fields["block"] == "CREDIT_BALANCE"
    assert credit_fields["correlation_id"] == "corr-telemetry"
    assert credit_fields["partner_id"] == str(partner.id)
    assert credit_fields["referee_id"] == str(referee.id)
    assert credit_fields["commission"] == pytest.approx(300.0)

    notification_fields = events[1][2]
    assert notification_fields["module"] == referral_service.MODULE_ID
    assert notification_fields["fn"] == "notify_partner_reward"
    assert notification_fields["block"] == "DISPATCH_NOTIFICATION"
    assert notification_fields["correlation_id"] == "corr-telemetry"
    assert notification_fields["telegram_id"] == partner.telegram_id
    assert notification_fields["commission"] == pytest.approx(300.0)
