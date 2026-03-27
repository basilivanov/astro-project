import os
import sys
import types
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

if "stellium" not in sys.modules:
    stellium = types.ModuleType("stellium")
    engines = types.ModuleType("stellium.engines")
    houses = types.ModuleType("stellium.engines.houses")

    class _StubHouseSystem:
        def __init__(self, *args, **kwargs):
            pass

    houses.EqualHouses = _StubHouseSystem
    houses.PlacidusHouses = _StubHouseSystem
    houses.WholeSignHouses = _StubHouseSystem
    engines.houses = houses
    stellium.engines = engines
    stellium.ChartBuilder = object
    stellium.ReturnBuilder = object
    stellium.ChartLocation = object
    stellium.FIXED_STARS_REGISTRY = {}
    stellium.get_fixed_star_info = lambda *args, **kwargs: None
    sys.modules["stellium"] = stellium
    sys.modules["stellium.engines"] = engines
    sys.modules["stellium.engines.houses"] = houses

if "stellium_engine" not in sys.modules:
    stellium_engine = types.ModuleType("stellium_engine")

    class _StubStelliumEngine:
        pass

    stellium_engine.StelliumEngine = _StubStelliumEngine
    sys.modules["stellium_engine"] = stellium_engine

if "yookassa" not in sys.modules:
    yookassa = types.ModuleType("yookassa")

    class _StubConfiguration:
        account_id = None
        secret_key = None

    class _StubPayment:
        @classmethod
        def create(cls, payload, idempotence_key):
            return {"id": "test", "status": "succeeded", "payload": payload, "key": idempotence_key}

    yookassa.Configuration = _StubConfiguration
    yookassa.Payment = _StubPayment
    sys.modules["yookassa"] = yookassa

if "backend.app.services.week_brief_service" not in sys.modules:
    week_brief_service = types.ModuleType("backend.app.services.week_brief_service")
    week_brief_service.build_week_brief_payload = lambda *args, **kwargs: {}
    sys.modules["backend.app.services.week_brief_service"] = week_brief_service

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.day_brief import (
    build_day_brief_fallback,
    build_day_brief_payload,
    build_day_brief_telemetry,
)


client = TestClient(app)


def _sample_facts() -> dict:
    return {
        "local_dt": "2026-03-27T07:00:00+03:00",
        "moon_phase": "Растущая Луна",
        "moon_sign": "Рыбы",
        "moon_emoji": "🌔",
        "aspects_count": 2,
        "aspect_summary": "Марс квадрат Солнце, Венера секстиль Венера",
        "traffic_lights": {"health": "red", "money": "green", "love": "yellow"},
        "week_data": {
            "days": [
                {
                    "moon": {"sign": "Рыбы", "phase": "Растущая", "void_of_course": True},
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                }
            ]
        },
        "semantic_layer": {
            "headline": "День про короткий фокус, аккуратные решения и взрослый темп.",
            "pacing": "Темп дня лучше держать короткими циклами и без лишнего разгона.",
            "rest": "Телу нужен запас по времени и пауза до следующего захода.",
            "money_admin_focus": "Хорошо закрывать один документ, одно согласование или одно денежное условие.",
            "relationship_softness": "Мягкость и честная формулировка работают сильнее, чем нажим.",
            "practical_move": "Закрой один важный вопрос и сразу зафиксируй детали письменно.",
            "focus_key": "money_admin",
            "tension": "лишняя скорость и спор на формулировках",
        },
        "personalization_level": "personalized_v2",
        "meta": {"fallback_mode": False},
        "month_data": {"status": "GREEN"},
        "year_data": {
            "profection": {"house": 10},
            "months": [{"month": 3, "status": "GREEN"}],
        },
        "fast_hits": [
            {
                "transit": "Mars",
                "natal": "Sun",
                "type": "Квадрат (90°)",
                "orb": 0.2,
                "summary": "Марс квадрат Солнце",
            },
            {
                "transit": "Venus",
                "natal": "Venus",
                "type": "Секстиль (60°)",
                "orb": 0.4,
                "summary": "Венера секстиль Венера",
            },
        ],
    }


