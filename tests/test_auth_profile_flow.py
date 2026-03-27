import json
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["ENVIRONMENT"] = "test"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token_for_auth_profile_flow"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import pytest

from backend.app.main import app, get_db
from backend.app.models import Base, User, AnalyticsEvent
from backend.app.auth import authenticate_telegram_user
from backend.app.logging_utils import correlation_scope, get_correlation_ids
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



def _auth_header(telegram_id: int, *, first_name: str = "Flow", last_name: str = "User") -> str:
    payload = {
        "id": telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": f"user{telegram_id}",
    }
    return sign_init_data(payload, os.environ["TELEGRAM_BOT_TOKEN"])



def test_auth_gateway_handler_creates_user_and_wait_flow_reads_profile(client, db_session):
    auth_header = _auth_header(301001)

    created_user = authenticate_telegram_user(auth_header, db_session)

    assert created_user.telegram_id == 301001
    assert created_user.referral_code
    assert created_user.subscription_active_until is not None
    assert created_user.full_name == "Flow User"

    response = client.get("/api/users/me", headers={"X-Telegram-Auth": auth_header})

    assert response.status_code == 200
    body = response.json()
    assert body["telegram_id"] == 301001
    assert body["full_name"] == "Flow User"
    assert body["birth_date"] is None
    assert body["birth_place"] is None
    assert body["days_left"] >= 13

    user = db_session.query(User).filter(User.telegram_id == 301001).one()
    assert user.id == created_user.id



def test_profile_completion_emits_single_profile_fill_after_wait_state(client, db_session):
    auth_header = _auth_header(301002, first_name="Profile", last_name="Pending")

    initial_response = client.get("/api/users/me", headers={"X-Telegram-Auth": auth_header})
    assert initial_response.status_code == 200
    initial_body = initial_response.json()
    assert initial_body["birth_date"] is None
    assert initial_body["birth_place"] is None

    complete_payload = {
        "full_name": "Profile Completed",
        "birth_date": "1990-04-11",
        "birth_time": "06:45",
        "birth_time_known": True,
        "birth_place": "Moscow",
        "birth_timezone": "Europe/Moscow",
        "current_location": "Moscow",
        "current_timezone": "Europe/Moscow",
    }
    update_response = client.put(
        "/api/users/me",
        headers={"X-Telegram-Auth": auth_header},
        json=complete_payload,
    )

    assert update_response.status_code == 200
    updated_body = update_response.json()
    assert updated_body["full_name"] == "Profile Completed"
    assert updated_body["birth_date"] == "1990-04-11"
    assert updated_body["birth_place"] == "Moscow"
    assert updated_body["birth_time_known"] is True

    user = db_session.query(User).filter(User.telegram_id == 301002).one()
    assert user.full_name == "Profile Completed"
    assert user.birth_date == "1990-04-11"
    assert user.birth_place == "Moscow"
    assert user.birth_time == "06:45"
    assert user.birth_timezone == "Europe/Moscow"
    assert user.current_location == "Moscow"
    assert user.current_timezone == "Europe/Moscow"
    assert user.sun_sign == "Aries"

    events = (
        db_session.query(AnalyticsEvent)
        .filter(AnalyticsEvent.telegram_id == 301002)
        .filter(AnalyticsEvent.event_name == "profile_fill")
        .all()
    )
    assert len(events) == 1
    assert events[0].source == "webapp"
    metadata = json.loads(events[0].event_metadata or "{}")
    assert metadata["endpoint"] == "/api/users/me"

    second_update = client.put(
        "/api/users/me",
        headers={"X-Telegram-Auth": auth_header},
        json={"current_location": "Saint Petersburg"},
    )
    assert second_update.status_code == 200

    events_after_second_update = (
        db_session.query(AnalyticsEvent)
        .filter(AnalyticsEvent.telegram_id == 301002)
        .filter(AnalyticsEvent.event_name == "profile_fill")
        .all()
    )
    assert len(events_after_second_update) == 1



def test_correlation_context_survives_auth_and_profile_steps(db_session):
    auth_header = _auth_header(301003, first_name="Correlation", last_name="Trace")

    with correlation_scope("auth_profile_flow", correlation_id="corr-auth-profile", trace_id="trace-auth-profile") as context:
        user = authenticate_telegram_user(auth_header, db_session)
        current = get_correlation_ids()

        assert user.telegram_id == 301003
        assert context["correlation_id"] == "corr-auth-profile"
        assert context["trace_id"] == "trace-auth-profile"
        assert context["correlation_source"] == "auth_profile_flow"
        assert current == context

    restored = get_correlation_ids()
    assert restored["correlation_id"] is None
    assert restored["trace_id"] is None
    assert restored["correlation_source"] is None
