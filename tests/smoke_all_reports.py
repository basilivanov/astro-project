import requests
import time
import sys
import os
import json

# ############################################################################
# AI_HEADER: TEST_SMOKE_ALL_REPORTS
# ROLE: Live smoke test for all report types using budget models.
# VERIFIES: Each report type can be generated successfully.
# ############################################################################

API_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_AUTH = os.getenv("X_TELEGRAM_AUTH", "999")
HEADERS = {"X-Telegram-Auth": TEST_AUTH}

REPORT_TYPES = [
    "natal_master",
    "year_forecast",
    "month_forecast",
    "week_forecast",
    "horary_answer",
    "synastry",
    "solar_return"
]

def verify_report(report_type):
    print(f"\n[SMOKE] Testing {report_type}...")
    question = "Will this smoke test pass?" if "horary" in report_type else None
    payload = {
        "report_type": report_type,
        "question": question,
        "llm_mode": "openrouter"
    }
    
    # For synastry we need partner data
    if report_type == "synastry":
        payload.update({
            "partner_name": "Partner",
            "partner_birth_date": "1992-02-02T12:00:00",
            "partner_birth_location": "Berlin",
            "partner_birth_lat": 52.52,
            "partner_birth_lon": 13.4,
            "partner_birth_timezone": "Europe/Berlin"
        })

    res = requests.post(f"{API_URL}/api/reports/create", headers=HEADERS, json=payload)
    if res.status_code != 200:
        print(f"  [FAIL] Creation failed: {res.status_code} {res.text}")
        return None
    
    rid = res.json()["report_id"]
    print(f"  [OK] Created ID: {rid}")
    
    # Poll
    for i in range(60):
        res = requests.get(f"{API_URL}/api/reports/{rid}", headers=HEADERS)
        data = res.json()
        status = data["report"]["status"]
        if status == "completed":
            print(f"  [OK] Completed in {i*5}s")
            return rid
        if status == "failed":
            print(f"  [FAIL] Error: {data['report'].get('error_message')}")
            return None
        time.sleep(5)
    
    print("  [FAIL] Timeout")
    return None

def run_smoke():
    # Setup profile
    profile_payload = {
        "full_name": "Smoke Tester",
        "birth_date": "1990-01-01",
        "birth_place": "Moscow",
        "birth_lat": 55.75,
        "birth_lon": 37.61,
        "current_timezone": "Europe/Moscow"
    }
    requests.put(f"{API_URL}/api/users/me", headers=HEADERS, json=profile_payload)
    
    results = {}
    for rt in REPORT_TYPES:
        rid = verify_report(rt)
        results[rt] = rid
        
    print("\n--- Smoke Test Results ---")
    all_ok = True
    for rt, rid in results.items():
        status = "✅ OK" if rid else "❌ FAIL"
        print(f"{rt:20}: {status} ({rid or '—'})")
        if not rid: all_ok = False
        
    if all_ok:
        print("\n✅ ALL REPORT TYPES SMOKE PASSED!")
    else:
        print("\n❌ SOME REPORT TYPES FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke()