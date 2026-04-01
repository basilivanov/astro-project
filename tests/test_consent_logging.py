import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["ENVIRONMENT"] = "test"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token_for_consent_logging"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from backend.app.main import app, get_db
from backend.app.models import Base, AnalyticsEvent, SupportTicket, User
from tests.utils import sign_init_data


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
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _auth_header(telegram_id: int) -> str:
    payload = {
        "id": telegram_id,
        "first_name": "Consent",
        "last_name": "User",
        "username": f"consent{telegram_id}",
    }
    return sign_init_data(payload, os.environ["TELEGRAM_BOT_TOKEN"])


def test_profile_update_persists_consent_versions(client, db_session):
    auth_header = _auth_header(401001)

    response = client.put(
        "/api/users/me",
        headers={"X-Telegram-Auth": auth_header},
        json={
            "full_name": "Consent User",
            "birth_date": "1991-05-21",
            "birth_time": "10:15",
            "birth_time_known": True,
            "birth_place": "Moscow",
            "birth_timezone": "Europe/Moscow",
            "consent_accepted": True,
            "consent_flow": "onboarding_profile",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["consent_log"]["current"]["flow"] == "onboarding_profile"
    assert body["consent_log"]["current"]["accepted"] is True
    assert body["consent_log"]["current"]["versions"]["terms"] == "offer_terms_ru_2026-04-01"

    user = db_session.query(User).filter(User.telegram_id == 401001).one()
    assert user.consent_log["current"]["flow"] == "onboarding_profile"
    assert user.consent_log["history"][0]["versions"]["privacy"] == "privacy_policy_ru_2026-04-01"

    events = (
        db_session.query(AnalyticsEvent)
        .filter(AnalyticsEvent.telegram_id == 401001)
        .filter(AnalyticsEvent.event_name == "legal_consent_accept")
        .all()
    )
    assert len(events) == 1


def test_support_ticket_requires_and_stores_consent_snapshot(client, db_session):
    auth_header = _auth_header(401002)

    profile_response = client.put(
        "/api/users/me",
        headers={"X-Telegram-Auth": auth_header},
        json={
            "full_name": "Support User",
            "birth_date": "1990-04-11",
            "birth_time": "06:45",
            "birth_time_known": True,
            "birth_place": "Moscow",
            "birth_timezone": "Europe/Moscow",
        },
    )
    assert profile_response.status_code == 200

    denied = client.post(
        "/api/support/tickets",
        headers={"X-Telegram-Auth": auth_header},
        json={"topic": "billing", "message": "help", "consent_accepted": False},
    )
    assert denied.status_code == 400
    assert denied.json()["detail"] == "consent_required"

    created = client.post(
        "/api/support/tickets",
        headers={"X-Telegram-Auth": auth_header},
        json={
            "topic": "billing",
            "message": "help",
            "consent_accepted": True,
            "consent_flow": "support_form",
        },
    )
    assert created.status_code == 200, created.text

    ticket = db_session.query(SupportTicket).filter(SupportTicket.topic == "billing").one()
    assert ticket.consent_snapshot["flow"] == "support_form"
    assert ticket.consent_snapshot["surface"] == "support"
    assert ticket.consent_snapshot["versions"]["data_processing"] == "data_processing_consent_ru_2026-04-01"
