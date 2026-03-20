import json
import pytest
from datetime import datetime, timezone
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.report_workflow import (
    build_chart_data,
    build_report_context,
    build_section_fallback_content,
    build_section_context,
    build_section_specs,
    resolve_solar_return_location,
    resolve_solar_return_target_year,
)
from backend.app.main import ReportWorkflowRequest

BASE_PAYLOAD = {
    "client_name": "Test User",
    "birth_date": "1990-01-01T12:00:00",
    "birth_location": "Moscow",
    "birth_lat": 55.7558,
    "birth_lon": 37.6173,
    "birth_timezone": "Europe/Moscow",
    "house_system": "Placidus",
    "include_fixed_stars": False,
    "fixed_star_orb": 1.0,
    "partner_name": "Partner",
    "partner_birth_date": "1992-02-02T06:30:00",
    "partner_birth_location": "London",
    "partner_birth_lat": 51.5074,
    "partner_birth_lon": -0.1278,
    "partner_birth_timezone": "Europe/London",
    "solar_current_location": "Moscow",
    "solar_current_lat": 55.7558,
    "solar_current_lon": 37.6173,
    "solar_current_timezone": "Europe/Moscow",
}

def test_horary_context_structure():
    print("\nTesting Horary Context...")
    req = ReportWorkflowRequest(
        **BASE_PAYLOAD,
        report_type="horary_answer",
        question="Will I pass the test?"
    )
    
    chart_data = build_chart_data(req)
    context = build_report_context(req, chart_data)
    
    assert "horary" in chart_data, "Horary data missing from chart"
    h = chart_data["horary"]
    assert "radicality" in h
    assert "dignities" in h
    assert "roles" in h
    assert "aspects" in h
    
    print("✅ Horary context keys present")
    
@pytest.mark.parametrize(
    "report_type",
    [
        "natal_master",
        "week_forecast",
        "month_forecast",
        "year_forecast",
        "ten_year_forecast",
        "horary_answer",
        "synastry",
        "solar_return",
    ],
)
def test_report_context_includes_facts(report_type):
    print(f"\nTesting context facts for {report_type}...")
    payload = dict(BASE_PAYLOAD)
    payload["report_type"] = report_type
    if report_type == "horary_answer":
        payload["question"] = "Will I pass the test?"

    req = ReportWorkflowRequest(**payload)
    chart_data = build_chart_data(req)
    context = build_report_context(req, chart_data)

    facts = context.get("facts")
    assert facts, f"facts missing for {report_type}"
    assert facts.get("v") == "facts_v1", f"facts schema missing for {report_type}"
    assert facts.get("pos"), f"facts.pos missing for {report_type}"
    assert facts.get("houses"), f"facts.houses missing for {report_type}"

    if report_type == "year_forecast":
        assert "year_forecast_data" in context
    if report_type == "month_forecast":
        assert "month_forecast_data" in context
    if report_type == "week_forecast":
        assert "week_forecast_data" in context
    if report_type == "ten_year_forecast":
        assert "decade_forecast_data" in context
        assert "ten_year_forecast_data" not in context