def test_build_day_brief_payload_returns_contract_shape() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(
            birth_time="07:05",
            birth_time_known=True,
            subscription_active_until=datetime(2026, 4, 3, tzinfo=timezone.utc),
        ),
        general_vibe="Главный акцент дня: Марс квадрат Солнце. Действуй точечно и не спорь на скорости.",
        generation_mode="llm",
    )

    assert payload["version"] == "day_brief_v1"
    assert payload["fallback_mode"] is False
    assert payload["summary"]["day_type"] in {"push", "balance", "caution", "deep_focus", "recovery"}
    assert payload["summary"]["tone"]
    assert [item["key"] for item in payload["scores"]] == ["energy", "money", "love", "focus"]
    assert {item["status"] for item in payload["scores"]} <= {"green", "yellow", "red"}
    assert payload["windows"]
    assert all(len(window["start"]) == 5 and len(window["end"]) == 5 for window in payload["windows"])
    assert payload["best_uses"]
    assert payload["risks"]
    assert payload["personalized_factors"]
    assert payload["explainability"]["birth_time_used"] is True
    assert payload["explainability"]["timing_precision"] == "exact"
    assert payload["premium"]["subscription_active"] is True
    assert payload["cta"]["primary"]["type"] == "open_week"
    assert payload["legacy"]["general_vibe"].startswith("Главный акцент дня")


def test_build_day_brief_fallback_is_safe_and_approximate() -> None:
    payload = build_day_brief_fallback(
        datetime(2026, 3, 27, 6, 0, tzinfo=timezone.utc),
        general_vibe="Сегодня Луна в знаке Луна. День лучше прожить на коротком фокусе.",
        generation_mode="fallback",
        reason="test",
    )
    telemetry = build_day_brief_telemetry(payload, generation_mode="fallback")

    assert payload["fallback_mode"] is True
    assert payload["explainability"]["timing_precision"] == "approximate"
    assert payload["explainability"]["confidence"] <= 0.65
    assert len(payload["personalized_factors"]) <= 3
    assert telemetry["generation_mode"] == "fallback"
    assert telemetry["birth_time_used"] is False
    assert telemetry["confidence_bucket"] in {"low", "medium"}


@patch("backend.app.main.get_daily_vibe_llm")
@patch("backend.app.main.build_personalized_daily_facts")
def test_feed_today_returns_day_brief_and_top_level_telemetry(mock_facts, mock_vibe) -> None:
    mock_facts.return_value = _sample_facts()
    mock_vibe.return_value = (
        "День просит коротких решений и аккуратной фиксации деталей.",
        {"generation_mode": "llm", "cache_hit": False, "llm_mode": "openrouter", "cache_scope": "scope-1"},
    )

    response = client.get("/api/feed/today")

    assert response.status_code == 200
    data = response.json()
    assert data["general_vibe"] == "День просит коротких решений и аккуратной фиксации деталей."
    assert data["traffic_lights"]["money"] == "green"
    assert data["fast_hits"][0]["summary"] == "Марс квадрат Солнце"
    assert data["day_brief"]["version"] == "day_brief_v1"
    assert data["day_brief"]["legacy"]["general_vibe"] == data["general_vibe"]
    assert data["generation_mode"] == "llm"
    assert data["birth_time_used"] is False
    assert data["confidence_bucket"] in {"low", "medium", "high"}
    assert data["factor_count"] >= 1
    assert "trace_id" in data


@patch("backend.app.main.build_personalized_daily_facts")
def test_feed_today_returns_day_brief_fallback_when_facts_fail(mock_facts) -> None:
    mock_facts.side_effect = RuntimeError("boom")

    response = client.get("/api/feed/today")

    assert response.status_code == 200
    data = response.json()
    assert data["personalization_level"] == "anonymous"
    assert data["generation_mode"] == "fallback"
    assert data["day_brief"]["fallback_mode"] is True
    assert data["day_brief"]["summary"]["headline"]
    assert data["day_brief"]["explainability"]["timing_precision"] == "approximate"

@patch("backend.app.main.get_daily_vibe_llm")
@patch("backend.app.main.build_personalized_daily_facts")
def test_feed_today_preserves_cache_generation_mode(mock_facts, mock_vibe) -> None:
    mock_facts.return_value = _sample_facts()
    mock_vibe.return_value = (
        "Кэшированный прогноз дня.",
        {"generation_mode": "cache", "cache_hit": True, "llm_mode": "openrouter", "cache_scope": "scope-1"},
    )

    response = client.get("/api/feed/today")

    assert response.status_code == 200
    data = response.json()
    assert data["general_vibe"] == "Кэшированный прогноз дня."
    assert data["generation_mode"] == "cache"
    assert data["day_brief"]["fallback_mode"] is False
    assert data["day_brief"]["legacy"]["general_vibe"] == "Кэшированный прогноз дня."

