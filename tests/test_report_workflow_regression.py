import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class _GeneratedSection:
    def __init__(self, content, usage=None):
        self.content = content
        self.usage = usage or {}

from backend.app.models import Report
from backend.app.services.report_workflow import (
    build_report_context,
    build_section_specs,
    generate_report_sections,
    load_section_specs_for_report,
)
from backend.app.reporting.section_templates import get_default_sections


@pytest.fixture
def workflow_payload():
    return SimpleNamespace(
        report_type="natal_master",
        report_mode="full",
        sections=None,
        birth_time_known=True,
        house_system="placidus",
        birth_date="1990-01-01T12:00:00",
        birth_location="Moscow",
        birth_lat=55.75,
        birth_lon=37.61,
        birth_timezone="Europe/Moscow",
        include_fixed_stars=False,
        fixed_star_orb=1.0,
        client_name="Regression User",
        solar_current_lat=None,
        solar_current_lon=None,
        solar_current_location=None,
        solar_current_timezone=None,
    )


@pytest.fixture
def report_entity():
    return Report(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        report_type="natal_master",
        status="pending",
    )


def test_build_section_specs_uses_section_templates_defaults(workflow_payload):
    workflow_specs = build_section_specs(workflow_payload)
    template_specs = get_default_sections("natal_master", mode="full")

    assert [spec.section_id for spec in workflow_specs] == [spec.section_id for spec in template_specs]
    assert workflow_specs[0].title == template_specs[0].title
    assert workflow_specs[-1].section_id == template_specs[-1].section_id


@pytest.mark.parametrize(
    ("payload_data", "expected_source"),
    [
        ({"report_type": "month_forecast", "report_mode": "full"}, "payload_data"),
        ({"report_type": "natal_master", "sections": "broken"}, "default_catalog"),
        (None, "default_catalog"),
    ],
)
def test_load_section_specs_for_report_resume_and_fallback(payload_data, expected_source, report_entity):
    with patch("backend.app.services.report_workflow._workflow_log") as workflow_log:
        specs = load_section_specs_for_report(report_entity, payload_data)

    assert specs
    if expected_source == "payload_data":
        assert [spec.section_id for spec in specs] == [
            spec.section_id for spec in get_default_sections("month_forecast", mode="full")
        ]
    else:
        assert [spec.section_id for spec in specs] == [
            spec.section_id for spec in get_default_sections(report_entity.report_type, mode="full")
        ]

    completed_logs = [call.kwargs for call in workflow_log.call_args_list if call.args[1] == "report.workflow.resume_restore_complete"]
    assert completed_logs
    assert completed_logs[-1]["source"] == expected_source


def test_generate_report_sections_build_path_marks_completed(workflow_payload, report_entity):
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    successful_content = _GeneratedSection('[{"type":"paragraph","text":"section ok"}]')

    with (
        patch("backend.app.services.report_workflow.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.services.report_workflow.build_report_context", return_value={"client": {"gender": "female"}}),
        patch("backend.app.services.report_workflow.initialize_report_chunks", return_value={}),
        patch("backend.app.services.report_workflow.generate_section_content", side_effect=[successful_content] * len(get_default_sections("natal_master", mode="full"))),
        patch("backend.app.services.report_workflow.render_report_chunks_to_messages", return_value=[]),
    ):
        import asyncio
        results, chart = asyncio.run(generate_report_sections(
            report_entity,
            workflow_payload,
            db,
            llm_client=MagicMock(),
            llm_mode="openrouter",
            reset_chunks=True,
            raise_on_error=False,
        ))

    assert chart == {"chart": "ok"}
    assert len(results) == len(get_default_sections("natal_master", mode="full"))
    assert report_entity.status == "completed"
    assert report_entity.error_message is None
    assert db.commit.called


