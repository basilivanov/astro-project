# ############################################################################
# AI_HEADER: TEST_AUTH_INTEGRATION
# ROLE: Verify authentication and referral logic flow using REAL signatures.
# GRACE_ANCHORS: [AUTH_TEST_REAL_SIG]
# ############################################################################

import os
import json
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup Environment BEFORE imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Important: This token MUST match the one used to sign data in tests
TEST_BOT_TOKEN = "test_token_for_integration"
os.environ["TELEGRAM_BOT_TOKEN"] = TEST_BOT_TOKEN
os.environ["ENVIRONMENT"] = "test"

from backend.app.main import app, get_db
from backend.app.models import Base, User, Referral
# Import the signing helper
from tests.utils import sign_init_data

# DB Fixture
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

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

# #START_BLOCK_AUTH_TEST_REAL_SIG
def test_auth_new_user_trial_real_sig(client, db_session):
    """
    # SCENARIO: New user logs in via initData with a VALID REAL SIGNATURE.
    # EXPECT: User created, 14 days trial granted.
    """
    
    user_data = {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser"
    }
    
    # Generate REAL valid initData string using the test token
    valid_auth_string = sign_init_data(user_data, TEST_BOT_TOKEN)
    
    # Send request with valid signature
    response = client.get("/api/users/me", headers={"X-Telegram-Auth": valid_auth_string})
        
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_id"] == 123456789
    assert data["days_left"] >= 13 # 14 days trial
    
    # Verify DB
    user = db_session.query(User).filter(User.telegram_id == 123456789).first()
    assert user is not None
    assert user.referral_code is not None
    assert user.subscription_active_until is not None

def test_auth_referral_flow_real_sig(client, db_session):
    """
    # SCENARIO: New user joins via referral link with REAL SIGNATURE.
    # EXPECT: Referrer and Referee get +14 days.
    """
    
    # 1. Create Referrer
    referrer = User(
        telegram_id=999,
        full_name="Referrer",
        referral_code="u_ABC123",
        subscription_active_until=None # Expired/None
    )
    db_session.add(referrer)
    db_session.commit()
    
    # 2. New User joins with start_param
    new_user_data = {
        "id": 888,
        "first_name": "New",
        "username": "newbie"
    }
    
    # Generate REAL valid initData string with start_param
    valid_auth_string = sign_init_data(
        new_user_data, 
        TEST_BOT_TOKEN,
        start_param="ref_u_ABC123"
    )
    
    response = client.get("/api/users/me", headers={"X-Telegram-Auth": valid_auth_string})
        
    assert response.status_code == 200
    
    # 3. Verify Bonus
    db_session.refresh(referrer)
    new_user = db_session.query(User).filter(User.telegram_id == 888).first()
    referral = db_session.query(Referral).first()
    
    assert referral is not None
    assert referral.referrer_id == referrer.id
    assert referral.referee_id == new_user.id
    assert referral.status == "rewarded"
    
    # Referrer got days (from None/Now -> +14)
    assert referrer.subscription_active_until is not None
    
    # New user got trial
    assert new_user.subscription_active_until is not None

def test_auth_invalid_hash_real_check(client):
    """
    # SCENARIO: Invalid initData signature (signed with WRONG token).
    # EXPECT: 401 Unauthorized.
    """
    user_data = {"id": 666, "first_name": "Evil"}
    
    # Sign with a DIFFERENT token -> valid format, invalid signature for the backend
    invalid_auth_string = sign_init_data(user_data, "WRONG_TOKEN")
    
    response = client.get("/api/users/me", headers={"X-Telegram-Auth": invalid_auth_string})
        
    assert response.status_code == 401

# #END_BLOCK_AUTH_TEST_REAL_SIG
