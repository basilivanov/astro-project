# ############################################################################
# AI_HEADER: TEST_B2C_FLOW
# ROLE: Integration tests for B2C features (Onboarding, Feed, Billing).
# DEPENDENCIES: pytest, fastapi.testclient, sqlalchemy
# GRACE_ANCHORS: [TEST_SETUP, TEST_ONBOARDING, TEST_FEED, TEST_BILLING_WEBHOOK]
# ############################################################################

import json
import uuid
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app, get_db
from backend.app.db import Base
from backend.app.models import User, Subscription, Transaction

# #START_BLOCK_TEST_SETUP
# Use an in-memory SQLite db for speed, or a separate test Postgres DB.
# For this environment, we will mock the session using the existing engine but wrapped in a transaction rollback.
# However, since we are running inside the container/environment where DB is Postgres, 
# let's rely on the real DB but use unique IDs to avoid collisions.

client = TestClient(app)

@pytest.fixture
def unique_tg_id():
    return int(datetime.utcnow().timestamp() * 1000)

@pytest.fixture
def auth_headers(unique_tg_id):
    return {"X-Telegram-ID": str(unique_tg_id)}

# #END_BLOCK_TEST_SETUP


# #START_BLOCK_TEST_ONBOARDING
def test_user_onboarding_and_profile(auth_headers, unique_tg_id):
    """
    # PURPOSE: Verify user creation and profile update via API.
    # STEPS: 1. Get Profile (should auto-create). 2. Update Profile. 3. Verify.
    """
    
    # 1. First login (Auto-create)
    res = client.get("/api/users/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["telegram_id"] == unique_tg_id
    assert data["balance"] == 0
    
    # 2. Onboarding (Update Profile)
    payload = {
        "full_name": "Test User",
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "birth_place": "Moscow",
        "birth_lat": 55.75,
        "birth_lon": 37.61
    }
    
    res = client.put("/api/users/me", headers=auth_headers, json=payload)
    assert res.status_code == 200
    updated_data = res.json()
    
    assert updated_data["full_name"] == "Test User"
    assert updated_data["birth_place"] == "Moscow"
    assert updated_data["birth_date"] == "1990-01-01"
# #END_BLOCK_TEST_ONBOARDING


# #START_BLOCK_TEST_FEED
def test_daily_feed(auth_headers):
    """
    # PURPOSE: Verify the feed endpoint returns calculated data.
    """
    # Ensure user exists (optional for public feed but good practice)
    client.get("/api/users/me", headers=auth_headers)

    res = client.get("/api/feed/today", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    
    # Validation
    assert "moon_sign" in data
    assert "moon_phase" in data
    assert "traffic_lights" in data
    assert "general_vibe" in data
    assert len(data["general_vibe"]) > 10 # Should have text
    
    print(f"Captured Vibe: {data['general_vibe']}")
# #END_BLOCK_TEST_FEED


# #START_BLOCK_TEST_BILLING_WEBHOOK
def test_billing_webhook_subscription(unique_tg_id):
    """
    # PURPOSE: Verify that a successful payment webhook extends subscription.
    """
    # 1. Create User directly in DB to get UUID (API doesn't return UUID usually, only TG ID)
    # We need UUID for the webhook metadata.
    # Let's use the API to create, then query DB via app dependency logic (or just trust the logic).
    # Since we can't easily access the DB session here without mocking, 
    # we will rely on the API flow or create a specialized setup.
    
    # Workaround: We will use a real DB session here for test setup.
    from backend.app.db import SessionLocal
    db = SessionLocal()
    try:
        user = User(telegram_id=unique_tg_id, full_name="Billing Tester")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_uuid = str(user.id)
    finally:
        db.close()

    # 2. Simulate Webhook
    webhook_payload = {
        "type": "notification",
        "event": "payment.succeeded",
        "object": {
            "id": "pay_test_123",
            "status": "succeeded",
            "amount": {
                "value": "990.00",
                "currency": "RUB"
            },
            "description": "Subscription",
            "payment_method": {
                "type": "bank_card",
                "id": "card_123",
                "saved": False
            },
            "metadata": {
                "user_id": user_uuid,
                "is_recurring": "True"
            }
        }
    }

    res = client.post("/api/billing/webhook", json=webhook_payload)
    assert res.status_code == 200

    # 3. Verify Result via API
    headers = {"X-Telegram-ID": str(unique_tg_id)}
    res = client.get("/api/users/me", headers=headers)
    data = res.json()
    
    assert data["subscription_active_until"] is not None
    assert data["days_left"] >= 29 # Should be ~30 days
# #END_BLOCK_TEST_BILLING_WEBHOOK
