import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.services.week_brief_service import (
    build_week_brief_envelope,
    build_week_brief_payload,
)
from backend.app.services.week_brief_validators import (
    validate_week_brief_envelope_payload,
    validate_week_brief_payload,
)


def _sample_context() -> dict:
    return {
        "forecast_window": {"start": "2026-03-30T05:00:00+03:00", "days": 7},
        "week_forecast_data": {
            "summary": {"traffic_light": "YELLOW", "avg_tension": 0.7},
            "days": [
                {
                    "date": "2026-03-30",
                    "weekday": "Monday",
                    "moon": {"sign": "Овен", "phase": "Растущая", "void_of_course": False},
                    "ingresses": ["Меркурий -> Овен"],
                    "aspects": [{"transit": "Марс", "natal": "Солнце", "aspect": "Квадрат"}],
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                    "tension_score": 0.7,
                },
                {
                    "date": "2026-03-31",
                    "weekday": "Tuesday",
                    "moon": {"sign": "Телец", "phase": "Растущая", "void_of_course": False},
                    "aspects": [{"transit": "Венера", "natal": "Венера", "aspect": "Секстиль"}],
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "tension_score": -0.4,
                },
                {
                    "date": "2026-04-01",
                    "weekday": "Wednesday",
                    "moon": {"sign": "Близнецы", "phase": "Растущая", "void_of_course": False},
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                    "tension_score": 0.3,
                },
                {
                    "date": "2026-04-02",
                    "weekday": "Thursday",
                    "moon": {"sign": "Рак", "phase": "Растущая", "void_of_course": True},
                    "traffic_light": "RED",
                    "traffic_desc": "🔴 Шторм",
                    "tension_score": 2.3,
                },
                {
                    "date": "2026-04-03",
                    "weekday": "Friday",
                    "moon": {"sign": "Лев", "phase": "Растущая", "void_of_course": False},
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "tension_score": -0.3,
                },
                {
                    "date": "2026-04-04",
                    "weekday": "Saturday",
                    "moon": {"sign": "Дева", "phase": "Растущая", "void_of_course": False},
                    "traffic_light": "YELLOW",
                    "traffic_desc": "🟡 Внимание",
                    "tension_score": 0.4,
                },
                {
                    "date": "2026-04-05",
                    "weekday": "Sunday",
                    "moon": {"sign": "Весы", "phase": "Полнолуние", "void_of_course": False},
                    "traffic_light": "GREEN",
                    "traffic_desc": "🟢 Зеленый",
                    "tension_score": -0.1,
                },
            ],
        },
        "month_forecast_data": {
            "major_transits": [
                "31.03 Сатурн Квадрат Солнце",
                "04.04 Юпитер Тригон Меркурий",
            ],
            "ingresses": ["30.03 Меркурий -> Овен"],
            "retrogrades": ["01.04 Меркурий -> R (Ретро)"],
            "lunations": ["05.04 Полнолуние в Весах"],
        },
        "year_forecast_data": {
            "profection": {"house": 10, "lord": "Венера", "age": 36},
            "solar_return": {"datetime": "2026-03-20T10:00:00+03:00", "asc_sign": "Овен", "sun_house": 10},
            "solar_arcs": [{"direction": "Сатурн", "natal": "MC", "orb": 0.4}],
        },
    }


def _sample_chunks():
    return [
        SimpleNamespace(section="week_strategy", content='[{"type":"header","level":2,"text":"Стратегия недели"},{"type":"paragraph","text":"Неделя лучше идет через одну линию и короткие проверки."}]', status="completed", order_index=0),
        SimpleNamespace(section="money", content='[{"type":"header","level":2,"text":"Работа и деньги"},{"type":"list","items":["Подтверждай условия письменно","Сужай фронт до главного"]}]', status="completed", order_index=1),
    ]


def _sample_report(status: str = "completed"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        report_type="week_forecast",
        status=status,
        created_at=datetime(2026, 3, 30, 5, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 30, 6, 0, tzinfo=timezone.utc),
        error_message=None,
    )


def _sample_payload():
    return SimpleNamespace(llm_mode="cheap", birth_time_known=True)


def test_build_week_brief_payload_validates_schema_and_logs_telemetry():
    report = _sample_report()
    chunks = _sample_chunks()
    telemetry = []

    with patch("backend.app.services.week_brief_service.log_grace_event", side_effect=lambda *args, **kwargs: telemetry.append((args, kwargs))):
        payload = build_week_brief_payload(
            report=report,
            payload=_sample_payload(),
            context=_sample_context(),
            chunks=chunks,
            user=SimpleNamespace(subscription_active_until=datetime(2026, 4, 30, tzinfo=timezone.utc)),
            llm_model="deterministic",
        )

    validated = validate_week_brief_payload(payload)
    assert validated["status"] == "ready"
    assert validated["fallback_mode"] is False
    assert len(validated["day_cards"]) == 7
    assert len(validated["domains"]) == 4
    assert len(validated["major_factors"]) >= 1
    assert len(validated["deep_sections"]) >= 2
    assert [section["slug"] for section in validated["deep_sections"][:2]] == ["overview", "timing"]
    assert validated["report_ref"]["report_id"] == str(report.id)
    built_events = [call for call in telemetry if call[0][1] == "week_brief_built"]
    assert built_events
    assert built_events[-1][1]["week_brief_fallback_mode"] is False
    assert built_events[-1][1]["week_brief_confidence_bucket"] in {"medium", "high"}


