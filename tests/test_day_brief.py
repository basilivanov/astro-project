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

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.day_brief import (
    build_day_brief_fallback,
    build_day_brief_payload,
    build_day_brief_telemetry,
)
from backend.app.services.day_brief_validators import validate_day_brief_payload


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
    assert payload["explainability"]["selected_factors"]
    assert payload["explainability"]["birth_time_used"] is True
    assert payload["explainability"]["timing_precision"] == "exact"
    assert payload["explainability"]["reliability_support"]
    assert payload["explainability"]["calibration"]["weight_profile_version"] == "v2"
    assert payload["premium"]["subscription_active"] is True
    assert payload["cta"]["primary"]["type"] == "open_week"
    assert payload["legacy"]["general_vibe"].startswith("Главный акцент дня")


def test_build_day_brief_payload_keeps_score_disclosures_item_local() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        general_vibe="Главный акцент дня: Марс квадрат Солнце. Действуй точечно и не спорь на скорости.",
        generation_mode="llm",
    )

    scores = {item["key"]: item for item in payload["scores"]}
    energy_factors = scores["energy"]["details"]["supporting_factors"]
    money_factors = scores["money"]["details"]["supporting_factors"]
    love_factors = scores["love"]["details"]["supporting_factors"]

    assert energy_factors == []
    assert all("Венера" in str(item.get("label") or "") for item in money_factors)
    assert love_factors == []



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
    assert telemetry["request_id"] == telemetry["trace_id"]
    assert telemetry["birth_time_used"] is False
    assert telemetry["confidence_bucket"] in {"low", "medium"}


@patch("backend.app.services.day_brief._log_day_brief_event")
def test_build_day_brief_payload_keeps_personalized_payload_when_logging_fails(mock_log_event) -> None:
    mock_log_event.side_effect = RuntimeError("synthetic log failure")

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

    assert payload["fallback_mode"] is False
    assert payload["personalization_level"] != "anonymous"
    assert payload["premium"]["subscription_active"] is True
    assert payload["cta"]["primary"]["type"] == "open_week"
    assert payload["explainability"]["birth_time_used"] is True


def test_build_day_brief_payload_clips_long_explainability_labels_instead_of_falling_back() -> None:
    facts = _sample_facts()
    long_label = (
        "День про рабочие и статусные договоренности проще собирать через вежливость и форму, "
        "но личное желание и эмоциональная реакция спорят за центр дня."
    )
    facts["semantic_layer"]["headline"] = long_label
    facts["fast_hits"] = []
    facts["meta"] = {"fallback_mode": False}
    facts["normalized_factors"] = [
        SimpleNamespace(
            id="semantic:money_admin",
            label=long_label,
            domain="money",
            family="slow_background",
            signal=0.45,
            weight=1.0,
            explanation_human="Выбери один главный шаг, зафиксируй его письменно и не распыляйся на всё сразу.",
            explanation_astro="",
            metadata={},
        )
    ]

    payload = build_day_brief_payload(
        facts,
        user=SimpleNamespace(
            birth_time="07:05",
            birth_time_known=True,
            subscription_active_until=datetime(2026, 4, 3, tzinfo=timezone.utc),
        ),
        general_vibe="Главный акцент дня: мягкий, но точный темп.",
        generation_mode="llm",
    )

    assert payload["fallback_mode"] is False
    model = validate_day_brief_payload(payload)
    assert model.fallback_mode is False
    assert model.personalization_level == "personalized_v2"
    assert model.explainability.selected_factors
    assert len(model.explainability.selected_factors[0].label) <= 120


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


def test_build_daily_forecast_semantic_headline_avoids_run_on_joiner() -> None:
    from backend.app.services.forecast_semantics import build_daily_forecast_semantic_layer

    payload = build_daily_forecast_semantic_layer(
        fast_hits=[
            {"transit": "Venus", "natal": "MC", "type": "Секстиль (60°)"},
            {"transit": "Sun", "natal": "Moon", "type": "Квадрат (90°)"},
        ],
        traffic_lights={"money": "red", "love": "red", "health": "red"},
        day_context={},
        month_data={},
    )

    assert ", но важно помнить: " in payload["headline"]
    assert "но личное желание" not in payload["headline"]

