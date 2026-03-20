# ############################################################################
# AI_HEADER: TEST_ENTITLEMENTS
# ROLE: Verify access control based on subscription status.
# ############################################################################

import os
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["ENVIRONMENT"] = "test"

from backend.app.main import app, get_db
from backend.app.models import Base, User
from backend.app.auth import get_current_user

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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

def test_report_generation_with_expired_subscription(client, db_session):
    """
    # SCENARIO: User with expired subscription tries to generate a report.
    # EXPECT: 403 Forbidden (or 402 Payment Required).
    """
    
    # 1. Create User with expired sub
    expired_date = datetime.now(timezone.utc) - timedelta(days=1)
    user = User(
        telegram_id=100,
        full_name="Expired User",
        subscription_active_until=expired_date
    )
    db_session.add(user)
    db_session.commit()
    
    # 2. Override auth to return this user
    app.dependency_overrides[get_current_user] = lambda: user
    
    payload = {
        "client_name": "Test",
        "birth_date": "1990-01-01",
        "birth_location": "London",
        "report_type": "month_forecast" # Premium report
    }
    
    response = client.post("/api/workflows/report", json=payload)
    
    # Clean up override
    del app.dependency_overrides[get_current_user]
    
    # ASSERT
    assert response.status_code in [402, 403], f"Expected 402/403, got {response.status_code}"
