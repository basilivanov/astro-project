import os
from stellium_engine import StelliumEngine
from backend.app.services.report_workflow import build_chart_data, build_report_context
from unittest.mock import MagicMock

def test_stellium_engine_cosmogram():
    engine = StelliumEngine()
    # Birth date at 05:00
    dt_str = "1990-01-01T05:00:00"
    loc = "Moscow"
    
    # 1. Standard chart
    chart_normal = engine.create_natal_chart("Test", dt_str, loc, birth_time_known=True)
    # Check either local or UTC depending on how Stellium engine is configured internally
    assert 5 in [chart_normal.datetime.utc_datetime.hour, chart_normal.datetime.local_datetime.hour]
    
    # 2. Cosmogram (time unknown)
    chart_cosmo = engine.create_natal_chart("Test", dt_str, loc, birth_time_known=False)
    # StelliumEngine should set it to 12:00
    assert 12 in [chart_cosmo.datetime.utc_datetime.hour, chart_cosmo.datetime.local_datetime.hour]

def test_workflow_cosmogram_context():
    payload = MagicMock()
    payload.client_name = "Test User"
    payload.birth_date = "1990-01-01T05:00:00"
    payload.birth_location = "Moscow"
    payload.birth_lat = 55.75
    payload.birth_lon = 37.61
    payload.birth_timezone = "Europe/Moscow"
    payload.birth_place_id = "1"
    payload.report_type = "natal_master"
    payload.house_system = "placidus"
    payload.include_fixed_stars = False
    payload.birth_time_known = False
    payload.client_note = "Test Note"
    # Partner fields
    payload.partner_name = None
    payload.partner_birth_date = None
    payload.partner_birth_timezone = None
    payload.partner_birth_location = None
    payload.partner_birth_lat = None
    payload.partner_birth_lon = None
    payload.partner_birth_place_id = None
    # Solar fields
    payload.solar_current_location = None
    payload.solar_current_lat = None
    payload.solar_current_lon = None
    payload.solar_current_timezone = None
    payload.solar_current_place_id = None
    payload.solar_next_location = None
    payload.solar_next_lat = None
    payload.solar_next_lon = None
    payload.solar_next_timezone = None
    payload.solar_next_place_id = None
    
    chart_data = build_chart_data(payload)
    context = build_report_context(payload, chart_data)
    
    assert context["client"]["birth_time_known"] is False
    assert "12:00" in chart_data["datetime_utc"] or "12:00" in chart_data["datetime_local"]

if __name__ == "__main__":
    test_stellium_engine_cosmogram()
    test_workflow_cosmogram_context()
    print("Cosmogram logic tests passed!")