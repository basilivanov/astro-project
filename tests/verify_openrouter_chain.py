import requests
import time
import sys
import os
import json

# ############################################################################
# AI_HEADER: TEST_VERIFY_OPENROUTER_CHAIN
# ROLE: Real-world verification of OpenRouter model chain with budget models.
# VERIFIES: End-to-end generation for Natal and Horary using GPT-4.1-Nano.
# ############################################################################

API_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_AUTH = os.getenv("X_TELEGRAM_AUTH", "999")
HEADERS = {"X-Telegram-Auth": TEST_AUTH}

def verify_case(report_type, question=None):
    print(f"\n--- Verifying {report_type} (real OpenRouter) ---")
    payload = {
        "report_type": report_type,
        "question": question,
        "llm_mode": "openrouter"
    }
    
    start_time = time.time()
    res = requests.post(f"{API_URL}/api/reports/create", headers=HEADERS, json=payload)
    if res.status_code != 200:
        print(f"  [FAIL] Report creation failed: {res.status_code} {res.text}")
        return False
    
    report_id = res.json()["report_id"]
    print(f"  [OK] Report created. ID: {report_id}")
    
    print("  Polling for completion...")
    # GPT-4.1-Nano with concurrency=10 should be very fast.
    max_attempts = 120 # 120 * 5s = 600s = 10 mins
    
    for i in range(max_attempts):
        try:
            res = requests.get(f"{API_URL}/api/reports/{report_id}", headers=HEADERS)
            if res.status_code != 200:
                print(f"    [WARN] Failed to poll: {res.status_code}")
                time.sleep(5)
                continue
                
            data = res.json()
            status = data["report"]["status"]
            chunks = data.get("chunks", [])
            completed_chunks = len([c for c in chunks if c.get("status") == "completed"])
            total_chunks = len(chunks)
            
            print(f"    Attempt {i+1}: status={status} ({completed_chunks}/{total_chunks} sections done)")
            
            if status == "completed":
                duration = time.time() - start_time
                print(f"  [OK] {report_type} completed successfully in {duration:.1f}s!")
                
                # Verify no fallback error callouts in content
                errors_found = []
                for chunk in chunks:
                    content = chunk.get("content")
                    if content and "Ошибка генерации" in content:
                        errors_found.append(chunk["section"])
                
                if errors_found:
                    print(f"  [FAIL] Detected fallback error blocks in sections: {errors_found}")
                    return False
                    
                return True
                
            if status == "failed":
                print(f"  [FAIL] {report_type} failed: {data['report'].get('error_message')}")
                return False
        except Exception as e:
            print(f"    [ERROR] Connection error during polling: {e}")
            
        time.sleep(5)
    
    print(f"  [FAIL] {report_type} timed out.")
    return False

def test_chain():
    print(f"Starting OpenRouter Chain Verification (Auth: {TEST_AUTH})...")
    
    # Check env vars
    print("Environment configuration:")
    for key in ["OPENROUTER_MODEL", "OPENROUTER_MODEL_NATAL", "OPENROUTER_MODEL_HORARY", "OPENROUTER_FALLBACK_CHAIN", "LLM_CONCURRENCY"]:
        val = os.getenv(key, "NOT SET")
        print(f"  {key}: {val}")

    # 1. Update Profile first to ensure birth data exists
    profile_payload = {
        "full_name": "Budget Chain Tester",
        "birth_date": "1990-01-01",
        "birth_place": "Moscow",
        "birth_lat": 55.75,
        "birth_lon": 37.61,
        "current_timezone": "Europe/Moscow"
    }
    
    print("Step 1: Setting up profile...")
    res = requests.put(f"{API_URL}/api/users/me", headers=HEADERS, json=profile_payload)
    if res.status_code != 200:
         print(f"  [FAIL] Profile setup failed: {res.status_code} {res.text}")
         sys.exit(1)
    print("  [OK] Profile ready.")

    # 2. Check horary_answer
    horary_ok = verify_case("horary_answer", "Will the budget models work reliably?")
    if not horary_ok:
        print("\n❌ Horary case FAILED.")
        sys.exit(1)

    # 3. Check natal_master
    natal_ok = verify_case("natal_master")
    
    if horary_ok and natal_ok:
        print("\n✅ ALL BUDGET MODEL CHAIN CASES PASSED!")
    else:
        print("\n❌ SOME CASES FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    test_chain()
