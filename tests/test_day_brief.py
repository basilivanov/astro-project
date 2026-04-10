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
    week_brief_service.build_week_brief_envelope = lambda *args, **kwargs: {}
    sys.modules["backend.app.services.week_brief_service"] = week_brief_service

from fastapi import HTTPException

from backend.app.services.day_brief import build_day_brief_payload, build_day_brief_telemetry
from backend.app.services.day_brief_validators import validate_day_brief_payload



def _sample_facts() -> dict:
    return {
        "local_dt": "2026-03-27T07:00:00+03:00",
        "moon_phase": "Растущая Луна",
        "moon_sign": "Рыбы",
        "moon_emoji": "🌔",
        "aspects_count": 2,
        "aspect_summary": "Марс квадрат Солнце, Венера секстиль Венера",
        "traffic_lights": {"health": "red", "money": "green", "love": "yellow"},
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
        "year_data": {"profection": {"house": 10}},
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


def test_build_day_brief_payload_returns_strict_contract_shape() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(
            birth_time="07:05",
            birth_time_known=True,
            subscription_active_until=datetime(2026, 4, 3, tzinfo=timezone.utc),
        ),
        general_vibe="Главный акцент дня: действуй точечно и не спорь на скорости.",
        generation_mode="llm",
    )
    assert payload["version"] == "day_brief_canon_v1"
    assert payload["status"] in {"complete", "partial"}
    assert set(payload.keys()) == {"version", "status", "date", "personalization_level", "hero", "domains", "premium", "cta"}
    assert set(payload["domains"].keys()) == {"energy", "money", "love", "focus"}
    assert "windows" not in payload
    assert "best_uses" not in payload
    assert "risks" not in payload


def test_build_day_brief_payload_populates_domain_texts() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    money = payload["domains"]["money"]
    assert money["score_status"] == "complete"
    assert money["description_status"] == "complete"
    assert money["why_status"] == "complete"
    assert money["description"]
    assert money["why_astro_text"]
    assert isinstance(money["evidence_refs"], list)


def test_build_day_brief_payload_uses_explicit_domain_statuses_without_fallback_copy() -> None:
    payload = build_day_brief_payload(
        {
            "local_dt": "2026-03-27T07:00:00+03:00",
            "personalization_level": "anonymous",
            "semantic_layer": {},
            "fast_hits": [],
            "year_data": {},
        },
        user=None,
        generation_mode="deterministic",
    )
    assert payload["status"] in {"partial", "complete"}
    for domain in payload["domains"].values():
        assert domain["score_status"] in {"complete", "missing", "failed"}
        assert domain["description_status"] in {"complete", "missing", "failed"}
        assert domain["why_status"] in {"complete", "missing", "failed"}
    assert "fallback_mode" not in payload


def test_build_day_brief_telemetry_uses_complete_domain_count() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    telemetry = build_day_brief_telemetry(payload, generation_mode="deterministic", trace_id="trace-x", request_id="req-x")
    assert telemetry["trace_id"] == "trace-x"
    assert telemetry["request_id"] == "req-x"
    assert telemetry["confidence_bucket"] in {"high", "medium", "low"}
    assert telemetry["factor_count"] >= 0


def test_validate_day_brief_payload_accepts_strict_contract() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    model = validate_day_brief_payload(payload)
    assert model.hero.title
    assert model.domains["energy"].title


def test_day_brief_payload_has_no_windows_actions_or_risks() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    assert "windows" not in payload
    assert "best_uses" not in payload
    assert "risks" not in payload


def test_day_brief_payload_has_only_four_domains() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    assert set(payload["domains"].keys()) == {"energy", "money", "love", "focus"}


def test_day_brief_payload_uses_canonical_domain_titles() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    assert payload["domains"]["energy"]["title"] == "Тонус"
    assert payload["domains"]["money"]["title"] == "Работа и деньги"
    assert payload["domains"]["love"]["title"] == "Чувства"
    assert payload["domains"]["focus"]["title"] == "Фокус"


def test_day_brief_payload_contains_only_canonical_surface_fields() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    assert set(payload.keys()).issubset({"version", "status", "date", "personalization_level", "hero", "domains", "premium", "cta"})
    assert {"version", "status", "date", "personalization_level", "hero", "domains", "cta"}.issubset(payload.keys())
    assert "summary" not in payload
    assert "explainability" not in payload


def test_day_brief_payload_never_sets_fallback_mode() -> None:
    payload = build_day_brief_payload(_sample_facts(), user=None, generation_mode="deterministic")
    assert "fallback_mode" not in payload
