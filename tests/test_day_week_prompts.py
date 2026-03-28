from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from backend.app.services.day_brief import (
    DAY_BRIEF_PROMPT_VERSION,
    build_day_brief_fallback,
    build_day_brief_prompt_bundle,
)
from backend.app.services.week_brief_service import (
    WEEK_BRIEF_PROMPT_VERSION,
    _build_week_brief_fallback,
    build_week_brief_prompt_bundle,
)


def test_day_brief_prompt_bundle_and_fallback_are_deterministic():
    facts = {
        "local_dt": "2026-03-27T09:00:00+03:00",
        "semantic_layer": {
            "focus_key": "money_admin",
            "headline": "День любит аккуратный ход и ясную фиксацию.",
            "pacing": "Лучше идти короткими циклами.",
        },
    }
    prompt = build_day_brief_prompt_bundle(facts, general_vibe="спокойный деловой фокус")
    assert prompt["version"] == DAY_BRIEF_PROMPT_VERSION
    assert prompt["model"] == "deterministic_repo"
    assert isinstance(prompt["seed"], int)
    assert "спокойный деловой фокус" in prompt["prompt"]

    payload = build_day_brief_fallback(datetime(2026, 3, 27, 6, 0, tzinfo=timezone.utc), general_vibe="спокойный деловой фокус")
    assert payload["fallback_mode"] is True
    assert payload["summary"]["headline"]
    assert payload["best_uses"][0]["text"]
    assert payload["risks"][0]["text"]


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
