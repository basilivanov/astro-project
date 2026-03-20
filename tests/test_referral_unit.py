# ############################################################################
# AI_HEADER: TEST_REFERRAL_UNIT
# ROLE: Unit test for referral service logic (using real DB session).
# DEPENDENCIES: pytest, backend.app.services.referral_service
# ############################################################################

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db import Base
from backend.app.models import User, Referral
from backend.app.services.referral_service import process_referral, resolve_referrer

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_resolve_referrer_exact(db_session):
    user = User(telegram_id=100, full_name="Ref", referral_code="u_123456")
    db_session.add(user)
    db_session.commit()
    
    res = resolve_referrer("u_123456", db_session)
    assert res.id == user.id

def test_resolve_referrer_prefix(db_session):
    user = User(telegram_id=101, full_name="Ref2", referral_code="u_ABCDEF")
    db_session.add(user)
    db_session.commit()
    
    res = resolve_referrer("ref_u_ABCDEF", db_session)
    assert res.id == user.id

def test_process_referral_success(db_session):
    referrer = User(
        telegram_id=200, 
        referral_code="u_REF1",
        subscription_active_until=datetime.now(timezone.utc) + timedelta(days=5),
        is_partner=False
    )
    new_user = User(telegram_id=201, referral_code="u_NEW1")
    
    db_session.add(referrer)
    db_session.add(new_user)
    db_session.commit()
    
    success = process_referral(referrer.id, new_user.id, db_session)
    assert success is True
    
    db_session.refresh(referrer)
    db_session.refresh(new_user)
    
    # Check New User (+14)
    assert new_user.subscription_active_until is not None
    # Check Referrer (+14)
    # Original +5 + 14 = +19
    ref_sub = referrer.subscription_active_until
    if ref_sub.tzinfo is None:
        ref_sub = ref_sub.replace(tzinfo=timezone.utc)
    delta = ref_sub - datetime.now(timezone.utc)
    assert delta.days >= 18
