from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from backend.app.services.day_brief import build_day_brief_payload
from backend.app.services.week_brief_service import (
    WEEK_BRIEF_PROMPT_VERSION,
    _build_week_brief_fallback,
    build_week_brief_prompt_bundle,
)


def test_day_brief_payload_is_canonical_only_and_omits_legacy_surface():
    payload = build_day_brief_payload(
        {
            "local_dt": "2026-03-27T09:00:00+03:00",
            "semantic_layer": {
                "focus_key": "money_admin",
                "headline": "День любит аккуратный ход и ясную фиксацию.",
                "pacing": "Лучше идти короткими циклами.",
                "practical_move": "Закрепи один главный шаг письменно.",
                "money_admin_focus": "Сверяй цифры и формулировки.",
                "relationship_softness": "Говори мягче и точнее.",
                "rest": "Не прожимай день первым рывком.",
            },
            "personalization_level": "personalized_v2",
        },
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        general_vibe="спокойный деловой фокус",
        generation_mode="deterministic",
    )
    assert payload["version"] == "day_brief_canon_v1"
    assert set(payload.keys()) == {"version", "status", "date", "personalization_level", "hero", "domains", "premium", "cta"}
    assert "windows" not in payload
    assert "best_uses" not in payload
    assert "risks" not in payload
    assert "fallback_mode" not in payload


def test_day_brief_hero_and_focus_are_not_near_duplicates():
    payload = build_day_brief_payload(
        {
            "local_dt": "2026-04-11T09:00:00+03:00",
            "semantic_layer": {
                "headline": "День лучше держать в одном векторе и не обещать лишнего.",
                "pacing": "Выбери один главный шаг, не распыляйся и не открывай лишние фронты.",
                "practical_move": "Собери короткий список дел и закрой один документ до конца.",
                "money_admin_focus": "Проверь условия, цифры и сроки перед подтверждением.",
                "relationship_softness": "Говори мягче и точнее.",
                "rest": "Не прожимай день первым рывком.",
            },
            "personalization_level": "personalized_v2",
        },
        user=SimpleNamespace(birth_time="07:05", birth_time_known=True),
        general_vibe="спокойный деловой фокус",
        generation_mode="deterministic",
    )
    hero_text = f"{payload['hero']['title']} {payload['hero']['subtitle']}".lower()
    focus_description = payload["domains"]["focus"]["description"].lower()
    money_description = payload["domains"]["money"]["description"].lower()

    assert "один документ" not in focus_description
    assert "не обещать" not in focus_description
    assert "список дел" not in focus_description
    assert any(token in focus_description for token in ("вниман", "переключ", "приоритет", "контур", "перегруз"))
    assert any(token in money_description for token in ("услов", "цифр", "срок", "договор", "документ", "соглас"))
    assert len(payload["hero"]["title"]) <= 72
    assert len(payload["hero"]["subtitle"]) <= 150
    assert payload["domains"]["focus"]["description"] not in hero_text


def test_week_brief_prompt_bundle_and_fallback_are_deterministic():
    report = SimpleNamespace(
        id="r1",
        report_type="week_forecast",
        status="completed",
        created_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
    )
    seed = {
        "days": [{"date": "2026-03-30", "weekday": "monday", "traffic_light": "GREEN"}] * 7,
        "summary": {"traffic_light": "YELLOW"},
        "semantic_layer": {"focus_key": "launch", "headline": "Неделя просит собранного запуска."},
    }
    prompt = build_week_brief_prompt_bundle(seed)
    assert prompt["version"] == WEEK_BRIEF_PROMPT_VERSION
    assert prompt["model"] == "deterministic_repo"
    assert isinstance(prompt["seed"], int)
    assert "Неделя просит собранного запуска." in prompt["prompt"]

    fallback = _build_week_brief_fallback(report=report, payload=None, context={"week_brief_seed": seed}, chunks=[], user=None)
    assert fallback["fallback_mode"] is True
    assert fallback["summary"]["headline"]
    assert fallback["best_uses"][0]["text"]
    assert fallback["risks"][0]["text"]
