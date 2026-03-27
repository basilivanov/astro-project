import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from backend.app.services.day_brief import build_day_brief_fallback, build_day_brief_payload
from backend.app.services.day_brief_types import DayBrief


def _sample_facts() -> dict:
    return {
        "local_dt": "2026-03-27T07:00:00+03:00",
        "moon_phase": "Растущая Луна",
        "moon_sign": "Рыбы",
        "moon_emoji": "🌔",
        "aspects_count": 2,
        "traffic_lights": {"health": "yellow", "money": "green", "love": "yellow"},
        "week_data": {"days": [{"moon": {"sign": "Рыбы", "phase": "Растущая", "void_of_course": False}}]},
        "semantic_layer": {
            "headline": "День про короткий фокус, ясные формулировки и аккуратные решения.",
            "pacing": "Лучше держать день короткими циклами и с запасом по времени.",
            "rest": "Не тратить весь ресурс первым рывком.",
            "money_admin_focus": "Закрыть один документ или одно согласование, не дробя внимание.",
            "relationship_softness": "Говорить прямо, но мягко и без лишнего нажима.",
            "practical_move": "Продвинь один главный вопрос и сразу закрепи детали.",
            "focus_key": "money_admin",
        },
        "personalization_level": "personalized_v2",
        "meta": {"fallback_mode": False},
        "month_data": {"status": "GREEN"},
        "year_data": {"profection": {"house": 10}, "months": [{"month": 3, "status": "GREEN"}]},
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


def test_day_brief_schema_exposes_contract_keys() -> None:
    schema = DayBrief.model_json_schema()

    assert set(schema["properties"].keys()) == {
        "version",
        "date",
        "personalization_level",
        "fallback_mode",
        "summary",
        "context",
        "scores",
        "windows",
        "best_uses",
        "risks",
        "personalized_factors",
        "explainability",
        "premium",
        "cta",
        "legacy",
    }
    assert set(schema["required"]) == {
        "date",
        "personalization_level",
        "summary",
        "context",
        "scores",
        "explainability",
    }


def test_day_brief_payload_validates_against_pydantic_schema() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        general_vibe="День просит коротких циклов и ясной фиксации главного.",
        generation_mode="llm",
    )

    model = DayBrief.model_validate(payload)
    assert model.version == "day_brief_v1"


def test_day_brief_fallback_validates_against_pydantic_schema() -> None:
    payload = build_day_brief_fallback(
        datetime(2026, 3, 27, 6, 0, tzinfo=timezone.utc),
        general_vibe="Сегодня лучше держать короткий фокус и один главный шаг.",
        generation_mode="fallback",
        reason="schema-test",
    )

    model = DayBrief.model_validate(payload)
    assert model.fallback_mode is True

import json
from pathlib import Path


def test_day_brief_json_schema_matches_contract_artifact() -> None:
    schema_path = Path("tmp/day_brief.schema.json")
    contract = json.loads(schema_path.read_text())

    assert contract["title"] == "DayBrief"
    assert contract["properties"]["summary"]["$ref"] == "#/$defs/DaySummary"
    assert contract["properties"]["scores"]["items"]["$ref"] == "#/$defs/DayScore"
    assert contract["properties"]["explainability"]["$ref"] == "#/$defs/Explainability"

