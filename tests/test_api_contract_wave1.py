from __future__ import annotations

import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token_for_api_contract_wave1")

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app, get_db
from backend.app.models import Base
from tests.canonical_persona_pack import get_fixture
from tests.utils import sign_init_data


def test_api_gateway_schema_and_helper_compat_exports_preserve_dto_behavior():
    from backend.app import api_helpers, api_schemas
    from backend.app import main

    assert main.ReportWorkflowRequest is api_schemas.ReportWorkflowRequest
    assert main.B2CReportCreateRequest is api_schemas.B2CReportCreateRequest
    assert main.format_datetime is api_helpers.format_datetime
    assert main.get_moon_phase_emoji is api_helpers.get_moon_phase_emoji

    payload = main.ReportWorkflowRequest(
        client_name="Schema Probe",
        birth_date="1990-01-02T03:04:00+00:00",
        birth_location="Moscow, Russia",
        report_type="natal_master",
        sections=[main.SectionInput(section_id="intro", title="Intro", prompt="Write intro")],
    )

    assert payload.model_dump() == api_schemas.ReportWorkflowRequest.model_validate(payload.model_dump()).model_dump()
    assert main.get_moon_phase_emoji(180) == "🌕"


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


def _auth_header(telegram_id: int, *, first_name: str = "Contract", last_name: str = "User") -> str:
    payload = {
        "id": telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": f"user{telegram_id}",
    }
    return sign_init_data(payload, os.environ["TELEGRAM_BOT_TOKEN"])


def _complete_profile_from_fixture(client: TestClient, auth_header: str, fixture_id: str) -> dict:
    fixture = get_fixture(fixture_id)
    canonical_inputs = fixture["canonical_inputs"]
    birth_dt = datetime.fromisoformat(canonical_inputs["birth_date_local"])
    payload = {
        "full_name": canonical_inputs["client_name"],
        "birth_date": birth_dt.date().isoformat(),
        "birth_time": birth_dt.strftime("%H:%M"),
        "birth_time_known": canonical_inputs["birth_time_known"],
        "birth_place": canonical_inputs["birth_location"],
        "birth_timezone": canonical_inputs["birth_timezone"],
        "current_location": canonical_inputs["birth_location"],
        "current_timezone": canonical_inputs["birth_timezone"],
    }
    response = client.put("/api/users/me", headers={"X-Telegram-Auth": auth_header}, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_profile_contract_preserves_selected_canonical_fields_for_exact_time_persona(client):
    fixture = get_fixture("CF-BE-001-baseline-exact-time")
    auth_header = _auth_header(401001, first_name="Ava", last_name="Meridian")

    updated = _complete_profile_from_fixture(client, auth_header, fixture["id"])
    profile = client.get("/api/users/me", headers={"X-Telegram-Auth": auth_header})

    assert profile.status_code == 200
    body = profile.json()
    canonical_inputs = fixture["canonical_inputs"]

    assert updated["full_name"] == canonical_inputs["client_name"]
    assert body["full_name"] == canonical_inputs["client_name"]
    assert body["birth_place"] == canonical_inputs["birth_location"]
    assert body["birth_timezone"] == canonical_inputs["birth_timezone"]
    assert body["birth_time_known"] is True
    assert body["birth_date"] == datetime.fromisoformat(canonical_inputs["birth_date_local"]).date().isoformat()
    assert "birth_time" not in updated
    assert "birth_time" not in body


def test_profile_contract_unknown_birth_time_update_currently_surfaces_server_error_boundary(client):
    fixture = get_fixture("CF-BTU-003-birth-time-unknown")
    auth_header = _auth_header(401002, first_name="Noon", last_name="Vale")
    canonical_inputs = fixture["canonical_inputs"]
    birth_dt = datetime.fromisoformat(canonical_inputs["birth_date_local"])

    initial_profile = client.get("/api/users/me", headers={"X-Telegram-Auth": auth_header})
    assert initial_profile.status_code == 200
    assert initial_profile.json()["birth_time_known"] is True

    response = client.put(
        "/api/users/me",
        headers={"X-Telegram-Auth": auth_header},
        json={
            "full_name": canonical_inputs["client_name"],
            "birth_date": birth_dt.date().isoformat(),
            "birth_time": birth_dt.strftime("%H:%M"),
            "birth_time_known": False,
            "birth_place": canonical_inputs["birth_location"],
            "birth_timezone": canonical_inputs["birth_timezone"],
        },
    )

    assert response.status_code == 500


def test_day_brief_contract_preserves_explainability_and_non_fallback_semantics_for_exact_time_persona(client, monkeypatch):
    fixture = get_fixture("CF-BE-001-baseline-exact-time")
    auth_header = _auth_header(401003, first_name="Ava", last_name="Meridian")
    _complete_profile_from_fixture(client, auth_header, fixture["id"])

    fixed_now = datetime(2026, 4, 1, 6, 0, tzinfo=timezone.utc)

    def fake_build_personalized_daily_facts(now, user=None, **_kwargs):
        return {
            "local_dt": "2026-04-01T09:00:00+03:00",
            "moon_phase": "Растущая Луна",
            "moon_sign": "Овен",
            "moon_emoji": "🌔",
            "aspects_count": 4,
            "aspect_summary": "Венера поддерживает точные договоренности без лишней спешки.",
            "traffic_lights": {"health": "yellow", "money": "green", "love": "yellow"},
            "week_data": {"days": [{"moon": {"sign": "Овен", "phase": "Растущая", "void_of_course": False}}]},
            "semantic_layer": {
                "headline": "День про ясный темп и короткие точные решения.",
                "pacing": "Лучше идти короткими циклами.",
                "rest": "Не выжигать ресурс в начале дня.",
                "money_admin_focus": "Закрыть один конкретный вопрос по работе.",
                "relationship_softness": "Говорить прямо и спокойно.",
                "practical_move": "Сделать один заметный шаг и закрепить результат.",
                "focus_key": "money_admin",
            },
            "personalization_level": "personalized_v2",
            "meta": {"fallback_mode": False},
            "month_data": {"status": "GREEN"},
            "year_data": {"profection": {"house": 10}, "months": [{"month": 4, "status": "GREEN"}]},
            "fast_hits": [
                {
                    "transit": "Venus",
                    "natal": "Venus",
                    "type": "Секстиль (60°)",
                    "orb": 0.4,
                    "summary": "Венера секстиль Венера",
                }
            ],
        }

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is not None else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr("backend.app.main.build_personalized_daily_facts", fake_build_personalized_daily_facts)
    monkeypatch.setattr("backend.app.main.datetime", FrozenDateTime)

    response = client.get("/api/feed/today", headers={"X-Telegram-Auth": auth_header})

    assert response.status_code == 200, response.text
    payload = response.json()
    day_brief = payload["day_brief"]

    assert payload["personalization_level"] == "personalized_v2"
    assert payload["birth_time_used"] is False
    assert payload["generation_mode"] in {"deterministic", "fallback"}
    assert isinstance(payload["factor_count"], int) and payload["factor_count"] >= 1
    assert day_brief.get("fallback_mode", False) is False
    assert day_brief["personalization_level"] == "personalized_v2"
    assert day_brief["status"] in {"complete", "partial"}
    assert day_brief["hero"]["title"]
    assert set(day_brief["domains"].keys()) == {"energy", "money", "love", "focus"}


def test_day_brief_contract_exposes_fallback_semantics_without_hiding_explainability(client, monkeypatch):
    auth_header = _auth_header(401004, first_name="Fallback", last_name="Probe")

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 4, 1, 6, 0, tzinfo=timezone.utc) if tz is not None else datetime(2026, 4, 1, 6, 0)

    def boom(*args, **kwargs):
        raise RuntimeError("synthetic feed failure")

    monkeypatch.setattr("backend.app.main.build_personalized_daily_facts", boom)
    monkeypatch.setattr("backend.app.main.datetime", FrozenDateTime)

    response = client.get("/api/feed/today", headers={"X-Telegram-Auth": auth_header, "X-Feed-Debug": "1"})

    assert response.status_code == 200, response.text
    payload = response.json()
    day_brief = payload["day_brief"]

    assert payload["personalization_level"] == "anonymous"
    assert payload["meta"] == {"reason": "endpoint_error"}
    assert payload["generation_mode"] == "fallback"
    assert payload["birth_time_used"] is None
    assert day_brief is None


