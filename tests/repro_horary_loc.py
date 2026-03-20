import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.report_workflow import build_chart_data
from backend.app.main import ReportWorkflowRequest

def test_horary_uses_current_location():
    # Moscow coordinates
    moscow = {"lat": 55.7558, "lon": 37.6173, "name": "Moscow", "tz": "Europe/Moscow"}
    # Tokyo coordinates
    tokyo = {"lat": 35.6895, "lon": 139.6917, "name": "Tokyo", "tz": "Asia/Tokyo"}
    
    payload = ReportWorkflowRequest(
        client_name="Test User",
        report_type="horary",
        birth_date="1990-01-01",
        birth_location=moscow["name"],
        birth_lat=moscow["lat"],
        birth_lon=moscow["lon"],
        birth_timezone=moscow["tz"],
        solar_current_location=tokyo["name"],
        solar_current_lat=tokyo["lat"],
        solar_current_lon=tokyo["lon"],
        solar_current_timezone=tokyo["tz"]
    )
    
    chart_data = build_chart_data(payload)
    
    loc = chart_data.get("location", {})
    print(f"Chart Location: {loc.get('name')} ({loc.get('latitude')}, {loc.get('longitude')})")
    
    # Assert that Tokyo coordinates are used
    assert abs(loc.get("latitude", 0) - tokyo["lat"]) < 0.01
    assert abs(loc.get("longitude", 0) - tokyo["lon"]) < 0.01
    assert loc.get("name") == tokyo["name"]
    
    print("✅ Success: Horary used current location instead of birth location.")

if __name__ == "__main__":
    test_horary_uses_current_location()
