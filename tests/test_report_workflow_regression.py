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