def test_report_week_brief_contract_preserves_explainability_and_report_reference():
    import uuid
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    from backend.app.main import get_report_detail

    user = SimpleNamespace(id=uuid.uuid4())
    report = SimpleNamespace(
        id=uuid.uuid4(),
        report_type="week_forecast",
        status="completed",
        created_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        client=SimpleNamespace(full_name="Mira North"),
        access_source="subscription",
        chunks=[SimpleNamespace(section="week_strategy", content="[]", status="completed", order_index=0)],
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = report
    week_brief = {
        "version": "week_brief_v1",
        "week_start": "2026-03-30",
        "week_end": "2026-04-05",
        "personalization_level": "personalized_v2",
        "fallback_mode": False,
        "status": "ready",
        "summary": {
            "headline": "Неделя просит точного темпа и фиксации решений.",
            "subhead": "Сильные дни подходят для договоренностей.",
            "week_type": "balance",
            "theme": "Работа, темп и границы",
        },
        "day_cards": [],
        "domains": [],
        "best_uses": [{"id": "focus", "text": "Держать один главный вектор."}],
        "risks": [{"id": "rush", "text": "Не дробить неделю на лишние фронты."}],
        "major_factors": [],
        "deep_sections": [],
        "explainability": {
            "confidence": 0.82,
            "birth_time_used": True,
            "factor_count": 5,
            "selected_factors": [{"id": "moon", "label": "Moon pacing"}],
        },
        "report_ref": {
            "report_id": str(report.id),
            "report_type": "week_forecast",
            "source_status": "completed",
        },
    }

    with (
        patch("backend.app.main.load_report_payload", return_value=SimpleNamespace(llm_mode="cheap", birth_time_known=True)),
        patch("backend.app.main.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.main.build_natal_chart_svg", return_value="<svg />"),
        patch("backend.app.main.build_report_context", return_value={"week_brief_seed": {}}),
        patch("backend.app.main.build_week_brief_payload", return_value=week_brief),
        patch("backend.app.main.build_week_brief_envelope", return_value={"status": "ready", "data": week_brief, "message": None, "retry_after_seconds": None}),
    ):
        response = get_report_detail(str(report.id), user=user, db=db)

    assert response["week_brief"]["fallback_mode"] is False
    assert response["week_brief"]["summary"]["headline"]
    assert response["week_brief"]["explainability"]["birth_time_used"] is True
    assert response["week_brief"]["explainability"]["factor_count"] == 5
    assert response["week_brief"]["report_ref"]["report_id"] == str(report.id)
    assert response["week_brief_envelope"]["status"] == "ready"
