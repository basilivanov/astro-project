import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from backend.app.services.day_brief import build_day_brief_payload
from backend.app.services.day_brief_types import DayBrief
from backend.app.services.day_brief_validators import validate_day_brief_payload


def _sample_facts() -> dict:
    return {
        "local_dt": "2026-03-27T07:00:00+03:00",
        "moon_phase": "Растущая Луна",
        "moon_sign": "Рыбы",
        "moon_emoji": "🌔",
        "aspects_count": 2,
        "traffic_lights": {"health": "red", "money": "green", "love": "yellow"},
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
        "year_data": {"profection": {"house": 10}},
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


def test_day_brief_schema_exposes_strict_contract_keys() -> None:
    schema = DayBrief.schema()
    assert set(schema["properties"].keys()) == {
        "version",
        "status",
        "date",
        "personalization_level",
        "hero",
        "domains",
        "premium",
        "cta",
    }
    assert set(schema["required"]) == {"date", "personalization_level", "hero", "domains"}


def test_day_brief_payload_validates_against_pydantic_schema() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        general_vibe="День просит коротких циклов и ясной фиксации главного.",
        generation_mode="llm",
    )
    model = DayBrief.parse_obj(payload)
    assert model.version in {"day_brief_canon_v1", "day_brief_v2"}
    assert set(model.domains.keys()) == {"energy", "money", "love", "focus"}


def test_day_brief_json_schema_matches_runtime_shape() -> None:
    schema = DayBrief.schema()
    assert schema["title"] == "DayBrief"
    assert "hero" in schema["properties"]
    assert "domains" in schema["properties"]


def test_day_brief_validator_rejects_partial_required_contract() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        generation_mode="deterministic",
    )
    del payload["hero"]["title"]
    try:
        validate_day_brief_payload(payload)
    except Exception as exc:
        assert "title" in str(exc)
    else:
        raise AssertionError("validator must fail when required hero fields are missing")


def test_day_brief_validator_repairs_unknown_nested_keys_without_contract_drift() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        generation_mode="deterministic",
    )
    payload["unexpected"] = {"debug": True}
    payload["hero"]["extra_copy"] = "noise"
    payload["domains"]["energy"]["shadow"] = "noise"
    dumped = validate_day_brief_payload(payload).dict(exclude_none=True)
    assert "unexpected" not in dumped
    assert "extra_copy" not in dumped["hero"]
    assert "shadow" not in dumped["domains"]["energy"]
    assert dumped["version"] in {"day_brief_canon_v1", "day_brief_v2"}


def test_day_brief_validator_preserves_domain_texts() -> None:
    payload = build_day_brief_payload(
        _sample_facts(),
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        generation_mode="deterministic",
    )
    dumped = validate_day_brief_payload(payload).dict(exclude_none=True)
    assert dumped["domains"]["money"]["description"]
    assert dumped["domains"]["money"]["why_astro_text"]
