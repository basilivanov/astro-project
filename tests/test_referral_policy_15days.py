# ############################################################################
# AI_HEADER: TEST_REFERRAL_POLICY_15DAYS
# ROLE: Regression coverage for referral policy edge cases and telemetry.
# DEPENDENCIES: pytest, backend.app.services.referral_service
# ############################################################################

import uuid
from datetime import datetime, timezone

import pytest

from backend.app.db import SessionLocal
from backend.app.models import Referral, User
from backend.app.services import referral_service


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_test_user(db_session, *, is_partner=False) -> User:
    tg_id = int(datetime.now(timezone.utc).timestamp() * 1000) + int(uuid.uuid4().int % 10000)
    user = User(
        telegram_id=tg_id,
        full_name=f"Referral Policy User {tg_id}",
        is_partner=is_partner,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_referral_policy_rejects_self_referral_and_logs_telemetry(db_session, monkeypatch):
    user = create_test_user(db_session)
    events = []
    before_count = db_session.query(Referral).count()

    def fake_log(level, event, **fields):
        events.append((level, event, fields))

    monkeypatch.setattr(referral_service, "log_grace_event", fake_log)

    result = referral_service.process_referral_signup(user.id, user.id, db_session, correlation_id="corr-self")

    assert result is False
    assert db_session.query(Referral).count() == before_count
    assert len(events) == 1

    level, event, fields = events[0]
    assert level == "warning"
    assert event == "referral.signup_rejected"
    assert fields["module"] == referral_service.MODULE_ID
    assert fields["fn"] == "process_referral_signup"
    assert fields["block"] == "VALIDATE_ACTORS"
    assert fields["result"] == "fail"
    assert fields["reason"] == "invalid_users"
    assert fields["correlation_id"] == "corr-self"
    assert fields["referrer_id"] == str(user.id)
    assert fields["referee_id"] == str(user.id)



def test_referral_policy_rejects_duplicate_links_and_preserves_single_edge(db_session, monkeypatch):
    referrer = create_test_user(db_session)
    referee = create_test_user(db_session)
    assert referral_service.process_referral(referrer.id, referee.id, db_session) is True

    events = []

    def fake_log(level, event, **fields):
        events.append((level, event, fields))

    monkeypatch.setattr(referral_service, "log_grace_event", fake_log)

    result = referral_service.process_referral_signup(
        referrer.id,
        referee.id,
        db_session,
        correlation_id="corr-dup",
    )

    assert result is False
    referrals = db_session.query(Referral).filter(Referral.referee_id == referee.id).all()
    assert len(referrals) == 1
    assert len(events) == 1

    level, event, fields = events[0]
    assert level == "info"
    assert event == "referral.signup_duplicate"
    assert fields["module"] == referral_service.MODULE_ID
    assert fields["fn"] == "process_referral_signup"
    assert fields["block"] == "ENSURE_UNIQUENESS"
    assert fields["result"] == "skip"
    assert fields["correlation_id"] == "corr-dup"
    assert fields["referee_id"] == str(referee.id)
    assert fields["existing_referrer_id"] == str(referrer.id)



def test_referral_policy_success_emits_signup_and_reward_telemetry(db_session, monkeypatch):
    referrer = create_test_user(db_session, is_partner=False)
    referee = create_test_user(db_session, is_partner=False)
    events = []

    def fake_log(level, event, **fields):
        events.append((level, event, fields))

    monkeypatch.setattr(referral_service, "log_grace_event", fake_log)

    result = referral_service.process_referral_signup(
        referrer.id,
        referee.id,
        db_session,
        correlation_id="corr-success",
    )

    assert result is True

    event_names = [event for _, event, _ in events]
    assert event_names == [
        "referral.signup_edge_created",
        "referral.referee_reward_applied",
        "referral.referrer_reward_granted",
        "referral.signup_processed",
    ]

    for level, event, fields in events:
        assert level == "info"
        assert fields["module"] == referral_service.MODULE_ID
        assert fields["correlation_id"] == "corr-success"
        assert fields["fn"] in {"process_referral_signup", "grant_referral_reward"}

    assert events[0][2]["block"] == "CREATE_REFERRAL_EDGE"
    assert events[1][2]["block"] == "APPLY_REFEREE_REWARD"
    assert events[2][2]["block"] == "APPLY_REFERRER_REWARD"
    assert events[3][2]["block"] == "COMMIT"

    referral = db_session.query(Referral).filter(Referral.referee_id == referee.id).one()
    assert referral.referrer_id == referrer.id
    assert referral.status == "rewarded"
    assert referral.reward_type == "days"
