import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.app.main import get_report_detail
from backend.app.services import report_workflow


def test_get_report_detail_returns_week_brief_without_changing_chunks():
    user = SimpleNamespace(id=uuid.uuid4())
    report = SimpleNamespace(
        id=uuid.uuid4(),
        report_type="week_forecast",
        status="completed",
        created_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        client=SimpleNamespace(full_name="Week Client"),
        access_source="subscription",
        chunks=[
            SimpleNamespace(section="week_strategy", content="[]", status="completed", order_index=0),
            SimpleNamespace(section="money", content="[]", status="completed", order_index=1),
        ],
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
            "subhead": "Сильные дни подходят для договоренностей, а слабые лучше вести через буфер и одну линию.",
            "week_type": "balance",
            "theme": "Работа, темп и границы",
        },
        "day_cards": [{
            "id": "week-day-2026-03-30",
            "date": "2026-03-30",
            "weekday": "mon",
            "mode": "green",
            "score": 81,
            "headline": "Держите один главный ритм",
            "lead": "День держится через один главный приоритет.",
            "practical": ["Закрыть приоритет"],
            "supporting_factors": [],
            "details": {"why_text": "Опора на устойчивый ритм.", "why_title": "Почему день так звучит", "supporting_factors": []},
            "factor_ids": ["week:theme_anchor"],
            "best_for": ["Стратегия"],
            "avoid": ["Суета"],
            "peak_window_label": "до 14:00"
        }],
        "domains": [],
        "best_uses": [],
        "risks": [],
        "major_factors": [],
        "deep_sections": [],
        "explainability": {
            "confidence": 0.8,
            "birth_time_used": True,
            "factor_count": 5,
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

    assert response["report"]["id"] == str(report.id)
    assert response["chunks"] == [
        {"section": "week_strategy", "content": "[]", "status": "completed", "order_index": 0},
        {"section": "money", "content": "[]", "status": "completed", "order_index": 1},
    ]
    assert response["week_brief"] == week_brief
    assert response["week_brief_envelope"]["status"] == "ready"
    assert response["week_brief_envelope"]["data"] == week_brief


def test_get_report_detail_keeps_week_brief_none_for_non_week_reports():
    user = SimpleNamespace(id=uuid.uuid4())
    report = SimpleNamespace(
        id=uuid.uuid4(),
        report_type="natal_master",
        status="completed",
        created_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        client=SimpleNamespace(full_name="Natal Client"),
        access_source="subscription",
        chunks=[],
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = report

    with (
        patch("backend.app.main.load_report_payload", return_value=SimpleNamespace()),
        patch("backend.app.main.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.main.build_natal_chart_svg", return_value="<svg />"),
    ):
        response = get_report_detail(str(report.id), user=user, db=db)

    assert response["week_brief"] is None
    assert response["week_brief_envelope"] is None


def test_week_prompt_context_delegates_to_week_owned_seed_boundary():
    week_seed = {
        "days": [{"date": "2026-03-30", "weekday_ru": "понедельник"}],
        "summary": {"traffic_light": "GREEN", "avg_tension": -0.1, "status_label": "GREEN"},
        "semantic_layer": {"headline": "Неделя дает ход."},
    }

    with patch("backend.app.services.report_workflow.build_week_brief_seed_bundle_owned", return_value=week_seed) as build_week_seed:
        result = report_workflow._build_week_forecast_prompt_context(
            {
                "client": {"gender": "female", "report_type": "week_forecast", "birth_time_known": True},
                "forecast_window": {"start": "2026-03-30T05:00:00+03:00", "days": 7},
            }
        )

    build_week_seed.assert_called_once()
    assert result["week_forecast_data"]["days"] == week_seed["days"]
    assert result["week_forecast_data"]["summary"] == week_seed["summary"]
    assert result["week_forecast_data"]["semantic_layer"] == week_seed["semantic_layer"]


def test_week_brief_api_contract_keeps_packet_local_service_entrypoints_stable():
    import backend.app.services.week_brief_service as week_brief_service

    assert week_brief_service.MODULE_ID == "M-WEEK-BRIEF-SERVICE"
    assert week_brief_service.WEEK_BRIEF_EVIDENCE_LANE == "packet_local"
    assert week_brief_service.WEEK_BRIEF_PACKET_SCOPE == "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:W01:packet_local"
    assert week_brief_service.WEEK_BRIEF_PAYLOAD_BLOCK == "WEEK_BRIEF_PAYLOAD_ASSEMBLY"
    assert callable(week_brief_service.build_week_brief_payload)
    assert callable(week_brief_service.build_week_brief_envelope)