@pytest.mark.parametrize("report_type", ["week_forecast", "month_forecast"])
def test_forecast_section_context_is_trimmed_for_prompt(report_type):
    payload = dict(BASE_PAYLOAD)
    payload["report_type"] = report_type

    req = ReportWorkflowRequest(**payload)
    chart_data = build_chart_data(req)
    context = build_report_context(req, chart_data)
    spec = build_section_specs(req)[0]
    section_context = build_section_context(spec.section_id, context, chart_data)

    assert "chart" not in section_context
    assert "facts" not in section_context

    if report_type == "week_forecast":
        days = section_context["week_forecast_data"]["days"]
        assert days
        assert days[0]["weekday_ru"]
        assert days[0]["date_label"]
        assert "moon_label" in days[0]
        assert section_context["week_forecast_data"]["semantic_layer"]["headline"]
        assert section_context["week_forecast_data"]["semantic_layer"]["pacing"]
    else:
        month_data = section_context["month_forecast_data"]
        assert month_data["status"]
        assert month_data["key_events"]
        assert month_data["month_label"]
        assert month_data["status_summary"]
        assert month_data["central_task"]
        assert month_data["semantic_layer"]["headline"]
        assert month_data["semantic_layer"]["money_admin_focus"]
        assert month_data["semantic_layer"]["scene_seed"]
        assert month_data["semantic_layer"]["campaign_shape"]
        assert month_data["campaign_arc"]["opening_scene"]
        assert month_data["campaign_arc"]["phase_sequence"]
        assert month_data["campaign_arc"]["close_focus"]
        assert len(month_data["event_cards"]) >= 3
        assert len(month_data["phases"]) == 4
        assert month_data["phases"][0]["label"] == "Неделя 1"
        assert month_data["phases"][0]["date_range_label"]
        assert month_data["phases"][0]["phase_role"]
        assert month_data["phases"][0]["scene_hint"]
        assert month_data["phases"][0]["transition_hint"]
        assert month_data["phases"][0]["focus_hint"]
        assert month_data["phases"][0]["push_hint"]
        assert month_data["phases"][0]["restraint_hint"]


def test_month_forecast_fallback_uses_weekly_campaign_structure():
    payload = dict(BASE_PAYLOAD)
    payload["report_type"] = "month_forecast"

    req = ReportWorkflowRequest(**payload)
    chart_data = build_chart_data(req)
    context = build_report_context(req, chart_data)
    spec = build_section_specs(req)[0]
    section_context = build_section_context(spec.section_id, context, chart_data)
    content = build_section_fallback_content(spec, section_context)

    blocks = json.loads(content)
    headers = [
        str(block.get("text", "")).strip().lower()
        for block in blocks
        if block.get("type") == "header"
    ]
    phase_paragraphs = [
        str(block.get("text", "")).strip().lower()
        for block in blocks
        if block.get("type") == "paragraph"
    ]
    all_text = " ".join(
        [
            str(block.get("text", ""))
            + " "
            + str(block.get("content", ""))
            + " "
            + " ".join(str(item) for item in block.get("items", []))
            for block in blocks
        ]
    ).lower()

    assert "стратегия по неделям" in headers
    assert any(header.startswith("неделя 1") for header in headers)
    assert any(header.startswith("неделя 4") for header in headers)
    assert any(
        marker in " ".join(phase_paragraphs)
        for marker in ("сначала", "затем", "к середине", "в финале")
    )
    assert "что продвигать" in all_text
    assert "где не форсировать" in all_text


def test_resolve_solar_return_target_year_uses_active_personal_year():
    payload_data = dict(BASE_PAYLOAD)
    payload_data.update({
        "report_type": "solar_return",
        "birth_date": "1990-10-10T12:00:00",
    })
    payload = ReportWorkflowRequest(**payload_data)

    before_birthday = datetime(2026, 3, 19, tzinfo=timezone.utc)
    after_birthday = datetime(2026, 11, 1, tzinfo=timezone.utc)

    assert resolve_solar_return_target_year(payload, now=before_birthday) == 2025
    assert resolve_solar_return_target_year(payload, now=after_birthday) == 2026


def test_resolve_solar_return_location_prefers_explicit_solar_location():
    payload_data = dict(BASE_PAYLOAD)
    payload_data.update({
        "report_type": "solar_return",
        "solar_current_location": "Tbilisi",
        "solar_current_lat": 41.6938,
        "solar_current_lon": 44.8015,
        "solar_current_timezone": "Asia/Tbilisi",
    })
    payload = ReportWorkflowRequest(**payload_data)

    sr_location = resolve_solar_return_location(payload)

    assert sr_location["name"] == "Tbilisi"
    assert sr_location["latitude"] == 41.6938
    assert sr_location["longitude"] == 44.8015
    assert sr_location["timezone"] == "Asia/Tbilisi"

if __name__ == "__main__":
    try:
        test_horary_context_structure()
        # test_solar_return_context_structure()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
