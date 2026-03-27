import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.app.main import get_report_detail


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
        "day_cards": [],
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
