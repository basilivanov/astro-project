import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.report_workflow import build_chart_data, build_report_context
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
}

def verify_all_report_types():
    report_types = [
        "natal_master",
        "week_forecast",
        "month_forecast",
        "year_forecast",
        "ten_year_forecast",
        "horary_answer",
        "synastry",
        "solar_return",
    ]
    
    results = {}
    
    for rt in report_types:
        print(f"Verifying {rt}...")
        payload = dict(BASE_PAYLOAD)
        payload["report_type"] = rt
        if rt == "horary_answer":
            payload["question"] = "Will this test pass?"
            
        req = ReportWorkflowRequest(**payload)
        chart_data = build_chart_data(req)
        context = build_report_context(req, chart_data)
        
        # Check facts
        facts = context.get("facts")
        if not facts:
            print(f"  [FAIL] No facts in context for {rt}")
            sys.exit(1)
            
        if facts.get("v") != "facts_v1":
            print(f"  [FAIL] Wrong facts version for {rt}: {facts.get('v')}")
            sys.exit(1)
            
        print(f"  [OK] Facts present (v1)")
        
        # Save a sample of facts for evidence (sanitized)
        if rt == "horary_answer":
            results["sample_horary_facts"] = facts
            
    # Write evidence log
    with open("test-results/evidence/facts_context_dump.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nEvidence saved to test-results/evidence/facts_context_dump.json")

if __name__ == "__main__":
    os.makedirs("test-results/evidence", exist_ok=True)
    verify_all_report_types()