def test_build_day_brief_payload_populates_score_supporting_factors_from_selected_explainability() -> None:
    payload = build_day_brief_payload(
        {
            'personalization_level': 'personalized_v2',
            'meta': {'fallback_mode': False},
            'timezone': 'Europe/Moscow',
            'location_label': 'Мончегорск, Россия',
            'moon_sign': 'Весы',
            'moon_phase': 'Полнолуние',
            'moon_emoji': '🌕',
            'aspects_count': 2,
            'traffic_lights': {'health': 'green', 'money': 'green', 'love': 'green'},
            'fast_hits': [
                {'transit': 'Mercury', 'natal': 'Mercury', 'type': 'Тригон (120°)', 'summary': 'Меркурий Тригон (120°) Меркурий'},
                {'transit': 'Sun', 'natal': 'Mars', 'type': 'Тригон (120°)', 'summary': 'Солнце Тригон (120°) Марс'},
            ],
            'semantic_layer': {
                'headline': 'День про проще собрать мысль, договориться о деталях и сшить разрозненные вводные: хороший результат дает короткий и взрослый ход.',
                'practical_move': 'Двигай одну покупку, одно условие или одну рабочую задачу, а остальное оставь в фоне.',
                'pacing': 'рабочий темп держится на одном-двух приоритетах, без расползания в суету',
                'rest': 'силы лучше держатся на ровном темпе, чем на вспышках',
                'money_admin_focus': 'рабочие и денежные вопросы лучше собирать по одному, а не параллельной пачкой',
                'relationship_softness': 'отношения сегодня любят ясность без нажима и без скрытых проверок',
                'focus_key': 'launch',
                'friction': 'распыление внимания, лишние обещания и попытка решить все одним рывком',
            },
        },
        user=None,
        generation_mode='deterministic',
    )

    scores = {item['key']: item for item in payload['scores']}
    assert scores['energy']['details']['supporting_factors']
    assert scores['money']['details']['supporting_factors']
    assert scores['love']['details']['supporting_factors']
    assert any('Солнце Тригон (120°) Марс' in (factor.get('label') or '') for factor in scores['energy']['details']['supporting_factors'])
    assert any('money:green' in (factor.get('label') or '') for factor in scores['money']['details']['supporting_factors'])
    assert any('love:green' in (factor.get('label') or '') for factor in scores['love']['details']['supporting_factors'])


def test_build_day_brief_payload_keeps_score_disclosure_honest_without_local_factors() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(
            birth_time="07:05",
            birth_time_known=True,
            subscription_active_until=datetime(2026, 4, 3, tzinfo=timezone.utc),
        ),
        general_vibe="Главный акцент дня: действуй точечно и без лишнего шума.",
    )

    focus_score = next(item for item in payload["scores"] if item["key"] == "focus")
    assert focus_score.get("details") is None or focus_score["details"].get("supporting_factors") == []


def test_build_day_brief_payload_dedupes_windows_and_risks_and_links_factors() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(
            birth_time="07:05",
            birth_time_known=True,
            subscription_active_until=datetime(2026, 4, 3, tzinfo=timezone.utc),
        ),
        general_vibe="Главный акцент дня: действуй точечно и без лишнего шума.",
    )

    assert payload["windows"]
    assert len({(item["start"], item["end"], item["label"]) for item in payload["windows"]}) == len(payload["windows"])
    assert all(item["label"] in {"Собрать ядро дня", "Согласовать и договориться", "Проверить и сверить", "Снизить темп и восстановиться", "Удержать глубокий фокус"} for item in payload["windows"])
    assert any(item.get("details", {}).get("factor_ids") for item in payload["windows"] if item.get("details"))

    risks = payload["risks"]
    assert len({(item["text"], item.get("timeframe")) for item in risks}) == len(risks)
    assert any(item.get("factor_ids") for item in risks)


def test_semantic_fingerprint_handles_punctuation_without_name_error() -> None:
    from backend.app.services.day_brief import _semantic_fingerprint

    fingerprint = _semantic_fingerprint("Марс: квадрат Солнце!", "Фокус, проверка; договоренности")

    assert "марс" in fingerprint
    assert "солнце" in fingerprint