def test_build_week_brief_payload_falls_back_but_stays_schema_valid():
    report = _sample_report(status="failed")
    bad_chunks = [SimpleNamespace(section="week_strategy", content="{not-json", status="failed", order_index=0)]
    telemetry = []

    with patch("backend.app.services.week_brief_service.log_grace_event", side_effect=lambda *args, **kwargs: telemetry.append((args, kwargs))):
        payload = build_week_brief_payload(
            report=report,
            payload=_sample_payload(),
            context={},
            chunks=bad_chunks,
            user=None,
            llm_model="deterministic",
        )

    validated = validate_week_brief_payload(payload)
    assert validated["status"] == "error"
    assert validated["fallback_mode"] is True
    assert len(validated["day_cards"]) == 7
    assert len(validated["major_factors"]) == 1
    assert [section["slug"] for section in validated["deep_sections"]] == ["overview"]
    assert "# Каркас недели" in validated["deep_sections"][0]["body_markdown"]
    assert any(call[0][1] == "week_brief_fallback_triggered" for call in telemetry)
    assert any(call[0][1] == "week_brief_built" and call[1]["week_brief_fallback_mode"] is True for call in telemetry)


def test_build_week_brief_payload_keeps_seed_sections_when_chunk_json_is_invalid():
    report = _sample_report()
    bad_chunks = [
        SimpleNamespace(section="week_strategy", content="{not-json", status="failed", order_index=0),
        SimpleNamespace(section="money", content="plain prose that is not json", status="completed", order_index=1),
    ]

    payload = build_week_brief_payload(
        report=report,
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=bad_chunks,
        user=None,
        llm_model="deterministic",
    )

    validated = validate_week_brief_payload(payload)
    assert validated["fallback_mode"] is False
    assert [section["slug"] for section in validated["deep_sections"][:3]] == ["overview", "timing", "background"]
    assert all(section["summary"] for section in validated["deep_sections"])
    assert "Неделя" in validated["deep_sections"][0]["body_markdown"] or "Каркас недели" in validated["deep_sections"][0]["body_markdown"]


def test_build_week_brief_envelope_supports_ready_and_in_progress_states():
    ready_report = _sample_report()
    ready_payload = build_week_brief_payload(
        report=ready_report,
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )
    ready_envelope = build_week_brief_envelope(report=ready_report, week_brief=ready_payload)
    validated_ready = validate_week_brief_envelope_payload(ready_envelope)

    assert validated_ready["status"] == "ready"
    assert validated_ready["data"]["report_ref"]["report_id"] == str(ready_report.id)

    pending_report = _sample_report(status="in_progress")
    pending_envelope = build_week_brief_envelope(report=pending_report, week_brief=None)
    validated_pending = validate_week_brief_envelope_payload(pending_envelope)

    assert validated_pending["status"] == "in_progress"
    assert validated_pending["data"] is None
    assert validated_pending["retry_after_seconds"] == 3


def test_week_top_layer_is_deterministic_for_same_seed():
    report = _sample_report()
    context = _sample_context()
    payload_a = build_week_brief_payload(
        report=report,
        payload=_sample_payload(),
        context=context,
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )
    payload_b = build_week_brief_payload(
        report=report,
        payload=_sample_payload(),
        context=context,
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    assert payload_a["major_factors"] == payload_b["major_factors"]
    assert [item["id"] for item in payload_a["major_factors"]] == [item["id"] for item in payload_b["major_factors"]]


def test_week_brief_prefers_theme_anchor_and_preserves_explainability_order():
    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    factor_ids = [item["id"] for item in payload["major_factors"]]
    assert factor_ids[0] == "week:theme_anchor"
    assert "week:profection:10" in factor_ids
    assert payload["explainability"]["factor_count"] >= len(payload["major_factors"])
    assert payload["explainability"]["reliability_support"]
    assert payload["explainability"]["calibration"]["weight_profile_version"] == "v2"

def test_validate_week_brief_payload_preserves_week_explainability_extension_fields():
    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=_sample_chunks(),
        user=None,
        llm_model="deterministic",
    )

    validated = validate_week_brief_payload(payload)

    assert validated["fallback_mode"] is False
    assert validated["explainability"]["reliability_support"]
    assert validated["explainability"]["calibration"]["weight_profile_version"] == "v2"
    assert "entrypoints" in validated["explainability"]["calibration"]

def test_week_brief_keeps_non_fallback_when_seed_is_complete_but_some_chunks_are_degraded():
    payload = build_week_brief_payload(
        report=_sample_report(),
        payload=_sample_payload(),
        context=_sample_context(),
        chunks=[
            SimpleNamespace(
                section="week_strategy",
                content='[{"type":"header","level":2,"text":"Стратегия недели"},{"type":"paragraph","text":"Неделя лучше идет через одну линию и короткие проверки."}]',
                status="completed",
                order_index=0,
            ),
            SimpleNamespace(
                section="money",
                content="plain markdown text from degraded live chunk",
                status="failed",
                order_index=1,
            ),
        ],
        user=None,
        llm_model="deterministic",
    )

    validated = validate_week_brief_payload(payload)

    assert validated["fallback_mode"] is False
    assert validated["deep_sections"]
    assert any(section["slug"] == "overview" for section in validated["deep_sections"])
    assert validated["explainability"]["confidence"] < 0.9
    assert validated["explainability"]["explanation_depth"] in {"full", "standard"}
