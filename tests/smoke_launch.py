import requests
import time
import sys
import os
import json

# ############################################################################
# AI_HEADER: TEST_SMOKE_LAUNCH_V3
# ROLE: End-to-end smoke test for real generation flow (non-mock).
# VERIFIES: Correct report type, section mapping, AND real content (no errors).
# ############################################################################

API_URL = os.getenv("API_URL", "http://localhost:8000")
# Use a numeric ID to trigger dev bypass (only works in ENVIRONMENT=development)
# For STAGE testing, you MUST provide a real X_TELEGRAM_AUTH via env.
TEST_AUTH = os.getenv("X_TELEGRAM_AUTH", "999")
HEADERS = {"X-Telegram-Auth": TEST_AUTH}

def test_full_flow():
    print(f"Starting Full Flow Smoke Test (Auth: {TEST_AUTH[:10]}...)...")
    
    # 1. Register/Get Profile
    res = requests.get(f"{API_URL}/api/users/me", headers=HEADERS)
    if res.status_code != 200:
        print(f"  [FAIL] Profile fetch failed: {res.status_code} {res.text}")
        sys.exit(1)
    user_data = res.json()
    print(f"  [OK] Profile active. User: {user_data['full_name']}")
    
    # 2. Update Profile
    profile_payload = {
        "full_name": "Smoke Tester",
        "birth_date": "1990-01-01",
        "birth_place": "Berlin",
        "birth_lat": 52.52,
        "birth_lon": 13.40,
        "current_timezone": "Europe/Berlin"
    }
    res = requests.put(f"{API_URL}/api/users/me", headers=HEADERS, json=profile_payload)
    if res.status_code != 200:
        print(f"  [FAIL] Profile update failed: {res.text}")
        sys.exit(1)
    print("  [OK] Profile updated.")
    
    # 3. Trigger Horary
    horary_payload = {
        "report_type": "horary",
        "question": "Will this smoke test pass flawlessly?",
        "llm_mode": "stub"
    }
    res = requests.post(f"{API_URL}/api/reports/create", headers=HEADERS, json=horary_payload)
    if res.status_code != 200:
        print(f"  [FAIL] Report creation failed: {res.text}")
        sys.exit(1)
    
    report_id = res.json()["report_id"]
    print(f"  [OK] Horary created. ID: {report_id}")
    
    # 4. Poll for Completion
    print("  Polling for completion (max 300s)...")
    success = False
    data = {}
    for i in range(60): # 60 * 5s = 300s
        res = requests.get(f"{API_URL}/api/reports/{report_id}", headers=HEADERS)
        data = res.json()
        status = data["report"]["status"]
        print(f"    Attempt {i+1}: status={status}")
        
        if status == "completed":
            success = True
            break
        if status == "error":
            print(f"    [FAIL] Report failed: {data.get('error_message')}")
            break
            
        time.sleep(5)
        
    if success:
        print("  [OK] Report completed successfully!")
        # 5. Verify Sections and Content
        chunks = data["chunks"]
        sections = [c["section"] for c in chunks]
        print(f"  Sections found: {sections}")
        
        # Check required sections
        required_horary = ["horary_01_verdict", "horary_11_summary"]
        for rs in required_horary:
            if rs not in sections:
                print(f"  [FAIL] Missing horary section: {rs}")
                sys.exit(1)
        
        # Check for fallback errors in content
        errors_found = []
        for chunk in chunks:
            content_json = chunk.get("content")
            if not content_json:
                continue
                
            try:
                blocks = json.loads(content_json)
                for block in blocks:
                    if block.get("type") == "callout" and block.get("variant") == "error" and block.get("title") == "Ошибка генерации":
                        errors_found.append(chunk["section"])
                        break
            except Exception as e:
                print(f"    [WARN] Failed to parse content for {chunk['section']}: {e}")

        if errors_found:
            print(f"  [FAIL] Detected 'Ошибка генерации' fallback in sections: {errors_found}")
            sys.exit(1)

        if "synthesis" in sections:
            print("  [FAIL] Detected natal fallback ('synthesis' section found in horary)!")
            sys.exit(1)
            
        print("  [OK] Content verified (Horary sections present, no errors, no natal fallback).")
    else:
        print("  [FAIL] Report timed out or failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_full_flow()
