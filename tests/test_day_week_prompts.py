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
