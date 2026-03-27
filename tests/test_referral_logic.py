# ############################################################################
# AI_HEADER: TEST_REFERRAL_LOGIC
# ROLE: Unit/Integration tests for Referral Service.
# DEPENDENCIES: pytest, backend.app.services.referral_service
# ############################################################################

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.app.models import User, Referral
from backend.app.services.referral_service import process_referral
from backend.app.db import SessionLocal

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def create_test_user(db: Session, is_partner=False) -> User:
    # Use timezone-aware UTC for consistency
    tg_id = int(datetime.now(timezone.utc).timestamp() * 1000) + int(uuid.uuid4().int % 10000)
    user = User(
        telegram_id=tg_id, 
        full_name=f"User {tg_id}",
        is_partner=is_partner
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_referral_regular_user(db_session):
    """
    # SCENARIO: Regular user invites New user.
    # EXPECT: Both get +14 days.
    """
    referrer = create_test_user(db_session, is_partner=False)
    new_user = create_test_user(db_session, is_partner=False)
    
    # Capture time before processing
    before = datetime.now(timezone.utc)
    
    success = process_referral(referrer.id, new_user.id, db_session)
    assert success is True
    
    # Reload
    db_session.refresh(referrer)
    db_session.refresh(new_user)
    
    # Validate New User (+14 days from moment of processing)
    # Since process_referral takes 'now' inside, it should be slightly after 'before'
    assert new_user.subscription_active_until is not None
    expected_duration = timedelta(days=14)
    actual_duration = new_user.subscription_active_until - before
    # Allow small drift (e.g., 5 seconds execution time)
    assert abs(actual_duration - expected_duration) < timedelta(seconds=10)
    
    # Validate Referrer (+14 days)
    assert referrer.subscription_active_until is not None
    actual_duration_ref = referrer.subscription_active_until - before
    assert abs(actual_duration_ref - expected_duration) < timedelta(seconds=10)
    
    # Referral Record Check
    ref_record = db_session.query(Referral).filter(Referral.referee_id == new_user.id).first()
    assert ref_record is not None
    assert ref_record.referrer_id == referrer.id
    assert ref_record.status == "rewarded"

def test_referral_partner(db_session):
    """
    # SCENARIO: Partner invites New user.
    # EXPECT: New user +14 days, Partner stays pending monetary reward.
    """
    referrer = create_test_user(db_session, is_partner=True)
    new_user = create_test_user(db_session, is_partner=False)
    
    before = datetime.now(timezone.utc)
    
    success = process_referral(referrer.id, new_user.id, db_session)
    assert success is True
    
    db_session.refresh(referrer)
    db_session.refresh(new_user)
    
    # New User gets days
    assert new_user.subscription_active_until is not None
    actual_duration = new_user.subscription_active_until - before
    assert abs(actual_duration - timedelta(days=14)) < timedelta(seconds=10)
    
    # Partner gets NO days (remains None or 0)
    assert referrer.subscription_active_until is None
    
    # Referral Record marks active money reward awaiting payout credit
    ref_record = db_session.query(Referral).filter(Referral.referee_id == new_user.id).first()
    assert ref_record.status == "active"

def test_referral_stacking(db_session):
    """
    # SCENARIO: Referrer already has active sub.
    # EXPECT: Adds 14 days to existing date.
    """
    referrer = create_test_user(db_session)
    
    # Give initial sub
    now = datetime.now(timezone.utc)
    initial_end = now + timedelta(days=10)
    referrer.subscription_active_until = initial_end
    db_session.commit()
    
    new_user = create_test_user(db_session)
    
    process_referral(referrer.id, new_user.id, db_session)
    db_session.refresh(referrer)
    
    # Should be initial_end + 14 days
    expected_end = initial_end + timedelta(days=14)
    
    # Check
    assert referrer.subscription_active_until is not None
    # Allow tiny drift due to precision loss in DB or processing time
    diff = abs(referrer.subscription_active_until - expected_end)
    assert diff < timedelta(seconds=10)

def test_duplicate_referral(db_session):
    """
    # SCENARIO: Try to refer same user twice.
    # EXPECT: Second time returns False, no double reward.
    """
    referrer = create_test_user(db_session)
    new_user = create_test_user(db_session)
    
    assert process_referral(referrer.id, new_user.id, db_session) is True
    assert process_referral(referrer.id, new_user.id, db_session) is False # Fail