def test_generate_report_sections_error_path_marks_failed(workflow_payload, report_entity):
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    success = _GeneratedSection('[{"type":"paragraph","text":"ok"}]')
    fallback = _GeneratedSection('[{"type":"callout","variant":"error","title":"Ошибка генерации","content":"boom"}]')

    with (
        patch("backend.app.services.report_workflow.build_chart_data", return_value={"chart": "ok"}),
        patch("backend.app.services.report_workflow.build_report_context", return_value={"client": {"gender": "female"}}),
        patch("backend.app.services.report_workflow.initialize_report_chunks", return_value={}),
        patch("backend.app.services.report_workflow.generate_section_content", side_effect=[success, success] + [fallback] * (len(get_default_sections("natal_master", mode="full")) - 2)),
        patch("backend.app.services.report_workflow.render_report_chunks_to_messages", return_value=[]),
    ):
        import asyncio
        results, _chart = asyncio.run(generate_report_sections(
            report_entity,
            workflow_payload,
            db,
            llm_client=MagicMock(),
            llm_mode="openrouter",
            reset_chunks=True,
            raise_on_error=False,
        ))

    assert len(results) == len(get_default_sections("natal_master", mode="full"))
    assert report_entity.status == "failed"
    assert "only 2" in (report_entity.error_message or "")
    assert "min 5" in (report_entity.error_message or "")


def test_build_report_context_week_forecast_exports_week_brief_seed():
    payload = SimpleNamespace(
        report_type="week_forecast",
        report_id="rep-1",
        client_name="Week User",
        client_note=None,
        birth_date="1990-01-01T12:00:00",
        birth_location="Moscow",
        birth_lat=55.75,
        birth_lon=37.61,
        birth_timezone="Europe/Moscow",
        birth_place_id=None,
        partner_name=None,
        partner_birth_date=None,
        partner_birth_location=None,
        partner_birth_lat=None,
        partner_birth_lon=None,
        partner_birth_timezone=None,
        partner_birth_place_id=None,
        solar_current_location="Moscow",
        solar_current_lat=55.75,
        solar_current_lon=37.61,
        solar_current_timezone="Europe/Moscow",
        solar_current_place_id=None,
        solar_next_location=None,
        solar_next_lat=None,
        solar_next_lon=None,
        solar_next_timezone=None,
        solar_next_place_id=None,
        birth_time_known=True,
        house_system="placidus",
        question=None,
    )
    chart_data = {"facts": "ok"}

    engine = MagicMock()
    natal_chart = SimpleNamespace()
    engine.create_natal_chart.return_value = natal_chart
    engine.calculate_forecast_week_data.return_value = {
        "summary": {"traffic_light": "YELLOW", "avg_tension": 0.5},
        "days": [
            {
                "date": "2026-03-30",
                "weekday": "Monday",
                "moon": {"sign": "Овен", "phase": "Растущая", "void_of_course": False},
                "traffic_light": "YELLOW",
                "traffic_desc": "🟡 Внимание",
                "tension_score": 0.5,
            }
        ],
    }
    engine.calculate_forecast_month_data.return_value = {
        "major_transits": ["31.03 Сатурн Квадрат Солнце"],
        "retrogrades": ["01.04 Меркурий -> R (Ретро)"],
        "lunations": ["05.04 Полнолуние в Весах"],
    }
    engine.calculate_forecast_year_data.return_value = {
        "profection": {"house": 10, "lord": "Венера", "age": 36},
        "solar_return": {"datetime": "2026-03-20T10:00:00+03:00", "asc_sign": "Овен", "sun_house": 10},
        "solar_arcs": [{"direction": "Сатурн", "natal": "MC", "orb": 0.4}],
    }

    with (
        patch("backend.app.services.report_workflow.StelliumEngine", return_value=engine),
        patch("backend.app.services.report_workflow.get_chart_facts_json", return_value={"v": "facts_v1", "pos": [], "houses": []}),
        patch("backend.app.services.report_workflow.engine_utils.resolve_house_system", return_value="placidus"),
    ):
        context = build_report_context(payload, chart_data)

    assert "week_forecast_data" in context
    assert "month_forecast_data" in context
    assert "year_forecast_data" in context
    assert "week_brief_seed" in context
    assert context["week_brief_seed"]["slow_background"]["profection"]["house"] == 10
    assert context["week_brief_seed"]["slow_background"]["solar_arcs"][0]["direction"] == "Сатурн"
    assert context["week_brief_seed"]["slow_background"]["long_transits"] == ["31.03 Сатурн Квадрат Солнце"]
